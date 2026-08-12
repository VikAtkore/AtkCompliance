"""Submission API. Phase 1 exposes JSON only -- UI templates land in Phase 2."""
from flask import Blueprint, current_app, g, jsonify, request
from ..extensions import db
from ..models import Submission, Attestation, Attachment, QuestionnaireResponse
from ..auth.decorators import login_required, require_permission
from ..auth.permissions import P
from ..services import (SubmissionService, AttestationService, AttachmentService,
                        ValidationService, TransitionError, AttachmentError)
from .serializers import submission_to_dict, attachment_to_dict

bp = Blueprint("submissions", __name__, url_prefix="/api/submissions")


def _service() -> SubmissionService:
    return SubmissionService(current_app.config)


def _load(submission_id: int) -> Submission:
    submission = db.session.get(Submission, submission_id)
    if submission is None:
        return None
    return submission


def _may_read(submission) -> bool:
    u = g.current_user
    if u.can(P.SUBMISSION_VIEW_ALL):
        return True
    if submission.EmployeeUserPrincipalName == u.upn:
        return True
    if u.can(P.SUBMISSION_VIEW_SCOPED):
        return (submission.Region in u.scope_regions
                or submission.BusinessUnit in u.scope_business_units
                or submission.EntityId in u.scope_entity_ids
                or u.unscoped)
    return False


def _may_write(submission) -> bool:
    u = g.current_user
    if u.can(P.SUBMISSION_EDIT_ANY):
        return True
    return (u.can(P.SUBMISSION_EDIT_OWN)
            and submission.EmployeeUserPrincipalName == u.upn)


@bp.get("")
@require_permission(P.SUBMISSION_VIEW_OWN)
def list_mine():
    stmt = SubmissionService.scoped_query(g.current_user)
    rows = db.session.scalars(stmt.order_by(Submission.CreatedUtc.desc()).limit(200)).all()
    return jsonify(items=[submission_to_dict(s, summary=True) for s in rows])


@bp.post("")
@require_permission(P.SUBMISSION_CREATE)
def create():
    payload = request.get_json(silent=True) or {}
    try:
        submission = _service().start_draft(
            period_id=payload.get("periodId"),
            entity_id=payload.get("entityId"),
            actor_upn=g.current_user.upn,
            employee_name=payload.get("employeeName") or g.current_user.display_name,
            preparer_role=payload.get("preparerRole", ""),
            region=payload.get("region"),
            business_segment=payload.get("businessSegment"),
            business_unit=payload.get("businessUnit"),
            location=payload.get("location"),
        )
    except TransitionError as exc:
        return jsonify(error="invalid_request", message=str(exc)), 400
    return jsonify(submission_to_dict(submission)), 201


@bp.get("/<int:submission_id>")
@login_required
def detail(submission_id):
    submission = _load(submission_id)
    if submission is None:
        return jsonify(error="not_found"), 404
    if not _may_read(submission):
        return jsonify(error="forbidden"), 403
    return jsonify(submission_to_dict(submission))


@bp.patch("/<int:submission_id>")
@require_permission(P.SUBMISSION_EDIT_OWN)
def update(submission_id):
    submission = _load(submission_id)
    if submission is None:
        return jsonify(error="not_found"), 404
    if not _may_write(submission):
        return jsonify(error="forbidden"), 403
    try:
        _service().update_header(submission, request.get_json(silent=True) or {},
                                 g.current_user.upn)
    except TransitionError as exc:
        return jsonify(error="invalid_state", message=str(exc)), 409
    return jsonify(submission_to_dict(submission))


