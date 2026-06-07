from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import warnings

warnings.filterwarnings("ignore", message=".*shadows an attribute.*")


class FieldValidation(BaseModel):
    rule: str  # "required", "maxLength", "regex", "range"
    value: Optional[str | int | float | bool] = None
    message: Optional[str] = None


class FieldDefinition(BaseModel):
    fieldId: str
    type: str  # "text", "dropdown", "date"
    label: str
    placeholder: Optional[str] = None
    options: Optional[list[str]] = None
    validations: list[FieldValidation] = []


class FormSchema(BaseModel):
    fields: list[FieldDefinition]


class FormDefinitionCreate(BaseModel):
    name: str
    schema_json: FormSchema


class FormDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    schema_json: dict
    version: int


class ProcessNode(BaseModel):
    id: str
    type: str  # "start", "approval", "condition", "end"
    assignee: Optional[str] = None


class ProcessEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None


class ProcessDefinitionSchema(BaseModel):
    nodes: list[ProcessNode]
    edges: list[ProcessEdge]


class ProcessDefinitionCreate(BaseModel):
    name: str
    definition_json: ProcessDefinitionSchema


class ProcessDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    definition_json: dict
    version: int


class StartProcessRequest(BaseModel):
    process_definition_id: int
    form_data: dict


class ApprovalRequest(BaseModel):
    process_instance_id: int
    assignee: str
    decision: str  # "approve", "reject", or "return"
    comment: Optional[str] = None


class ResubmitRequest(BaseModel):
    process_instance_id: int
    form_data: dict


class ApprovalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_instance_id: int
    node_id: str
    assignee: str
    decision: Optional[str]
    comment: Optional[str]
    created_at: Optional[datetime] = None


class ProcessInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_definition_id: int
    form_instance_id: Optional[int]
    current_node_id: str
    status: str


# --- Simulation schemas ---

class SimulationDecision(BaseModel):
    node_id: str
    decision: str  # "approve", "reject", "return"


class SimulateRequest(BaseModel):
    definition: ProcessDefinitionSchema
    form_data: dict
    decisions: list[SimulationDecision] = []
    auto_approve: bool = False


class ConditionEvalDetail(BaseModel):
    expression: str
    field_name: str
    field_value: Optional[str | int | float] = None
    compare_value: Optional[str | int | float] = None
    operator: str
    result: bool


class SimulationStep(BaseModel):
    step_index: int
    node_id: str
    node_type: str
    assignee: Optional[str] = None
    status: str  # "running", "completed", "rejected", "returned", "waiting_for_decision"
    decision_made: Optional[str] = None
    condition_evaluations: list[ConditionEvalDetail] = []
    form_data: dict


class SimulateResponse(BaseModel):
    steps: list[SimulationStep]
    final_status: str
    visited_node_ids: list[str]
    all_node_ids: list[str]
    unvisited_node_ids: list[str]
    coverage_percent: float
