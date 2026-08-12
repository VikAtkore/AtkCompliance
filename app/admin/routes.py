"""Admin API: periods, entities, reference documents, roles, audit."""
from flask import Blueprint, g, jsonify, request
from sqlalchemy import select
from ..extensions import db
from ..models import (CertificationPeriod, EntityMaster, ReferenceDocument,
                      AppUser, Role, UserRole, AuditLog)
from ..auth.decorators import require_permission
from ..auth.permissions import P
from ..services import EntityService, PeriodService, AuditService
from ..constants import AuditAction

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---- Certification periods ----
@bp.get("/periods")
@require_permission(P.PERIOD_MANAGE)
def list_periods():
    rows = db.session.scalars(
        select(CertificationPeriod).order_by(CertificationPeriod.StartDate.desc())).all()
    return jsonify(items=[{
        "periodId": p.PeriodId, "quarterLabel": p.QuarterLabel,
        "fiscalYear": p.FiscalYear, "quarterNumber": p.QuarterNumber,
        "startDate": p.StartDate.isoformat() if p.StartDate else None,
        "dueDate": p.DueDate.isoformat() if p.DueDate else None,
        "isOpen": p.IsOpen, "enable404": p.Enable404, "isArchived": p.IsArchived,
    } for p in rows])


@bp.post("/periods")
@require_permission(P.PERIOD_MANAGE)
def create_period():
    period = PeriodService.create(request.get_json(silent=True) or {}, g.current_user.upn)
    return jsonify(periodId=period.PeriodId), 201


@bp.patch("/periods/<int:period_id>")
@require_permission(P.PERIOD_MANAGE)
def update_period(period_id):
    period = db.session.get(CertificationPeriod, period_id)
    if period is None:
        return jsonify(error="not_found"), 404
    PeriodService.update(period, request.get_json(silent=True) or {}, g.current_user.upn)
    return jsonify(periodId=period.PeriodId)


# ---- Entity master ----
@bp.get("/entities")
@require_permission(P.ENTITY_MANAGE)
def list_entities():
    rows = db.session.scalars(select(EntityMaster).order_by(EntityMaster.Title)).all()
    return jsonify(items=[{
        "entityId": e.EntityId, "title": e.Title, "entityNumber": e.EntityNumber,
        "pullName": e.PullName, "submitName": e.SubmitName,
        "submittedCode": e.SubmittedCode, "region": e.Region,
        "businessSegment": e.BusinessSegment, "businessUnit": e.BusinessUnit,
        "location": e.Location, "isGroup1": e.IsGroup1, "isGroup2": e.IsGroup2,
        "isActive": e.IsActive,
    } for e in rows])


@bp.post("/entities")
@require_permission(P.ENTITY_MANAGE)
def create_entity():
    entity = EntityService.create(request.get_json(silent=True) or {}, g.current_user.upn)
    return jsonify(entityId=entity.EntityId), 201


@bp.patch("/entities/<int:entity_id>")
@require_permission(P.ENTITY_MANAGE)
def update_entity(entity_id):
    entity = db.session.get(EntityMaster, entity_id)
    if entity is None:
        return jsonify(error="not_found"), 404
    EntityService.update(entity, request.get_json(silent=True) or {}, g.current_user.upn)
    return jsonify(entityId=entity.EntityId)


# ---- Reference documents ----
@bp.get("/reference-documents")
@require_permission(P.REFDOC_MANAGE)
def list_reference_documents():
    rows = db.session.scalars(select(ReferenceDocument)).all()
    return jsonify(items=[{
        "referenceDocumentId": d.ReferenceDocumentId, "periodId": d.PeriodId,
        "attestationType": d.AttestationType, "title": d.Title,
        "storageUrl": d.StorageUrl, "isActive": d.IsActive,
    } for d in rows])


@bp.post("/reference-documents")
@require_permission(P.REFDOC_MANAGE)
def create_reference_document():
    payload = request.get_json(silent=True) or {}
    doc = ReferenceDocument(
        PeriodId=payload.get("periodId"),
        AttestationType=payload.get("attestationType"),
        Title=payload.get("title"), StorageUrl=payload.get("storageUrl"),
        GraphItemId=payload.get("graphItemId"),
        DisplayOrder=payload.get("displayOrder", 0), CreatedBy=g.current_user.upn)
    db.session.add(doc)
    db.session.commit()
    AuditService.record("ReferenceDocument", doc.ReferenceDocumentId,
                        AuditAction.ADMIN_CHANGE, after=payload)
    return jsonify(referenceDocumentId=doc.ReferenceDocumentId), 201


# ---- Roles ----
@bp.get("/users")
@require_permission(P.ROLE_MANAGE)
def list_users():
    rows = db.session.scalars(select(AppUser).order_by(AppUser.DisplayName)).all()
    return jsonify(items=[{
        "userId": u.UserId, "displayName": u.DisplayName,
        "userPrincipalName": u.UserPrincipalName, "isActive": u.IsActive,
        "roles": sorted(u.role_names),
        "lastLoginUtc": u.LastLoginUtc.isoformat() if u.LastLoginUtc else None,
    } for u in rows])


@bp.post("/users/<int:user_id>/roles")
@require_permission(P.ROLE_MANAGE)
def grant_role(user_id):
    payload = request.get_json(silent=True) or {}
    user = db.session.get(AppUser, user_id)
    role = db.session.scalar(select(Role).where(Role.RoleName == payload.get("roleName")))
    if user is None or role is None:
        return jsonify(error="not_found"), 404
    assignment = UserRole(
        UserId=user.UserId, RoleId=role.RoleId,
        ScopeRegion=payload.get("scopeRegion"),
        ScopeBusinessUnit=payload.get("scopeBusinessUnit"),
        ScopeEntityId=payload.get("scopeEntityId"),
        GrantedBy=g.current_user.upn)
    db.session.add(assignment)
    db.session.commit()
    AuditService.record("UserRole", assignment.UserRoleId, AuditAction.ROLE_CHANGE,
                        after=payload)
    return jsonify(userRoleId=assignment.UserRoleId), 201


@bp.delete("/users/<int:user_id>/roles/<int:user_role_id>")
@require_permission(P.ROLE_MANAGE)
def revoke_role(user_id, user_role_id):
    assignment = db.session.get(UserRole, user_role_id)
    if assignment is None or assignment.UserId != user_id:
        return jsonify(error="not_found"), 404
    assignment.IsActive = False
    db.session.commit()
    AuditService.record("UserRole", user_role_id, AuditAction.ROLE_CHANGE,
                        details={"revoked": True})
    return "", 204


# ---- Audit ----
@bp.get("/audit")
@require_permission(P.AUDIT_VIEW)
def list_audit():
    stmt = select(AuditLog).order_by(AuditLog.EventUtc.desc())
    if request.args.get("entityName"):
        stmt = stmt.where(AuditLog.EntityName == request.args["entityName"])
    if request.args.get("entityKey"):
        stmt = stmt.where(AuditLog.EntityKey == request.args["entityKey"])
    if request.args.get("actor"):
        stmt = stmt.where(AuditLog.Actor == request.args["actor"])
    rows = db.session.scalars(stmt.limit(request.args.get("limit", 200, type=int))).all()
    return jsonify(items=[{
        "auditLogId": a.AuditLogId, "entityName": a.EntityName,
        "entityKey": a.EntityKey, "action": a.Action, "actor": a.Actor,
        "eventUtc": a.EventUtc.isoformat(), "beforeJson": a.BeforeJson,
        "afterJson": a.AfterJson, "detailsJson": a.DetailsJson,
    } for a in rows])
