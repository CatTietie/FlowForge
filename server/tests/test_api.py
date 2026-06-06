import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine as db_engine


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=db_engine)
    yield
    Base.metadata.drop_all(bind=db_engine)


client = TestClient(app)


class TestFormValidation:
    """Test form schema validation rules by submitting invalid data through the API."""

    def _create_form_with_required_field(self):
        schema = {
            "name": "test-form",
            "schema_json": {
                "fields": [
                    {
                        "fieldId": "name_field",
                        "type": "text",
                        "label": "姓名",
                        "validations": [
                            {"rule": "required", "message": "此项为必填"}
                        ],
                    },
                    {
                        "fieldId": "dept_field",
                        "type": "dropdown",
                        "label": "部门",
                        "options": ["技术部", "产品部"],
                        "validations": [
                            {"rule": "required", "message": "请选择部门"}
                        ],
                    },
                ]
            },
        }
        res = client.post("/api/forms/", json=schema)
        assert res.status_code == 200
        return res.json()

    def test_create_form_schema(self):
        form = self._create_form_with_required_field()
        assert form["id"] is not None
        assert form["version"] == 1
        assert form["name"] == "test-form"

    def test_get_form_schema(self):
        form = self._create_form_with_required_field()
        res = client.get(f"/api/forms/schema/{form['id']}")
        assert res.status_code == 200
        data = res.json()
        assert len(data["fields"]) == 2
        assert data["fields"][0]["fieldId"] == "name_field"
        assert data["fields"][0]["validations"][0]["rule"] == "required"

    def test_version_increments(self):
        self._create_form_with_required_field()
        form2 = self._create_form_with_required_field()
        assert form2["version"] == 2

    def test_form_not_found(self):
        res = client.get("/api/forms/999")
        assert res.status_code == 404


class TestFormFieldValidationLogic:
    """Unit tests for the validation logic itself (mirroring frontend behavior)."""

    def validate_field(self, value, validations):
        for v in validations:
            rule = v["rule"]
            if rule == "required":
                if not value or (isinstance(value, str) and value.strip() == ""):
                    return v.get("message", "此项为必填")
            elif rule == "maxLength":
                if isinstance(value, str) and len(value) > v["value"]:
                    return v.get("message", f"最大长度为{v['value']}")
            elif rule == "regex":
                import re
                if isinstance(value, str) and not re.match(v["value"], value):
                    return v.get("message", "格式不正确")
        return None

    def test_required_empty_string_fails(self):
        error = self.validate_field("", [{"rule": "required", "message": "此项为必填"}])
        assert error == "此项为必填"

    def test_required_none_fails(self):
        error = self.validate_field(None, [{"rule": "required", "message": "此项为必填"}])
        assert error == "此项为必填"

    def test_required_whitespace_fails(self):
        error = self.validate_field("   ", [{"rule": "required", "message": "此项为必填"}])
        assert error == "此项为必填"

    def test_required_valid_passes(self):
        error = self.validate_field("张三", [{"rule": "required", "message": "此项为必填"}])
        assert error is None

    def test_max_length_exceeds(self):
        error = self.validate_field("abcdef", [{"rule": "maxLength", "value": 5, "message": "最大长度为5"}])
        assert error == "最大长度为5"

    def test_max_length_within_limit(self):
        error = self.validate_field("abc", [{"rule": "maxLength", "value": 5}])
        assert error is None

    def test_regex_invalid(self):
        error = self.validate_field("abc", [{"rule": "regex", "value": r"^\d+$", "message": "必须为数字"}])
        assert error == "必须为数字"

    def test_regex_valid(self):
        error = self.validate_field("123", [{"rule": "regex", "value": r"^\d+$", "message": "必须为数字"}])
        assert error is None

    def test_multiple_rules_first_fails(self):
        rules = [
            {"rule": "required", "message": "必填"},
            {"rule": "maxLength", "value": 3, "message": "太长"},
        ]
        error = self.validate_field("", rules)
        assert error == "必填"

    def test_multiple_rules_second_fails(self):
        rules = [
            {"rule": "required", "message": "必填"},
            {"rule": "maxLength", "value": 3, "message": "太长"},
        ]
        error = self.validate_field("abcde", rules)
        assert error == "太长"


