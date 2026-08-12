"""Validation rules carried over from the legacy InfoPath rule sets."""
import pytest
from app.services import ValidationService, SubmissionService
from app.extensions import db
from app.constants import (AttestationType, QUESTION_CATALOG, GROUP2_EXCEPTION_CODE,
                           GROUP1_EXCEPTION_CODE)

CONFIG = {"GROUP1_EXCEPTION_THRESHOLD": 250000, "GROUP2_EXCEPTION_THRESHOLD": 450000,
          "DEFAULT_NO_EXCEPTION_TEXT": "None noted", "REQUIRE_ACKNOWLEDGEMENT": True}


def _draft(app, period, entity):
    with app.app_context():
        return SubmissionService({**CONFIG, **app.config}).start_draft(
            period_id=period.PeriodId, entity_id=entity.EntityId,
            actor_upn="vpandey@atkore.com", employee_name="Vikash Pandey",
            preparer_role="Controller")


def _attach(submission):
    return db.session.merge(submission)


def _codes(result):
    return {i.code for i in result.issues}


def _fields(result):
    return {i.field for i in result.issues}


def test_draft_creation_seeds_ten_questions_plus_group2(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        codes = {r.QuestionCode for r in submission.responses}
        assert len(QUESTION_CATALOG) == 10
        assert {c for c, _, _ in QUESTION_CATALOG} <= codes
        assert GROUP2_EXCEPTION_CODE in codes
        assert GROUP1_EXCEPTION_CODE not in codes  # entity is Group 2 only


def test_submit_requires_at_least_one_attestation(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert not result.is_valid
        assert "attestations" in _fields(result)


def test_yes_answer_requires_explanation(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        for a in submission.attestations:
            if a.AttestationType == AttestationType.QUESTIONNAIRE_302:
                a.Selected = True
                a.Acknowledged = True
        for r in submission.responses:
            r.Answer = False
        target = next(r for r in submission.responses if r.QuestionCode == "FRAUD_INDICATORS")
        target.Answer = True
        target.Explanation = ""

        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert not result.is_valid
        assert "question.FRAUD_INDICATORS.explanation" in _fields(result)
        assert "explanation_required" in _codes(result)


def test_yes_answer_with_explanation_passes(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        for a in submission.attestations:
            if a.AttestationType == AttestationType.QUESTIONNAIRE_302:
                a.Selected = True
                a.Acknowledged = True
        for r in submission.responses:
            r.Answer = False
            r.Explanation = "None noted"
        target = next(r for r in submission.responses if r.QuestionCode == "SYSTEM_CHANGE")
        target.Answer = True
        target.Explanation = "ERP upgrade completed in January."

        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert result.is_valid, result.to_dict()


def test_selected_module_requires_acknowledgement(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        for a in submission.attestations:
            if a.AttestationType == AttestationType.LEGAL_REPRESENTATION:
                a.Selected = True
                a.Acknowledged = False
        for r in submission.responses:
            r.Answer = False

        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert not result.is_valid
        assert "acknowledgement_required" in _codes(result)


def test_group2_threshold_question_requires_explanation(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        for a in submission.attestations:
            if a.AttestationType == AttestationType.MANAGEMENT_REPRESENTATION:
                a.Selected = True
                a.Acknowledged = True
        for r in submission.responses:
            r.Answer = False
        threshold = next(r for r in submission.responses
                         if r.QuestionCode == GROUP2_EXCEPTION_CODE)
        threshold.Answer = True
        threshold.Explanation = ""

        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert not result.is_valid
        issue = next(i for i in result.issues
                     if i.field == f"question.{GROUP2_EXCEPTION_CODE}.explanation")
        assert "$450,000" in issue.message


def test_no_exception_default_text_applied(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        for a in submission.attestations:
            if a.AttestationType == AttestationType.FINANCE_CODE_OF_CONDUCT:
                a.Selected = True
                a.Acknowledged = True
        for r in submission.responses:
            r.Answer = False
            r.Explanation = None

        ValidationService(CONFIG).apply_no_exception_defaults(submission)
        assert all(r.Explanation == "None noted" for r in submission.responses)
        selected = next(a for a in submission.attestations
                        if a.AttestationType == AttestationType.FINANCE_CODE_OF_CONDUCT)
        assert selected.ExceptionText == "None noted"


def test_header_fields_are_required(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        submission.EmployeeName = ""
        submission.PreparerRole = ""
        result = ValidationService(CONFIG).validate_for_submit(submission)
        assert {"EmployeeName", "PreparerRole"} <= _fields(result)


def test_404_module_absent_when_period_disables_it(app, open_period, group2_entity):
    submission = _draft(app, open_period, group2_entity)
    with app.app_context():
        submission = _attach(submission)
        types = {a.AttestationType for a in submission.attestations}
        assert AttestationType.CERTIFICATION_404 not in types
        assert len(types) == 4
