import asyncio
import logging
import os
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from database import SessionLocal
from models.models import NodeTransitionLog, SlaAlert

logger = logging.getLogger("flowforge.sla_checker")

CHECK_INTERVAL_SECONDS = 60

# notified field values: 0=pending, 1=sent, 2=failed (retry on next scan)


async def sla_check_loop():
    while True:
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        try:
            _check_sla_violations()
        except Exception as e:
            logger.error(f"SLA check error: {e}")


def _check_sla_violations():
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()

        # 1. Detect new SLA violations
        open_nodes = db.query(NodeTransitionLog).filter(
            NodeTransitionLog.leave_time.is_(None),
            NodeTransitionLog.sla_hours.isnot(None),
        ).all()

        for log in open_nodes:
            deadline = log.enter_time + timedelta(hours=log.sla_hours)
            if now > deadline:
                existing = db.query(SlaAlert).filter(
                    SlaAlert.process_instance_id == log.process_instance_id,
                    SlaAlert.node_id == log.node_id,
                ).first()
                if not existing:
                    alert = SlaAlert(
                        process_instance_id=log.process_instance_id,
                        node_id=log.node_id,
                        assignee=log.assignee,
                        sla_hours=log.sla_hours,
                        exceeded_at=now,
                    )
                    db.add(alert)
                    log.sla_exceeded = 1
                    db.flush()
                    _dispatch_alert(db, alert)

        # 2. Retry previously failed webhook alerts
        failed_alerts = db.query(SlaAlert).filter(SlaAlert.notified == 2).all()
        for alert in failed_alerts:
            _dispatch_alert(db, alert)

        db.commit()
    finally:
        db.close()


def _dispatch_alert(db: Session, alert: SlaAlert):
    logger.warning(
        f"SLA EXCEEDED: instance={alert.process_instance_id}, "
        f"node={alert.node_id}, assignee={alert.assignee}, "
        f"sla={alert.sla_hours}h"
    )
    webhook_url = os.environ.get("SLA_WEBHOOK_URL")
    if webhook_url:
        success = _send_webhook(webhook_url, alert)
        alert.notified = 1 if success else 2
    else:
        alert.notified = 1


def _send_webhook(url: str, alert: SlaAlert) -> bool:
    try:
        import httpx
        payload = {
            "event": "sla_exceeded",
            "process_instance_id": alert.process_instance_id,
            "node_id": alert.node_id,
            "assignee": alert.assignee,
            "sla_hours": alert.sla_hours,
            "exceeded_at": alert.exceeded_at.isoformat() if alert.exceeded_at else None,
        }
        with httpx.Client(timeout=10) as client:
            resp = client.post(url, json=payload)
            if resp.status_code < 300:
                logger.info(f"Webhook sent successfully for instance={alert.process_instance_id}")
                return True
            else:
                logger.warning(f"Webhook returned status {resp.status_code}")
                return False
    except Exception as e:
        logger.error(f"Webhook dispatch failed: {e}")
        return False
