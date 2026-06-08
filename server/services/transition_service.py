from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from models.models import NodeTransitionLog


def open_node_log(
    db: Session,
    process_instance_id: int,
    process_definition_id: int,
    node_id: str,
    node_type: str,
    assignee: Optional[str],
    sla_hours: Optional[float],
):
    log = NodeTransitionLog(
        process_instance_id=process_instance_id,
        process_definition_id=process_definition_id,
        node_id=node_id,
        node_type=node_type,
        assignee=assignee,
        enter_time=datetime.utcnow(),
        sla_hours=sla_hours,
    )
    db.add(log)
    return log


def close_current_node_log(db: Session, process_instance_id: int):
    log = db.query(NodeTransitionLog).filter(
        NodeTransitionLog.process_instance_id == process_instance_id,
        NodeTransitionLog.leave_time.is_(None),
    ).first()
    if log:
        now = datetime.utcnow()
        log.leave_time = now
        delta = (now - log.enter_time).total_seconds()
        log.duration_seconds = int(delta)
        if log.sla_hours is not None:
            sla_seconds = log.sla_hours * 3600
            if delta > sla_seconds:
                log.sla_exceeded = 1
    return log


def open_node_log_from_definition(
    db: Session,
    process_instance_id: int,
    process_definition_id: int,
    node_id: str,
    definition_json: dict,
):
    node_info = _find_node_in_definition(node_id, definition_json)
    node_type = node_info.get("type", "unknown") if node_info else "unknown"
    assignee = node_info.get("assignee") if node_info else None
    sla_hours = node_info.get("sla_hours") if node_info else None
    return open_node_log(
        db, process_instance_id, process_definition_id,
        node_id, node_type, assignee, sla_hours,
    )


def _find_node_in_definition(node_id: str, definition_json: dict) -> Optional[dict]:
    nodes = definition_json.get("nodes", [])
    for node in nodes:
        if node.get("id") == node_id:
            return node
    return None


def log_condition_nodes_traversed(
    db: Session,
    process_instance_id: int,
    process_definition_id: int,
    condition_node_ids: list[str],
    definition_json: dict,
):
    now = datetime.utcnow()
    for node_id in condition_node_ids:
        log = NodeTransitionLog(
            process_instance_id=process_instance_id,
            process_definition_id=process_definition_id,
            node_id=node_id,
            node_type="condition",
            assignee=None,
            enter_time=now,
            leave_time=now,
            duration_seconds=0,
            sla_hours=None,
            sla_exceeded=0,
        )
        db.add(log)
