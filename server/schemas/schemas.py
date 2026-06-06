from pydantic import BaseModel, ConfigDict
from typing import Optional
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
    type: str  # "start", "approval", "end"
    assignee: Optional[str] = None


class ProcessEdge(BaseModel):
    source: str
    target: str


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
    decision: str  # "approve" or "reject"
    comment: Optional[str] = None


class ProcessInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    process_definition_id: int
    form_instance_id: Optional[int]
    current_node_id: str
    status: str
