"""ValidationService -- the compliance rules carried over from InfoPath.

These are the rules the legacy form enforced through XSF rule sets. They are
implemented here (not in the UI) so the API, the import path and the UI all
enforce identical behaviour.
"""
from dataclasses import dataclass, field
from ..constants import (AttestationType, GROUP1_EXCEPTION_CODE, GROUP2_EXCEPTION_CODE,
                         QUESTION_CATALOG)

REQUIRED_HEADER_FIELDS = [
    ("PeriodId", "Certification quarter"),
    ("EmployeeName", "Your name"),
    ("BusinessSegment", "Business segment"),
    ("PreparerRole", "Preparer role"),
]

QUESTION_CODES = {code for code, _, _ in QUESTION_CATALOG}


@dataclass
class ValidationIssue:
    field: str
    code: str
    message: str
    step: int = 0


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def add(self, field_name: str, code: str, message: str, step: int = 0):
        self.issues.append(ValidationIssue(field_name, code, message, step))

    def to_dict(self) -> dict:
        return {"isValid": self.is_valid,
                "issues": [i.__dict__ for i in self.issues]}


class ValidationService:
    """Stateless rule engine. Pass a Submission with relationships loaded."""

    def __init__(self, config: dict | None = None):
        cfg = config or {}
        self.group1_threshold = cfg.get("GROUP1_EXCEPTION_THRESHOLD", 250000)
        self.group2_threshold = cfg.get("GROUP2_EXCEPTION_THRESHOLD", 450000)
        self.no_exception_text = cfg.get("DEFAULT_NO_EXCEPTION_TEXT", "None noted")
        self.require_ack = cfg.get("REQUIRE_ACKNOWLEDGEMENT", True)

    # ---- Rule 1: required header fields ----
    def validate_header(self, submission, result: ValidationResult) -> None:
        for attr, label in REQUIRED_HEADER_FIELDS:
            if not getattr(submission, attr, None):
                result.add(attr, "required", f"{label} is required.", step=1)

    # ---- Rule 2: at least one certification module selected ----
    def validate_attestation_selection(self, submission, result: ValidationResult) -> None:
        selected = [a for a in submission.attestations if a.Selected]
        if not selected:
            result.add("attestations", "required",
                       "Select at least one certification type.", step=2)

    # ---- Rule 3: acknowledgement required for each selected module ----
    def validate_acknowledgements(self, submission, result: ValidationResult) -> None:
        if not self.require_ack:
            return
        for a in submission.attestations:
            if a.Selected and not a.Acknowledged:
                result.add(f"attestation.{a.AttestationType}.acknowledged", "acknowledgement_required",
                           f"You must acknowledge the {a.AttestationType} certification "
                           f"before submitting.", step=5)

    # ---- Rule 4: exception classification must be answered ----
    def validate_group_classification(self, submission, result: ValidationResult) -> None:
        if submission.Group1Entity is None and submission.Group2Entity is None:
            result.add("groupClassification", "required",
                       "Indicate whether this entity is Group 1 or Group 2.", step=3)

    # ---- Rule 5: Yes answers require an explanation ----
    def validate_questionnaire(self, submission, result: ValidationResult) -> None:
        selected_302 = any(a.Selected and a.AttestationType == AttestationType.QUESTIONNAIRE_302
                           for a in submission.attestations)
        if not selected_302:
            return

        answered = {r.QuestionCode for r in submission.responses
                    if r.QuestionCode in QUESTION_CODES}
        for code in QUESTION_CODES - answered:
            result.add(f"question.{code}", "required",
                       "Answer Yes or No for every 302 questionnaire item.", step=4)

        for r in submission.responses:
            if r.Answer is None and r.QuestionCode in QUESTION_CODES:
                result.add(f"question.{r.QuestionCode}", "required",
                           f"'{r.QuestionText}' must be answered.", step=4)
            if r.Answer and r.RequiresExplanationWhenYes and not (r.Explanation or "").strip():
                result.add(f"question.{r.QuestionCode}.explanation", "explanation_required",
                           f"An explanation is required because '{r.QuestionText}' "
                           f"was answered Yes.", step=4)

    # ---- Rule 6: threshold exception questions ----
    def validate_exception_thresholds(self, submission, result: ValidationResult) -> None:
        by_code = {r.QuestionCode: r for r in submission.responses}

        if submission.Group2Entity:
            self._check_threshold(by_code.get(GROUP2_EXCEPTION_CODE), GROUP2_EXCEPTION_CODE,
                                  self.group2_threshold, result)
        if submission.Group1Entity:
            self._check_threshold(by_code.get(GROUP1_EXCEPTION_CODE), GROUP1_EXCEPTION_CODE,
                                  self.group1_threshold, result)

    def _check_threshold(self, response, code: str, threshold: int,
                         result: ValidationResult) -> None:
        if response is None or response.Answer is None:
            result.add(f"question.{code}", "required",
                       f"Answer the exception question for amounts over "
                       f"${threshold:,}.", step=3)
            return
        if response.Answer and not (response.Explanation or "").strip():
            result.add(f"question.{code}.explanation", "explanation_required",
                       f"Describe the exception over ${threshold:,}.", step=3)

    # ---- Legacy default: 'None noted' when nothing was reported ----
    def apply_no_exception_defaults(self, submission) -> None:
        for r in submission.responses:
            if r.Answer is False and not (r.Explanation or "").strip():
                r.Explanation = self.no_exception_text
        for a in submission.attestations:
            if a.Selected and not (a.ExceptionText or "").strip():
                a.ExceptionText = self.no_exception_text

    # ---- Entry points ----
    def validate_for_submit(self, submission) -> ValidationResult:
        result = ValidationResult()
        self.validate_header(submission, result)
        self.validate_attestation_selection(submission, result)
        self.validate_group_classification(submission, result)
        self.validate_exception_thresholds(submission, result)
        self.validate_questionnaire(submission, result)
        self.validate_acknowledgements(submission, result)
        return result

    def validate_for_draft(self, submission) -> ValidationResult:
        """Drafts save freely; only structural integrity is enforced."""
        result = ValidationResult()
        if not submission.PeriodId:
            result.add("PeriodId", "required", "Certification quarter is required.", step=1)
        return result
