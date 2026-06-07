import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


SIMPLE_PROCESS = {
    "nodes": [
        {"id": "start", "type": "start", "assignee": None},
        {"id": "mgr", "type": "approval", "assignee": "manager"},
        {"id": "end", "type": "end", "assignee": None},
    ],
    "edges": [
        {"source": "start", "target": "mgr"},
        {"source": "mgr", "target": "end"},
    ],
}

CONDITION_PROCESS = {
    "nodes": [
        {"id": "start", "type": "start", "assignee": None},
        {"id": "dept_mgr", "type": "approval", "assignee": "manager"},
        {"id": "check_days", "type": "condition", "assignee": None},
        {"id": "gm_approval", "type": "approval", "assignee": "gm"},
        {"id": "end", "type": "end", "assignee": None},
    ],
    "edges": [
        {"source": "start", "target": "dept_mgr"},
        {"source": "dept_mgr", "target": "check_days"},
        {"source": "check_days", "target": "gm_approval", "condition": "days > 3"},
        {"source": "check_days", "target": "end"},
        {"source": "gm_approval", "target": "end"},
    ],
}


class TestSimulationAutoApprove:
    def test_simple_auto_approve(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "start" in data["visited_node_ids"]
        assert "mgr" in data["visited_node_ids"]
        assert "end" in data["visited_node_ids"]
        assert data["coverage_percent"] == 100.0

    def test_condition_auto_approve_days_gt_3(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 5},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "gm_approval" in data["visited_node_ids"]
        assert "end" in data["visited_node_ids"]
        assert data["coverage_percent"] == 100.0

    def test_condition_auto_approve_days_le_3(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 2},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "gm_approval" not in data["visited_node_ids"]
        assert "gm_approval" in data["unvisited_node_ids"]


class TestSimulationStepMode:
    def test_no_decisions_waits_at_first_approval(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "decisions": [],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "waiting_for_decision"
        waiting_step = data["steps"][-1]
        assert waiting_step["node_id"] == "mgr"
        assert waiting_step["status"] == "waiting_for_decision"

    def test_one_decision_completes(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "decisions": [{"node_id": "mgr", "decision": "approve"}],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"

    def test_condition_step_mode(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 5},
            "decisions": [
                {"node_id": "dept_mgr", "decision": "approve"},
                {"node_id": "gm_approval", "decision": "approve"},
            ],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "gm_approval" in data["visited_node_ids"]


class TestSimulationConditionDetails:
    def test_condition_evaluations_present(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 5},
            "auto_approve": True,
        })
        data = resp.json()
        condition_steps = [s for s in data["steps"]
                          if s["node_type"] == "condition" and s["condition_evaluations"]]
        assert len(condition_steps) >= 1
        evals = condition_steps[0]["condition_evaluations"]
        assert len(evals) >= 1
        assert evals[0]["field_name"] == "days"
        assert evals[0]["operator"] == ">"
        assert evals[0]["result"] is True

    def test_condition_evaluations_false(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 2},
            "auto_approve": True,
        })
        data = resp.json()
        condition_steps = [s for s in data["steps"]
                          if s["node_type"] == "condition" and s["condition_evaluations"]]
        assert len(condition_steps) >= 1
        evals = condition_steps[0]["condition_evaluations"]
        assert evals[0]["result"] is False


class TestSimulationRejectReturn:
    def test_reject_halts_simulation(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "decisions": [{"node_id": "mgr", "decision": "reject"}],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "rejected"

    def test_return_resets_to_start(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "decisions": [{"node_id": "mgr", "decision": "return"}],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "returned"


class TestSimulationCoverage:
    def test_partial_coverage(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": CONDITION_PROCESS,
            "form_data": {"days": 2},
            "auto_approve": True,
        })
        data = resp.json()
        assert data["coverage_percent"] < 100.0
        assert "gm_approval" in data["unvisited_node_ids"]

    def test_full_coverage_simple(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": SIMPLE_PROCESS,
            "form_data": {},
            "auto_approve": True,
        })
        data = resp.json()
        assert data["coverage_percent"] == 100.0
        assert data["unvisited_node_ids"] == []


class TestSimulationErrors:
    def test_invalid_definition(self):
        resp = client.post("/api/processes/simulate", json={
            "definition": {
                "nodes": [{"id": "start", "type": "start", "assignee": None}],
                "edges": [],
            },
            "form_data": {},
            "auto_approve": True,
        })
        assert resp.status_code == 400

    def test_malformed_condition_expression(self):
        """A condition expression with invalid format should return 400, not crash."""
        bad_condition_process = {
            "nodes": [
                {"id": "start", "type": "start", "assignee": None},
                {"id": "check", "type": "condition", "assignee": None},
                {"id": "end", "type": "end", "assignee": None},
            ],
            "edges": [
                {"source": "start", "target": "check"},
                {"source": "check", "target": "end", "condition": "this is not valid!!!"},
            ],
        }
        resp = client.post("/api/processes/simulate", json={
            "definition": bad_condition_process,
            "form_data": {"x": 1},
            "auto_approve": True,
        })
        assert resp.status_code == 400
        assert "detail" in resp.json()


