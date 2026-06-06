from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models.models import ProcessDefinition, ProcessInstance, FormInstance, ApprovalRecord
from schemas.schemas import (
    ProcessDefinitionCreate,
    ProcessDefinitionResponse,
    ProcessInstanceResponse,
    StartProcessRequest,
    ApprovalRequest,
)
from engine.process_engine import ProcessEngine, ProcessEngineError

router = APIRouter(prefix="/api/processes", tags=["processes"])


@router.post("/definitions", response_model=ProcessDefinitionResponse)
def create_process_definition(proc: ProcessDefinitionCreate, db: Session = Depends(get_db)):
    existing = db.query(ProcessDefinition).filter(ProcessDefinition.name == proc.name).order_by(ProcessDefinition.version.desc()).first()
    version = (existing.version + 1) if existing else 1

    db_proc = ProcessDefinition(
        name=proc.name,
        definition_json=proc.definition_json.model_dump(),
        version=version,
    )
    db.add(db_proc)
    db.commit()
    db.refresh(db_proc)
    return db_proc


@router.get("/definitions", response_model=list[ProcessDefinitionResponse])
def list_process_definitions(db: Session = Depends(get_db)):
    return db.query(ProcessDefinition).all()


@router.get("/definitions/{proc_id}", response_model=ProcessDefinitionResponse)
def get_process_definition(proc_id: int, db: Session = Depends(get_db)):
    proc = db.query(ProcessDefinition).filter(ProcessDefinition.id == proc_id).first()
    if not proc:
        raise HTTPException(status_code=404, detail="Process definition not found")
    return proc


@router.post("/start", response_model=ProcessInstanceResponse)
def start_process(req: StartProcessRequest, db: Session = Depends(get_db)):
    proc_def = db.query(ProcessDefinition).filter(ProcessDefinition.id == req.process_definition_id).first()
    if not proc_def:
        raise HTTPException(status_code=404, detail="Process definition not found")

    try:
        engine = ProcessEngine(proc_def.definition_json)
        start_node_id = engine.get_start_node_id()
        next_node_id, status = engine.advance(start_node_id)
    except ProcessEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))

    form_instance = FormInstance(
        form_definition_id=proc_def.id,
        data_json=req.form_data,
    )
    db.add(form_instance)
    db.flush()

    process_instance = ProcessInstance(
        process_definition_id=proc_def.id,
        form_instance_id=form_instance.id,
        current_node_id=next_node_id,
        status=status,
    )
    db.add(process_instance)
    db.commit()
    db.refresh(process_instance)
    return process_instance


@router.post("/approve", response_model=ProcessInstanceResponse)
def approve_process(req: ApprovalRequest, db: Session = Depends(get_db)):
    instance = db.query(ProcessInstance).filter(ProcessInstance.id == req.process_instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Process instance not found")
    if instance.status != "running":
        raise HTTPException(status_code=400, detail=f"Process is not running (status: {instance.status})")

    proc_def = db.query(ProcessDefinition).filter(ProcessDefinition.id == instance.process_definition_id).first()
    engine = ProcessEngine(proc_def.definition_json)

    current_assignee = engine.get_current_assignee(instance.current_node_id)
    if current_assignee and current_assignee != req.assignee:
        raise HTTPException(status_code=403, detail=f"Not authorized. Expected assignee: {current_assignee}")

    try:
        next_node_id, status = engine.advance(instance.current_node_id, decision=req.decision)
    except ProcessEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))

    record = ApprovalRecord(
        process_instance_id=instance.id,
        node_id=instance.current_node_id,
        assignee=req.assignee,
        decision=req.decision,
        comment=req.comment,
    )
    db.add(record)

    instance.current_node_id = next_node_id
    instance.status = status
    db.commit()
    db.refresh(instance)
    return instance


@router.get("/instances/{instance_id}", response_model=ProcessInstanceResponse)
def get_process_instance(instance_id: int, db: Session = Depends(get_db)):
    instance = db.query(ProcessInstance).filter(ProcessInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Process instance not found")
    return instance
