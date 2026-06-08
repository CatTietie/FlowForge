from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from database import get_db
from models.models import NodeTransitionLog, ProcessInstance

router = APIRouter(prefix="/api/statistics", tags=["statistics"])


def _to_period(dt: datetime, granularity: str) -> str:
    if granularity == "day":
        return dt.strftime("%Y-%m-%d")
    elif granularity == "week":
        return dt.strftime("%Y-%W")
    else:
        return dt.strftime("%Y-%m")


def _apply_filters(query, model, process_definition_id, assignee, start_date, end_date):
    if process_definition_id is not None:
        query = query.filter(model.process_definition_id == process_definition_id)
    if assignee:
        query = query.filter(model.assignee == assignee)
    if start_date:
        query = query.filter(model.enter_time >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(model.enter_time <= datetime.combine(end_date, datetime.max.time()))
    return query


@router.get("/avg-duration")
def get_avg_duration(
    process_definition_id: Optional[int] = Query(None),
    assignee: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    base = db.query(NodeTransitionLog).filter(
        NodeTransitionLog.leave_time.isnot(None),
        NodeTransitionLog.node_type == "approval",
    )
    base = _apply_filters(base, NodeTransitionLog, process_definition_id, assignee, start_date, end_date)

    overall = base.with_entities(
        sa_func.avg(NodeTransitionLog.duration_seconds),
    ).scalar() or 0.0

    by_node_rows = base.with_entities(
        NodeTransitionLog.node_id,
        sa_func.avg(NodeTransitionLog.duration_seconds),
        sa_func.count(NodeTransitionLog.id),
    ).group_by(NodeTransitionLog.node_id).all()

    return {
        "overall_avg_seconds": round(float(overall), 1),
        "by_node": [
            {"node_id": row[0], "avg_seconds": round(float(row[1] or 0), 1), "count": row[2]}
            for row in by_node_rows
        ],
    }


@router.get("/timeout-rate")
def get_timeout_rate(
    process_definition_id: Optional[int] = Query(None),
    assignee: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    base = db.query(NodeTransitionLog).filter(
        NodeTransitionLog.leave_time.isnot(None),
        NodeTransitionLog.sla_hours.isnot(None),
    )
    base = _apply_filters(base, NodeTransitionLog, process_definition_id, assignee, start_date, end_date)

    total = base.count()
    exceeded = base.filter(NodeTransitionLog.sla_exceeded == 1).count()

    by_node_rows = base.with_entities(
        NodeTransitionLog.node_id,
        sa_func.count(NodeTransitionLog.id),
        sa_func.sum(NodeTransitionLog.sla_exceeded),
    ).group_by(NodeTransitionLog.node_id).all()

    return {
        "total_completed": total,
        "total_exceeded": exceeded,
        "rate_percent": round((exceeded / total * 100) if total > 0 else 0.0, 1),
        "by_node": [
            {
                "node_id": row[0],
                "total": row[1],
                "exceeded": int(row[2] or 0),
                "rate_percent": round((int(row[2] or 0) / row[1] * 100) if row[1] > 0 else 0.0, 1),
            }
            for row in by_node_rows
        ],
    }


@router.get("/completion-trend")
def get_completion_trend(
    granularity: str = Query("day", pattern="^(day|week|month)$"),
    process_definition_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    base = db.query(ProcessInstance).filter(
        ProcessInstance.status.in_(["completed", "rejected", "returned"])
    )
    if process_definition_id is not None:
        base = base.filter(ProcessInstance.process_definition_id == process_definition_id)
    if start_date:
        base = base.filter(ProcessInstance.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        base = base.filter(ProcessInstance.created_at <= datetime.combine(end_date, datetime.max.time()))

    rows = base.with_entities(ProcessInstance.updated_at, ProcessInstance.status).all()

    trend: dict = {}
    for updated_at, status in rows:
        if updated_at is None:
            continue
        period = _to_period(updated_at, granularity)
        if period not in trend:
            trend[period] = {"period": period, "completed": 0, "rejected": 0, "returned": 0, "total": 0}
        trend[period][status] += 1
        trend[period]["total"] += 1

    data_points = sorted(trend.values(), key=lambda x: x["period"])

    return {
        "granularity": granularity,
        "data_points": data_points,
    }


@router.get("/backlog")
def get_backlog(
    process_definition_id: Optional[int] = Query(None),
    assignee: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    base = db.query(NodeTransitionLog).filter(
        NodeTransitionLog.leave_time.is_(None),
    )
    if process_definition_id is not None:
        base = base.filter(NodeTransitionLog.process_definition_id == process_definition_id)
    if assignee:
        base = base.filter(NodeTransitionLog.assignee == assignee)

    total_pending = base.count()

    by_node_rows = base.with_entities(
        NodeTransitionLog.node_id,
        NodeTransitionLog.assignee,
        sa_func.count(NodeTransitionLog.id),
        sa_func.min(NodeTransitionLog.enter_time),
    ).group_by(NodeTransitionLog.node_id, NodeTransitionLog.assignee).all()

    now = datetime.utcnow()
    sla_at_risk = []
    at_risk_logs = base.filter(NodeTransitionLog.sla_hours.isnot(None)).all()
    for log in at_risk_logs:
        elapsed_hours = (now - log.enter_time).total_seconds() / 3600
        if elapsed_hours > log.sla_hours * 0.8:
            sla_at_risk.append({
                "process_instance_id": log.process_instance_id,
                "node_id": log.node_id,
                "assignee": log.assignee,
                "enter_time": log.enter_time.isoformat() if log.enter_time else None,
                "sla_hours": log.sla_hours,
                "elapsed_hours": round(elapsed_hours, 2),
            })

    return {
        "total_pending": total_pending,
        "by_node": [
            {
                "node_id": row[0],
                "assignee": row[1],
                "count": row[2],
                "oldest_enter_time": row[3].isoformat() if row[3] else None,
            }
            for row in by_node_rows
        ],
        "sla_at_risk": sla_at_risk,
    }
