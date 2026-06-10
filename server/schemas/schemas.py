from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
import warnings

warnings.filterwarnings("ignore", message=".*shadows an attribute.*")


class FieldValidation(BaseModel):
    rule: str  # "required", "maxLength", "regex", "range"
    value: Optional[str | int | float | bool] = None
    message: Optional[str] = None
    message_i18n: Optional[dict[str, str]] = None


class FieldDefinition(BaseModel):
    fieldId: str
    type: str  # "text", "dropdown", "date"
    label: str
    label_i18n: Optional[dict[str, str]] = None
    placeholder: Optional[str] = None
    placeholder_i18n: Optional[dict[str, str]] = None
    options: Optional[list[str]] = None
    options_i18n: Optional[dict[str, list[str]]] = None
    validations: list[FieldValidation] = []


class FormSchema(BaseModel):
    fields: list[FieldDefinition]
    supported_locales: list[str] = ["zh"]


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
    name: Optional[str] = None
    name_i18n: Optional[dict[str, str]] = None
    assignee: Optional[str] = None
    sla_hours: Optional[float] = None


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


# --- Statistics schemas ---

class StatisticsFilter(BaseModel):
    process_definition_id: Optional[int] = None
    assignee: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class NodeDurationStat(BaseModel):
    node_id: str
    avg_seconds: float
    count: int


class AvgDurationResponse(BaseModel):
    overall_avg_seconds: float
    by_node: list[NodeDurationStat]


class NodeTimeoutStat(BaseModel):
    node_id: str
    total: int
    exceeded: int
    rate_percent: float


class TimeoutRateResponse(BaseModel):
    total_completed: int
    total_exceeded: int
    rate_percent: float
    by_node: list[NodeTimeoutStat]


class TrendDataPoint(BaseModel):
    period: str
    completed: int
    rejected: int
    returned: int
    total: int


class CompletionTrendResponse(BaseModel):
    granularity: str
    data_points: list[TrendDataPoint]


class BacklogNodeStat(BaseModel):
    node_id: str
    assignee: Optional[str]
    count: int
    oldest_enter_time: Optional[datetime]


class SlaAtRiskItem(BaseModel):
    process_instance_id: int
    node_id: str
    assignee: Optional[str]
    enter_time: Optional[datetime]
    sla_hours: float
    elapsed_hours: float


class BacklogResponse(BaseModel):
    total_pending: int
    by_node: list[BacklogNodeStat]
    sla_at_risk: list[SlaAtRiskItem]
