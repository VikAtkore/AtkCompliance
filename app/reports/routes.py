"""Reviewer dashboard and export API."""
from flask import Blueprint, Response, g, jsonify, request
from ..auth.decorators import require_permission
from ..auth.permissions import P
from ..services import ReportingService, ReminderService
from ..submissions.serializers import submission_to_dict

bp = Blueprint("reports", __name__, url_prefix="/api/reports")

FILTER_KEYS = ("period_id", "entity_id", "region", "business_unit", "location",
               "status", "preparer_role")


def _filters() -> dict:
    filters = {}
    for key in FILTER_KEYS:
        value = request.args.get(key)
        if value:
            filters[key] = int(value) if key.endswith("_id") else value
    return filters


@bp.get("/submissions")
@require_permission(P.REPORT_VIEW)
def search():
    result = ReportingService.search(
        g.current_user, _filters(),
        page=request.args.get("page", 1, type=int),
        page_size=min(request.args.get("pageSize", 50, type=int), 200))
    return jsonify(total=result["total"], page=result["page"],
                   pageSize=result["pageSize"],
                   items=[submission_to_dict(s, summary=True) for s in result["items"]])


@bp.get("/summary")
@require_permission(P.REPORT_VIEW)
def summary():
    period_id = request.args.get("period_id", type=int)
    if not period_id:
        return jsonify(error="invalid_request", message="period_id is required."), 400
    return jsonify(ReportingService.status_summary(g.current_user, period_id))


@bp.get("/missing")
@require_permission(P.REPORT_VIEW_MISSING)
def missing():
    period_id = request.args.get("period_id", type=int)
    if not period_id:
        return jsonify(error="invalid_request", message="period_id is required."), 400
    entities = ReminderService.missing_submissions(period_id)
    return jsonify(periodId=period_id, count=len(entities), items=[{
        "entityId": e.EntityId, "title": e.Title, "entityNumber": e.EntityNumber,
        "region": e.Region, "businessUnit": e.BusinessUnit,
    } for e in entities])


@bp.get("/export")
@require_permission(P.REPORT_EXPORT)
def export():
    payload = ReportingService.export_xlsx(g.current_user, _filters(), g.current_user.upn)
    return Response(
        payload,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition":
                 'attachment; filename="compliance_submissions.xlsx"'})
