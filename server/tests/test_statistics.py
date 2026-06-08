import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from database import Base, engine as db_engine, SessionLocal
from models.models import NodeTransitionLog, ProcessInstance, ProcessDefinition, SlaAlert
from services.sla_checker import _check_sla_violations


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=db_engine)
    yield
    Base.metadata.drop_all(bind=db_engine)


client = TestClient(app)

SIMPLE_DEFINITION = {
    "nodes": [
        {"id": "start", "type": "start"},
        {"id": "approval1", "type": "approval", "assignee": "manager", "sla_hours": 2.0},
        {"id": "end", "type": "end"},
    ],
    "edges": [
        {"source": "start", "target": "approval1"},
        {"source": "approval1", "target": "end"},
    ],
}

CONDITION_DEFINITION = {
    "nodes": [
        {"id": "start", "type": "start"},
        {"id": "check", "type": "condition"},
        {"id": "approval1", "type": "approval", "assignee": "manager", "sla_hours": 4.0},
        {"id": "end", "type": "end"},
    ],
    "edges": [
        {"source": "start", "target": "check"},
        {"source": "check", "target": "approval1", "condition": "amount > 100"},
        {"source": "check", "target": "end"},
    ],
}


def _create_process_def(definition=None):
    res = client.post("/api/processes/definitions", json={
        "name": "test-process",
        "definition_json": definition or SIMPLE_DEFINITION,
    })
    assert res.status_code == 200
    return res.json()


def _start_process(proc_def_id, form_data=None):
    res = client.post("/api/processes/start", json={
        "process_definition_id": proc_def_id,
        "form_data": form_data or {"name": "test"},
    })
    assert res.status_code == 200
    return res.json()


def _approve(instance_id, assignee="manager", decision="approve"):
    res = client.post("/api/processes/approve", json={
        "process_instance_id": instance_id,
        "assignee": assignee,
        "decision": decision,
    })
    return res


class TestStatisticsAvgDuration:
    def test_empty_data_returns_zero(self):
        resp = client.get("/api/statistics/avg-duration")
        assert resp.status_code == 200
        data = resp.json()
        assert data["overall_avg_seconds"] == 0.0
        assert data["by_node"] == []

    def test_avg_duration_after_approval(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])
        _approve(instance["id"])

        resp = client.get("/api/statistics/avg-duration")
        data = resp.json()
        assert data["overall_avg_seconds"] >= 0
        assert len(data["by_node"]) == 1
        assert data["by_node"][0]["node_id"] == "approval1"
        assert data["by_node"][0]["count"] == 1

    def test_filter_by_assignee(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])
        _approve(instance["id"])

        resp = client.get("/api/statistics/avg-duration?assignee=manager")
        data = resp.json()
        assert data["by_node"][0]["count"] == 1

        resp = client.get("/api/statistics/avg-duration?assignee=nobody")
        data = resp.json()
        assert data["overall_avg_seconds"] == 0.0
        assert data["by_node"] == []


class TestStatisticsTimeoutRate:
    def test_empty_data(self):
        resp = client.get("/api/statistics/timeout-rate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_completed"] == 0
        assert data["total_exceeded"] == 0
        assert data["rate_percent"] == 0.0

    def test_no_timeout_when_fast(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])
        _approve(instance["id"])

        resp = client.get("/api/statistics/timeout-rate")
        data = resp.json()
        assert data["total_completed"] == 1
        assert data["total_exceeded"] == 0
        assert data["rate_percent"] == 0.0

    def test_timeout_detected(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])

        db = SessionLocal()
        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
        ).first()
        log.enter_time = datetime.utcnow() - timedelta(hours=5)
        db.commit()
        db.close()

        _approve(instance["id"])

        resp = client.get("/api/statistics/timeout-rate")
        data = resp.json()
        assert data["total_completed"] == 1
        assert data["total_exceeded"] == 1
        assert data["rate_percent"] == 100.0


class TestStatisticsCompletionTrend:
    def test_empty_data(self):
        resp = client.get("/api/statistics/completion-trend?granularity=day")
        assert resp.status_code == 200
        data = resp.json()
        assert data["granularity"] == "day"
        assert data["data_points"] == []

    def test_trend_after_completions(self):
        proc = _create_process_def()
        inst1 = _start_process(proc["id"])
        _approve(inst1["id"])
        inst2 = _start_process(proc["id"])
        _approve(inst2["id"], decision="reject")

        resp = client.get("/api/statistics/completion-trend?granularity=day")
        data = resp.json()
        assert len(data["data_points"]) >= 1
        point = data["data_points"][0]
        assert point["completed"] + point["rejected"] + point["returned"] == point["total"]

    def test_granularity_month(self):
        proc = _create_process_def()
        inst = _start_process(proc["id"])
        _approve(inst["id"])

        resp = client.get("/api/statistics/completion-trend?granularity=month")
        data = resp.json()
        assert data["granularity"] == "month"
        assert len(data["data_points"]) >= 1
        assert len(data["data_points"][0]["period"]) == 7  # "YYYY-MM"


