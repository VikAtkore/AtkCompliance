"""SubmissionService -- lifecycle, status transitions, scoping."""
from sqlalchemy import select, or_
from ..extensions import db
from ..models import (Submission, QuestionnaireResponse, Attestation,
                      CertificationPeriod, EntityMaster)
from ..constants import (SubmissionStatus, ALLOWED_STATUS_TRANSITIONS, AuditAction,
                         QUESTION_CATALOG, AttestationType, GROUP1_EXCEPTION_CODE,
                         GROUP2_EXCEPTION_CODE)
from ..models.base import utcnow
from .audit_service import AuditService, snapshot
from .validation_service import ValidationService

AUDITED_FIELDS = ["Status", "PeriodId", "EntityId", "EmployeeName", "Region",
                  "BusinessSegment", "BusinessUnit", "Location", "PreparerRole",
                  "Group1Entity", "Group2Entity"]


class TransitionError(Exception):
    pass


class SubmissionService:
    def __init__(self, config: dict):
        self.config = config
        self.validator = ValidationService(config)

    # ---- Creation ----
    def start_draft(self, *, period_id: int, entity_id: int | None, actor_upn: str,
                    employee_name: str, preparer_role: str, **header) -> Submission:
        period = db.session.get(CertificationPeriod, period_id)
        if period is None or not period.IsOpen:
            raise TransitionError("The selected certification period is not open.")

        entity = db.session.get(EntityMaster, entity_id) if entity_id else None
        submission = Submission(
            PeriodId=period_id,
            EntityId=entity_id,
            EmployeeName=employee_name,
            EmployeeUserPrincipalName=actor_upn,
            PreparerRole=preparer_role,
            Region=header.get("region") or (entity.Region if entity else None),
            BusinessSegment=header.get("business_segment") or (entity.BusinessSegment if entity else None),
            BusinessUnit=header.get("business_unit") or (entity.BusinessUnit if entity else None),
            Location=header.get("location") or (entity.Location if entity else None),
            Group1Entity=entity.IsGroup1 if entity else None,
            Group2Entity=entity.IsGroup2 if entity else None,
            Status=SubmissionStatus.DRAFT,
            CreatedBy=actor_upn,
        )
        db.session.add(submission)
        db.session.flush()

        self._seed_questionnaire(submission)
        self._seed_attestations(submission, period)
        db.session.commit()

        AuditService.record("Submission", submission.SubmissionId, AuditAction.CREATE,
                            after=snapshot(submission, AUDITED_FIELDS))
        return submission

    def _seed_questionnaire(self, submission: Submission) -> None:
        for code, text, order in QUESTION_CATALOG:
            db.session.add(QuestionnaireResponse(
                SubmissionId=submission.SubmissionId, QuestionCode=code,
                QuestionText=text, RequiresExplanationWhenYes=True, DisplayOrder=order))

        g1 = self.config.get("GROUP1_EXCEPTION_THRESHOLD", 250000)
        g2 = self.config.get("GROUP2_EXCEPTION_THRESHOLD", 450000)
        if submission.Group2Entity:
            db.session.add(QuestionnaireResponse(
                SubmissionId=submission.SubmissionId, QuestionCode=GROUP2_EXCEPTION_CODE,
                QuestionText=f"Are there exceptions over ${g2:,}?",
                RequiresExplanationWhenYes=True, DisplayOrder=5))
        if submission.Group1Entity:
            db.session.add(QuestionnaireResponse(
                SubmissionId=submission.SubmissionId, QuestionCode=GROUP1_EXCEPTION_CODE,
                QuestionText=f"Are there exceptions over ${g1:,}?",
                RequiresExplanationWhenYes=True, DisplayOrder=6))

    def _seed_attestations(self, submission: Submission, period: CertificationPeriod) -> None:
        for att_type in AttestationType:
            if att_type == AttestationType.CERTIFICATION_404 and not period.Enable404:
                continue
            db.session.add(Attestation(SubmissionId=submission.SubmissionId,
                                       AttestationType=att_type.value))

    # ---- Editing ----
    def update_header(self, submission: Submission, changes: dict, actor_upn: str) -> Submission:
        self._assert_editable(submission)
        before = snapshot(submission, AUDITED_FIELDS)
        for key, value in changes.items():
            if hasattr(submission, key) and key not in ("SubmissionId", "Status"):
                setattr(submission, key, value)
        submission.ModifiedBy = actor_upn
        submission.RowVersion += 1
        db.session.commit()
        AuditService.record("Submission", submission.SubmissionId, AuditAction.EDIT,
                            before=before, after=snapshot(submission, AUDITED_FIELDS))
        return submission

    # ---- Status transitions ----
    def submit(self, submission: Submission, actor_upn: str):
        self._assert_editable(submission)
        self.validator.apply_no_exception_defaults(submission)
        result = self.validator.validate_for_submit(submission)
        if not result.is_valid:
            return result

        self._transition(submission, SubmissionStatus.SUBMITTED, actor_upn,
                         AuditAction.SUBMIT)
        submission.SubmittedUtc = utcnow()
        db.session.commit()
        return result

    def reopen(self, submission: Submission, actor_upn: str, reason: str) -> Submission:
        self._transition(submission, SubmissionStatus.DRAFT, actor_upn,
                         AuditAction.REOPEN, details={"reason": reason},
                         force_from={SubmissionStatus.SUBMITTED, SubmissionStatus.RETURNED,
                                     SubmissionStatus.UNDER_REVIEW})
        db.session.commit()
        return submission

    def return_to_submitter(self, submission: Submission, actor_upn: str,
                            comment: str) -> Submission:
        submission.ReviewerComment = comment
        submission.ReviewedBy = actor_upn
        submission.ReviewedUtc = utcnow()
        self._transition(submission, SubmissionStatus.RETURNED, actor_upn,
                         AuditAction.RETURN, details={"comment": comment})
        db.session.commit()
        return submission

    def accept(self, submission: Submission, actor_upn: str) -> Submission:
        submission.ReviewedBy = actor_upn
        submission.ReviewedUtc = utcnow()
        self._transition(submission, SubmissionStatus.ACCEPTED, actor_upn, AuditAction.ACCEPT)
        db.session.commit()
        return submission

    def archive(self, submission: Submission, actor_upn: str) -> Submission:
        self._transition(submission, SubmissionStatus.ARCHIVED, actor_upn, AuditAction.ARCHIVE)
        submission.ArchivedUtc = utcnow()
        db.session.commit()
        return submission

    def _transition(self, submission, target, actor_upn, action, details=None,
                    force_from=None):
        current = SubmissionStatus(submission.Status)
        allowed = ALLOWED_STATUS_TRANSITIONS.get(current, set())
        if target not in allowed and not (force_from and current in force_from):
            raise TransitionError(f"Cannot move a {current} submission to {target}.")
        before = snapshot(submission, AUDITED_FIELDS)
        submission.Status = target
        submission.ModifiedBy = actor_upn
        submission.RowVersion += 1
        AuditService.record("Submission", submission.SubmissionId, action,
                            before=before, after=snapshot(submission, AUDITED_FIELDS),
                            details=details, commit=False)

    def _assert_editable(self, submission: Submission) -> None:
        if not submission.is_editable:
            raise TransitionError(
                f"This submission is {submission.Status} and can no longer be edited.")

    # ---- Scoped querying ----
    @staticmethod
    def scoped_query(current_user):
        """Row-level filter applied to every list/report query."""
        from ..auth.permissions import P
        stmt = select(Submission)
        if current_user.can(P.SUBMISSION_VIEW_ALL):
            return stmt
        if current_user.can(P.SUBMISSION_VIEW_SCOPED):
            clauses = [Submission.EmployeeUserPrincipalName == current_user.upn]
            if current_user.scope_regions:
                clauses.append(Submission.Region.in_(current_user.scope_regions))
            if current_user.scope_business_units:
                clauses.append(Submission.BusinessUnit.in_(current_user.scope_business_units))
            if current_user.scope_entity_ids:
                clauses.append(Submission.EntityId.in_(current_user.scope_entity_ids))
            if current_user.unscoped:
                return stmt
            return stmt.where(or_(*clauses))
        return stmt.where(Submission.EmployeeUserPrincipalName == current_user.upn)
