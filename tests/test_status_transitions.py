"""Submission lifecycle guards."""
import pytest
from app.services import SubmissionService, TransitionError
from app.constants import SubmissionStatus, AttestationType


def _valid_draft(app, period, entity):
    service = SubmissionService(app.config)
    submission = service.start_draft(
        period_id=period.PeriodId, entity_id=entity.EntityId,
        actor_upn="vpandey@atkore.com", employee_name="Vikash Pandey",
        preparer_role="Controller")
    for a in submission.attestations:
        if a.AttestationType == AttestationType.MANAGEMENT_REPRESENTATION:
            a.Selected = True
            a.Acknowledged = True
    for r in submission.responses:
        r.Answer = False
    return service, submission


def test_submit_moves_draft_to_submitted(app, open_period, group2_entity):
    with app.app_context():
        service, submission = _valid_draft(app, open_period, group2_entity)
        result = service.submit(submission, "vpandey@atkore.com")
        assert result.is_valid, result.to_dict()
        assert submission.Status == SubmissionStatus.SUBMITTED
        assert submission.SubmittedUtc is not None


def test_submitted_record_is_not_editable(app, open_period, group2_entity):
    with app.app_context():
        service, submission = _valid_draft(app, open_period, group2_entity)
        service.submit(submission, "vpandey@atkore.com")
        assert not submission.is_editable
        with pytest.raises(TransitionError):
            service.update_header(submission, {"Location": "Harvey"}, "vpandey@atkore.com")


def test_reviewer_return_reopens_for_editing(app, open_period, group2_entity):
    with app.app_context():
        service, submission = _valid_draft(app, open_period, group2_entity)
        service.submit(submission, "vpandey@atkore.com")
        service.return_to_submitter(submission, "reviewer@atkore.com", "Please attach evidence.")
        assert submission.Status == SubmissionStatus.RETURNED
        assert submission.is_editable


def test_cannot_archive_a_draft(app, open_period, group2_entity):
    with app.app_context():
        service, submission = _valid_draft(app, open_period, group2_entity)
        with pytest.raises(TransitionError):
            service.archive(submission, "admin@atkore.com")


def test_draft_cannot_be_created_in_a_closed_period(app, open_period, group2_entity):
    with app.app_context():
        open_period.IsOpen = False
        from app.extensions import db
        db.session.commit()
        with pytest.raises(TransitionError):
            SubmissionService(app.config).start_draft(
                period_id=open_period.PeriodId, entity_id=group2_entity.EntityId,
                actor_upn="vpandey@atkore.com", employee_name="Vikash Pandey",
                preparer_role="Controller")