# Complex process with multiple approvals and condition branches
COMPLEX_PROCESS = {
    "nodes": [
        {"id": "start", "type": "start", "assignee": None},
        {"id": "team_lead", "type": "approval", "assignee": "lead"},
        {"id": "check_amount", "type": "condition", "assignee": None},
        {"id": "finance_mgr", "type": "approval", "assignee": "finance"},
        {"id": "check_dept", "type": "condition", "assignee": None},
        {"id": "ceo", "type": "approval", "assignee": "ceo"},
        {"id": "end", "type": "end", "assignee": None},
    ],
    "edges": [
        {"source": "start", "target": "team_lead"},
        {"source": "team_lead", "target": "check_amount"},
        {"source": "check_amount", "target": "finance_mgr", "condition": "amount > 1000"},
        {"source": "check_amount", "target": "end"},
        {"source": "finance_mgr", "target": "check_dept"},
        {"source": "check_dept", "target": "ceo", "condition": "dept == tech"},
        {"source": "check_dept", "target": "end"},
        {"source": "ceo", "target": "end"},
    ],
}


class TestComplexProcessSimulation:
    """Validates the refactored simulator with a multi-approval, multi-condition process."""

    def test_auto_approve_high_amount_tech(self):
        """amount>1000 + dept==tech => full path through all approvals."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "team_lead" in data["visited_node_ids"]
        assert "finance_mgr" in data["visited_node_ids"]
        assert "ceo" in data["visited_node_ids"]
        assert "check_amount" in data["visited_node_ids"]
        assert "check_dept" in data["visited_node_ids"]
        assert data["coverage_percent"] == 100.0

    def test_auto_approve_high_amount_non_tech(self):
        """amount>1000 + dept!=tech => skips CEO, goes directly to end after finance."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "hr"},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "finance_mgr" in data["visited_node_ids"]
        assert "ceo" not in data["visited_node_ids"]
        assert "ceo" in data["unvisited_node_ids"]

    def test_auto_approve_low_amount(self):
        """amount<=1000 => skips finance and everything after."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 500, "dept": "tech"},
            "auto_approve": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert "finance_mgr" not in data["visited_node_ids"]
        assert "ceo" not in data["visited_node_ids"]
        assert "check_dept" not in data["visited_node_ids"]

    def test_step_mode_pauses_at_each_approval(self):
        """Step mode: no decisions => pauses at first approval."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "decisions": [],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "waiting_for_decision"
        assert data["steps"][-1]["node_id"] == "team_lead"

    def test_step_mode_pauses_at_second_approval(self):
        """Step mode with one decision => advances past condition, pauses at finance_mgr."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "decisions": [{"node_id": "team_lead", "decision": "approve"}],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "waiting_for_decision"
        assert data["steps"][-1]["node_id"] == "finance_mgr"

    def test_step_mode_full_path(self):
        """Step mode with all decisions => same result as auto-approve."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "decisions": [
                {"node_id": "team_lead", "decision": "approve"},
                {"node_id": "finance_mgr", "decision": "approve"},
                {"node_id": "ceo", "decision": "approve"},
            ],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "completed"
        assert data["coverage_percent"] == 100.0

    def test_step_mode_reject_midway(self):
        """Rejecting at finance_mgr halts the simulation there."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "decisions": [
                {"node_id": "team_lead", "decision": "approve"},
                {"node_id": "finance_mgr", "decision": "reject"},
            ],
            "auto_approve": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_status"] == "rejected"
        assert "ceo" not in data["visited_node_ids"]

    def test_condition_details_recorded_for_both_conditions(self):
        """Both condition nodes should have evaluation details in the steps."""
        resp = client.post("/api/processes/simulate", json={
            "definition": COMPLEX_PROCESS,
            "form_data": {"amount": 5000, "dept": "tech"},
            "auto_approve": True,
        })
        data = resp.json()
        condition_steps = [s for s in data["steps"]
                          if s["node_type"] == "condition" and s["condition_evaluations"]]
        assert len(condition_steps) == 2

        amount_step = next(s for s in condition_steps if
                          any(e["field_name"] == "amount" for e in s["condition_evaluations"]))
        assert amount_step["condition_evaluations"][0]["result"] is True

        dept_step = next(s for s in condition_steps if
                        any(e["field_name"] == "dept" for e in s["condition_evaluations"]))
        assert dept_step["condition_evaluations"][0]["result"] is True
