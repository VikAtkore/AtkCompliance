"""Reminder configuration and run-log API."""
from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import select
from ..extensions import db
from ..models import (ReminderMilestone, ReminderRecipient, ReminderTemplate,
                      ReminderRunLog)
from ..auth.decorators import require_permission
from ..auth.permissions import P
from ..services import ReminderService, AuditService
from ..constants import AuditAction

bp = Blueprint("reminders", __name__, url_prefix="/api/reminders")


@bp.get("/milestones")
@require_permission(P.REMINDER_MANAGE)
def list_milestones():
    rows = db.session.scalars(select(ReminderMilestone)).all()
    return jsonify(items=[{
        "reminderMilestoneId": m.ReminderMilestoneId, "periodId": m.PeriodId,
        "title": m.Title,
        "reminderDate": m.ReminderDate.isoformat() if m.ReminderDate else None,
        "offsetDaysFromDue": m.OffsetDaysFromDue, "level": m.ReminderLevel,
        "templateId": m.TemplateId, "isActive": m.IsActive,
        "recipientCount": len(m.recipients),
    } for m in rows])


@bp.post("/milestones")
@require_permission(P.REMINDER_MANAGE)
def create_milestone():
    payload = request.get_json(silent=True) or {}
    milestone = ReminderMilestone(
        PeriodId=payload.get("periodId"), Title=payload.get("title"),
        ReminderDate=payload.get("reminderDate"),
        OffsetDaysFromDue=payload.get("offsetDaysFromDue"),
        ReminderLevel=payload.get("level"), TemplateId=payload.get("templateId"),
        CreatedBy=g.current_user.upn)
    db.session.add(milestone)
    db.session.commit()
    AuditService.record("ReminderMilestone", milestone.ReminderMilestoneId,
                        AuditAction.ADMIN_CHANGE, after=payload)
    return jsonify(reminderMilestoneId=milestone.ReminderMilestoneId), 201


@bp.post("/milestones/<int:milestone_id>/recipients")
@require_permission(P.REMINDER_MANAGE)
def add_recipient(milestone_id):
    payload = request.get_json(silent=True) or {}
    recipient = ReminderRecipient(
        ReminderMilestoneId=milestone_id, EntityId=payload.get("entityId"),
        RoleName=payload.get("roleName"),
        UserPrincipalName=payload.get("userPrincipalName"),
        Email=payload.get("email"), EscalationLevel=payload.get("escalationLevel", 1))
    db.session.add(recipient)
    db.session.commit()
    AuditService.record("ReminderRecipient", recipient.ReminderRecipientId,
                        AuditAction.ADMIN_CHANGE, after=payload)
    return jsonify(reminderRecipientId=recipient.ReminderRecipientId), 201


@bp.get("/templates")
@require_permission(P.REMINDER_MANAGE)
def list_templates():
    rows = db.session.scalars(select(ReminderTemplate)).all()
    return jsonify(items=[{
        "templateId": t.TemplateId, "name": t.Name, "subject": t.Subject,
        "targetAudience": t.TargetAudience, "isActive": t.IsActive,
    } for t in rows])


@bp.get("/runs")
@require_permission(P.REMINDER_MANAGE)
def list_runs():
    rows = db.session.scalars(
        select(ReminderRunLog).order_by(ReminderRunLog.RunUtc.desc()).limit(500)).all()
    return jsonify(items=[{
        "runLogId": r.RunLogId, "milestoneId": r.ReminderMilestoneId,
        "runUtc": r.RunUtc.isoformat(), "recipient": r.RecipientEmail,
        "status": r.Status, "error": r.ErrorMessage,
    } for r in rows])


@bp.post("/run")
@require_permission(P.REMINDER_RUN)
def run_now():
    summary = ReminderService(current_app.config).run()
    return jsonify(summary)
