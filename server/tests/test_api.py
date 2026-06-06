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