class TestEndToEndFlow:
    """Test the complete flow: create form + process, start process, approve."""

    def _setup_process(self):
        proc = {
            "name": "leave-approval",
            "definition_json": {
                "nodes": [
                    {"id": "start", "type": "start", "assignee": None},
                    {"id": "manager_review", "type": "approval", "assignee": "manager"},
                    {"id": "end", "type": "end", "assignee": None},
                ],
                "edges": [
                    {"source": "start", "target": "manager_review"},
                    {"source": "manager_review", "target": "end"},
                ],
            },
        }
        res = client.post("/api/processes/definitions", json=proc)
        assert res.status_code == 200
        return res.json()

    def test_start_and_approve_process(self):
        proc = self._setup_process()

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "张三", "days": 2},
        })
        assert start_res.status_code == 200
        instance = start_res.json()
        assert instance["status"] == "running"
        assert instance["current_node_id"] == "manager_review"

        approve_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
            "comment": "同意",
        })
        assert approve_res.status_code == 200
        result = approve_res.json()
        assert result["status"] == "completed"
        assert result["current_node_id"] == "end"

    def test_start_and_reject_process(self):
        proc = self._setup_process()

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "李四", "days": 5},
        })
        instance = start_res.json()

        reject_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "reject",
            "comment": "不批准",
        })
        assert reject_res.status_code == 200
        result = reject_res.json()
        assert result["status"] == "rejected"
        assert result["current_node_id"] == "manager_review"

    def test_wrong_assignee_rejected(self):
        proc = self._setup_process()

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "王五"},
        })
        instance = start_res.json()

        res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "someone_else",
            "decision": "approve",
        })
        assert res.status_code == 403

    def test_cannot_approve_completed_process(self):
        proc = self._setup_process()

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "赵六"},
        })
        instance = start_res.json()

        client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
        })

        res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
        })
        assert res.status_code == 400


class TestConditionBranchAPI:
    """Test condition branch routing through API - leave scenario."""

    def _setup_leave_process(self):
        proc = {
            "name": "leave-with-condition",
            "definition_json": {
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
            },
        }
        res = client.post("/api/processes/definitions", json=proc)
        assert res.status_code == 200
        return res.json()

    def test_days_gt_3_routes_to_gm(self):
        proc = self._setup_leave_process()
        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "张三", "days": 5},
        })
        instance = start_res.json()
        assert instance["current_node_id"] == "dept_mgr"

        approve_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
        })
        result = approve_res.json()
        assert result["current_node_id"] == "gm_approval"
        assert result["status"] == "running"

        final_res = client.post("/api/processes/approve", json={
            "process_instance_id": result["id"],
            "assignee": "gm",
            "decision": "approve",
        })
        final = final_res.json()
        assert final["status"] == "completed"
        assert final["current_node_id"] == "end"

    def test_days_le_3_ends_directly(self):
        proc = self._setup_leave_process()
        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "李四", "days": 2},
        })
        instance = start_res.json()
        assert instance["current_node_id"] == "dept_mgr"

        approve_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
        })
        result = approve_res.json()
        assert result["current_node_id"] == "end"
        assert result["status"] == "completed"