@bp.put("/<int:submission_id>/attestations")
@require_permission(P.SUBMISSION_EDIT_OWN)
def set_attestations(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_write(submission):
        return jsonify(error="forbidden"), 403
    AttestationService.set_selection(
        submission, (request.get_json(silent=True) or {}).get("selectedTypes", []),
        g.current_user.upn)
    return jsonify(submission_to_dict(submission))


@bp.post("/<int:submission_id>/attestations/<int:attestation_id>/acknowledge")
@require_permission(P.SUBMISSION_EDIT_OWN)
def acknowledge(submission_id, attestation_id):
    submission = _load(submission_id)
    attestation = db.session.get(Attestation, attestation_id)
    if submission is None or attestation is None \
            or attestation.SubmissionId != submission_id:
        return jsonify(error="not_found"), 404
    if not _may_write(submission):
        return jsonify(error="forbidden"), 403
    payload = request.get_json(silent=True) or {}
    AttestationService.acknowledge(attestation, g.current_user.upn,
                                   payload.get("exceptionText"))
    return jsonify(submission_to_dict(submission))


@bp.put("/<int:submission_id>/responses")
@require_permission(P.SUBMISSION_EDIT_OWN)
def save_responses(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_write(submission):
        return jsonify(error="forbidden"), 403
    answers = {a.get("questionCode"): a for a in
               (request.get_json(silent=True) or {}).get("responses", [])}
    for response in submission.responses:
        payload = answers.get(response.QuestionCode)
        if payload is None:
            continue
        response.Answer = payload.get("answer")
        response.Explanation = payload.get("explanation")
    db.session.commit()
    return jsonify(submission_to_dict(submission))


@bp.post("/<int:submission_id>/validate")
@login_required
def validate(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_read(submission):
        return jsonify(error="forbidden"), 403
    result = ValidationService(current_app.config).validate_for_submit(submission)
    return jsonify(result.to_dict())


@bp.post("/<int:submission_id>/submit")
@require_permission(P.SUBMISSION_SUBMIT)
def submit(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_write(submission):
        return jsonify(error="forbidden"), 403
    try:
        result = _service().submit(submission, g.current_user.upn)
    except TransitionError as exc:
        return jsonify(error="invalid_state", message=str(exc)), 409
    if not result.is_valid:
        return jsonify(error="validation_failed", **result.to_dict()), 422
    return jsonify(submission_to_dict(submission))


@bp.post("/<int:submission_id>/reopen")
@require_permission(P.SUBMISSION_REOPEN)
def reopen(submission_id):
    submission = _load(submission_id)
    if submission is None:
        return jsonify(error="not_found"), 404
    reason = (request.get_json(silent=True) or {}).get("reason", "")
    try:
        _service().reopen(submission, g.current_user.upn, reason)
    except TransitionError as exc:
        return jsonify(error="invalid_state", message=str(exc)), 409
    return jsonify(submission_to_dict(submission))


# ---- Attachments ----
@bp.post("/<int:submission_id>/attachments")
@require_permission(P.ATTACHMENT_UPLOAD)
def upload_attachment(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_write(submission):
        return jsonify(error="forbidden"), 403
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify(error="invalid_request", message="No file part provided."), 400
    try:
        attachment = AttachmentService(current_app.config).upload(
            submission, uploaded.stream, uploaded.filename, uploaded.mimetype,
            g.current_user.upn,
            attestation_id=request.form.get("attestationId", type=int),
            field_code=request.form.get("fieldCode"))
    except AttachmentError as exc:
        return jsonify(error="upload_failed", message=str(exc)), 400
    return jsonify(attachment_to_dict(attachment)), 201


@bp.get("/<int:submission_id>/attachments")
@login_required
def list_attachments(submission_id):
    submission = _load(submission_id)
    if submission is None or not _may_read(submission):
        return jsonify(error="forbidden"), 403
    return jsonify(items=[attachment_to_dict(a) for a in submission.attachments
                          if not a.IsDeleted])


@bp.get("/<int:submission_id>/attachments/<int:attachment_id>/download")
@login_required
def download_attachment(submission_id, attachment_id):
    submission = _load(submission_id)
    attachment = db.session.get(Attachment, attachment_id)
    if submission is None or attachment is None \
            or attachment.SubmissionId != submission_id:
        return jsonify(error="not_found"), 404
    if not _may_read(submission):
        return jsonify(error="forbidden"), 403
    try:
        url = AttachmentService(current_app.config).download_url(attachment)
    except AttachmentError as exc:
        return jsonify(error="download_failed", message=str(exc)), 502
    return jsonify(downloadUrl=url, fileName=attachment.OriginalFileName)
