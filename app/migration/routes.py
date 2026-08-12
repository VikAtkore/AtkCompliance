"""Legacy import API. SystemAdmin only -- never enabled for general users."""
from flask import Blueprint, g, jsonify, request
from ..auth.decorators import require_permission
from ..auth.permissions import P
from ..services import MigrationService

bp = Blueprint("migration", __name__, url_prefix="/api/migration")


@bp.post("/xml/stage")
@require_permission(P.MIGRATION_RUN)
def stage_xml():
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify(error="invalid_request", message="No file part provided."), 400
    row = MigrationService.stage_xml(
        file_name=uploaded.filename,
        raw_xml=uploaded.read().decode("utf-8", errors="replace"),
        source_library=request.form.get("sourceLibrary", "Submitted Forms"),
        source_path=request.form.get("sourcePath"))
    return jsonify(stageId=row.StageId), 201


@bp.post("/vlookup/merge")
@require_permission(P.MIGRATION_RUN)
def merge_vlookup():
    return jsonify(MigrationService.merge_vlookup())


@bp.get("/reconcile")
@require_permission(P.MIGRATION_RUN)
def reconcile():
    period_id = request.args.get("period_id", type=int)
    if not period_id:
        return jsonify(error="invalid_request", message="period_id is required."), 400
    return jsonify(MigrationService.reconcile(period_id))