class TestStatisticsBacklog:
    def test_empty_backlog(self):
        resp = client.get("/api/statistics/backlog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_pending"] == 0
        assert data["by_node"] == []

    def test_backlog_with_pending_instance(self):
        proc = _create_process_def()
        _start_process(proc["id"])

        resp = client.get("/api/statistics/backlog")
        data = resp.json()
        assert data["total_pending"] == 1
        assert len(data["by_node"]) == 1
        assert data["by_node"][0]["node_id"] == "approval1"

    def test_sla_at_risk(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])

        db = SessionLocal()
        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
            NodeTransitionLog.leave_time.is_(None),
        ).first()
        log.enter_time = datetime.utcnow() - timedelta(hours=3)
        db.commit()
        db.close()

        resp = client.get("/api/statistics/backlog")
        data = resp.json()
        assert len(data["sla_at_risk"]) == 1
        assert data["sla_at_risk"][0]["node_id"] == "approval1"
        assert data["sla_at_risk"][0]["elapsed_hours"] > 2.0


class TestConditionNodeTransitionLogs:
    def test_condition_node_logged(self):
        proc = _create_process_def(CONDITION_DEFINITION)
        instance = _start_process(proc["id"], form_data={"amount": 200})

        db = SessionLocal()
        logs = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
        ).order_by(NodeTransitionLog.id).all()
        db.close()

        node_ids = [log.node_id for log in logs]
        assert "check" in node_ids
        condition_log = next(l for l in logs if l.node_id == "check")
        assert condition_log.node_type == "condition"
        assert condition_log.duration_seconds == 0
        assert condition_log.leave_time is not None


class TestSlaChecker:
    def test_new_violation_creates_alert(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])

        db = SessionLocal()
        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
            NodeTransitionLog.leave_time.is_(None),
        ).first()
        log.enter_time = datetime.utcnow() - timedelta(hours=5)
        db.commit()
        db.close()

        _check_sla_violations()

        db = SessionLocal()
        alert = db.query(SlaAlert).filter(
            SlaAlert.process_instance_id == instance["id"],
        ).first()
        assert alert is not None
        assert alert.node_id == "approval1"
        assert alert.sla_hours == 2.0
        assert alert.notified == 1

        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
        ).first()
        assert log.sla_exceeded == 1
        db.close()

    def test_deduplication_no_double_alert(self):
        proc = _create_process_def()
        instance = _start_process(proc["id"])

        db = SessionLocal()
        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
            NodeTransitionLog.leave_time.is_(None),
        ).first()
        log.enter_time = datetime.utcnow() - timedelta(hours=5)
        db.commit()
        db.close()

        _check_sla_violations()
        _check_sla_violations()

        db = SessionLocal()
        alerts = db.query(SlaAlert).filter(
            SlaAlert.process_instance_id == instance["id"],
        ).all()
        assert len(alerts) == 1
        db.close()

    def test_no_alert_when_within_sla(self):
        proc = _create_process_def()
        _start_process(proc["id"])

        _check_sla_violations()

        db = SessionLocal()
        alerts = db.query(SlaAlert).all()
        assert len(alerts) == 0
        db.close()

    @patch("services.sla_checker._send_webhook")
    def test_webhook_failure_marks_alert_and_retries(self, mock_webhook):
        mock_webhook.return_value = False

        proc = _create_process_def()
        instance = _start_process(proc["id"])

        db = SessionLocal()
        log = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.process_instance_id == instance["id"],
            NodeTransitionLog.node_id == "approval1",
            NodeTransitionLog.leave_time.is_(None),
        ).first()
        log.enter_time = datetime.utcnow() - timedelta(hours=5)
        db.commit()
        db.close()

        with patch.dict(os.environ, {"SLA_WEBHOOK_URL": "http://example.com/hook"}):
            _check_sla_violations()

        db = SessionLocal()
        alert = db.query(SlaAlert).filter(
            SlaAlert.process_instance_id == instance["id"],
        ).first()
        assert alert.notified == 2  # failed
        db.close()

        mock_webhook.return_value = True
        with patch.dict(os.environ, {"SLA_WEBHOOK_URL": "http://example.com/hook"}):
            _check_sla_violations()

        db = SessionLocal()
        alert = db.query(SlaAlert).filter(
            SlaAlert.process_instance_id == instance["id"],
        ).first()
        assert alert.notified == 1  # now sent
        db.close()
