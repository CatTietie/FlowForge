import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from engine.process_engine import ProcessEngine, ProcessEngineError


SIMPLE_PROCESS = {
    "nodes": [
        {"id": "start", "type": "start", "assignee": None},
        {"id": "approval1", "type": "approval", "assignee": "manager"},
        {"id": "end", "type": "end", "assignee": None},
    ],
    "edges": [
        {"source": "start", "target": "approval1"},
        {"source": "approval1", "target": "end"},
    ],
}


class TestProcessEngine:
    def test_get_start_node(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        assert engine.get_start_node_id() == "start"

    def test_advance_from_start_to_approval(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        next_node, status = engine.advance("start")
        assert next_node == "approval1"
        assert status == "running"

    def test_approve_advances_to_end(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        next_node, status = engine.advance("approval1", decision="approve")
        assert next_node == "end"
        assert status == "completed"

    def test_reject_stays_at_node_with_rejected_status(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        next_node, status = engine.advance("approval1", decision="reject")
        assert next_node == "approval1"
        assert status == "rejected"

    def test_approval_without_decision_raises(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        with pytest.raises(ProcessEngineError, match="requires a decision"):
            engine.advance("approval1", decision=None)

    def test_invalid_decision_raises(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        with pytest.raises(ProcessEngineError, match="Invalid decision"):
            engine.advance("approval1", decision="maybe")

    def test_cannot_advance_past_end(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        with pytest.raises(ProcessEngineError, match="Cannot advance past end"):
            engine.advance("end")

    def test_invalid_node_raises(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        with pytest.raises(ProcessEngineError, match="not found"):
            engine.advance("nonexistent")

    def test_get_assignee(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        assert engine.get_current_assignee("approval1") == "manager"
        assert engine.get_current_assignee("start") is None

    def test_multi_step_process(self):
        definition = {
            "nodes": [
                {"id": "start", "type": "start", "assignee": None},
                {"id": "review", "type": "approval", "assignee": "reviewer"},
                {"id": "final", "type": "approval", "assignee": "director"},
                {"id": "end", "type": "end", "assignee": None},
            ],
            "edges": [
                {"source": "start", "target": "review"},
                {"source": "review", "target": "final"},
                {"source": "final", "target": "end"},
            ],
        }
        engine = ProcessEngine(definition)
        node, status = engine.advance("start")
        assert node == "review"
        assert status == "running"

        node, status = engine.advance("review", decision="approve")
        assert node == "final"
        assert status == "running"

        node, status = engine.advance("final", decision="approve")
        assert node == "end"
        assert status == "completed"

    def test_missing_start_node_raises(self):
        bad_def = {
            "nodes": [{"id": "end", "type": "end", "assignee": None}],
            "edges": [],
        }
        with pytest.raises(ProcessEngineError, match="exactly one start"):
            ProcessEngine(bad_def)

    def test_missing_end_node_raises(self):
        bad_def = {
            "nodes": [{"id": "start", "type": "start", "assignee": None}],
            "edges": [],
        }
        with pytest.raises(ProcessEngineError, match="at least one end"):
            ProcessEngine(bad_def)


class TestConditionBranch:
    """Condition node selects edge based on form data expression."""

    LEAVE_PROCESS = {
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

    def test_condition_routes_to_gm_when_days_gt_3(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        node, status = engine.advance("check_days", form_data={"days": 5})
        assert node == "gm_approval"
        assert status == "running"

    def test_condition_routes_to_end_when_days_le_3(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        node, status = engine.advance("check_days", form_data={"days": 2})
        assert node == "end"
        assert status == "completed"

    def test_condition_with_equal_boundary(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        node, status = engine.advance("check_days", form_data={"days": 3})
        assert node == "end"
        assert status == "completed"

    def test_full_flow_days_gt_3(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        form_data = {"days": 5}

        node, status = engine.advance("start", form_data=form_data)
        assert node == "dept_mgr"

        node, status = engine.advance("dept_mgr", decision="approve", form_data=form_data)
        assert node == "gm_approval"
        assert status == "running"

        node, status = engine.advance("gm_approval", decision="approve", form_data=form_data)
        assert node == "end"
        assert status == "completed"

    def test_full_flow_days_le_3(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        form_data = {"days": 1}

        node, status = engine.advance("start", form_data=form_data)
        assert node == "dept_mgr"

        node, status = engine.advance("dept_mgr", decision="approve", form_data=form_data)
        assert node == "end"
        assert status == "completed"

    def test_condition_without_form_data_raises(self):
        engine = ProcessEngine(self.LEAVE_PROCESS)
        with pytest.raises(ProcessEngineError, match="requires form_data"):
            engine.advance("check_days", form_data=None)

    def test_condition_string_comparison(self):
        definition = {
            "nodes": [
                {"id": "start", "type": "start", "assignee": None},
                {"id": "branch", "type": "condition", "assignee": None},
                {"id": "a", "type": "approval", "assignee": "admin"},
                {"id": "end", "type": "end", "assignee": None},
            ],
            "edges": [
                {"source": "start", "target": "branch"},
                {"source": "branch", "target": "a", "condition": "dept == tech"},
                {"source": "branch", "target": "end"},
                {"source": "a", "target": "end"},
            ],
        }
        engine = ProcessEngine(definition)
        node, _ = engine.advance("branch", form_data={"dept": "tech"})
        assert node == "a"
        node, status = engine.advance("branch", form_data={"dept": "sales"})
        assert node == "end"
        assert status == "completed"


class TestReturnToInitiator:
    def test_return_decision_goes_to_start(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        node, status = engine.advance("approval1", decision="return")
        assert node == "start"
        assert status == "returned"

    def test_after_return_can_advance_again(self):
        engine = ProcessEngine(SIMPLE_PROCESS)
        node, status = engine.advance("approval1", decision="return")
        assert status == "returned"
        # Simulating resubmit: advance from start again
        node, status = engine.advance("start")
        assert node == "approval1"
        assert status == "running"