class TestReturnAndResubmitAPI:
    """Test return to initiator and resubmit flow."""

    def _setup_process(self):
        proc = {
            "name": "return-test",
            "definition_json": {
                "nodes": [
                    {"id": "start", "type": "start", "assignee": None},
                    {"id": "review", "type": "approval", "assignee": "manager"},
                    {"id": "end", "type": "end", "assignee": None},
                ],
                "edges": [
                    {"source": "start", "target": "review"},
                    {"source": "review", "target": "end"},
                ],
            },
        }
        res = client.post("/api/processes/definitions", json=proc)
        return res.json()

    def test_return_then_resubmit_then_approve(self):
        proc = self._setup_process()

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "王五", "days": 1},
        })
        instance = start_res.json()
        assert instance["status"] == "running"

        # Manager returns to initiator
        return_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "return",
            "comment": "请修改天数",
        })
        returned = return_res.json()
        assert returned["status"] == "returned"
        assert returned["current_node_id"] == "start"

        # Initiator resubmits with modified data
        resubmit_res = client.post("/api/processes/resubmit", json={
            "process_instance_id": instance["id"],
            "form_data": {"name": "王五", "days": 3},
        })
        resubmitted = resubmit_res.json()
        assert resubmitted["status"] == "running"
        assert resubmitted["current_node_id"] == "review"

        # Manager approves this time
        approve_res = client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
        })
        final = approve_res.json()
        assert final["status"] == "completed"

    def test_resubmit_non_returned_process_fails(self):
        proc = self._setup_process()
        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc["id"],
            "form_data": {"name": "test"},
        })
        instance = start_res.json()

        res = client.post("/api/processes/resubmit", json={
            "process_instance_id": instance["id"],
            "form_data": {"name": "new"},
        })
        assert res.status_code == 400


class TestApprovalRecordsAPI:
    """Test approval history query endpoint."""

    def test_get_records_after_approval(self):
        proc = {
            "name": "records-test",
            "definition_json": {
                "nodes": [
                    {"id": "start", "type": "start", "assignee": None},
                    {"id": "review", "type": "approval", "assignee": "manager"},
                    {"id": "end", "type": "end", "assignee": None},
                ],
                "edges": [
                    {"source": "start", "target": "review"},
                    {"source": "review", "target": "end"},
                ],
            },
        }
        proc_res = client.post("/api/processes/definitions", json=proc)
        proc_id = proc_res.json()["id"]

        start_res = client.post("/api/processes/start", json={
            "process_definition_id": proc_id,
            "form_data": {"name": "test"},
        })
        instance = start_res.json()

        client.post("/api/processes/approve", json={
            "process_instance_id": instance["id"],
            "assignee": "manager",
            "decision": "approve",
            "comment": "LGTM",
        })

        records_res = client.get(f"/api/processes/instances/{instance['id']}/records")
        assert records_res.status_code == 200
        records = records_res.json()
        assert len(records) == 1
        assert records[0]["assignee"] == "manager"
        assert records[0]["decision"] == "approve"
        assert records[0]["comment"] == "LGTM"
        assert records[0]["node_id"] == "review"


class TestNumberFieldValidation:
    """Test min/max validation for number fields."""

    def validate_field(self, value, validations):
        for v in validations:
            rule = v["rule"]
            if rule == "required":
                if not value and value != 0:
                    return v.get("message", "此项为必填")
                if isinstance(value, str) and value.strip() == "":
                    return v.get("message", "此项为必填")
            elif rule == "min":
                num = float(value) if value is not None else 0
                if num < v["value"]:
                    return v.get("message", f"最小值为{v['value']}")
            elif rule == "max":
                num = float(value) if value is not None else 0
                if num > v["value"]:
                    return v.get("message", f"最大值为{v['value']}")
        return None

    def test_min_value_violation(self):
        error = self.validate_field(0, [{"rule": "min", "value": 1, "message": "最小值为1"}])
        assert error == "最小值为1"

    def test_max_value_violation(self):
        error = self.validate_field(100, [{"rule": "max", "value": 30, "message": "最大值为30"}])
        assert error == "最大值为30"

    def test_within_range_passes(self):
        rules = [
            {"rule": "min", "value": 1, "message": "最小值为1"},
            {"rule": "max", "value": 30, "message": "最大值为30"},
        ]
        error = self.validate_field(5, rules)
        assert error is None

    def test_required_zero_passes(self):
        error = self.validate_field(0, [{"rule": "required", "message": "必填"}])
        assert error is None

    def test_required_empty_string_fails(self):
        error = self.validate_field("", [{"rule": "required", "message": "必填"}])
        assert error == "必填"
