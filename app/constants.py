"""Domain constants derived from the legacy InfoPath solution."""
from enum import StrEnum


class SubmissionStatus(StrEnum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "UnderReview"
    RETURNED = "Returned"
    ACCEPTED = "Accepted"
    ARCHIVED = "Archived"


ALLOWED_STATUS_TRANSITIONS = {
    SubmissionStatus.DRAFT: {SubmissionStatus.SUBMITTED},
    SubmissionStatus.SUBMITTED: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.RETURNED,
                                 SubmissionStatus.ACCEPTED},
    SubmissionStatus.UNDER_REVIEW: {SubmissionStatus.RETURNED, SubmissionStatus.ACCEPTED},
    SubmissionStatus.RETURNED: {SubmissionStatus.DRAFT},
    SubmissionStatus.ACCEPTED: {SubmissionStatus.ARCHIVED},
    SubmissionStatus.ARCHIVED: set(),
}


class AttestationType(StrEnum):
    MANAGEMENT_REPRESENTATION = "ManagementRepresentation"
    QUESTIONNAIRE_302 = "Questionnaire302"
    FINANCE_CODE_OF_CONDUCT = "FinanceCodeOfConduct"
    LEGAL_REPRESENTATION = "LegalRepresentation"
    CERTIFICATION_404 = "Certification404"


ATTESTATION_LABELS = {
    AttestationType.MANAGEMENT_REPRESENTATION: "Management Representation",
    AttestationType.QUESTIONNAIRE_302: "302 Questionnaire",
    AttestationType.FINANCE_CODE_OF_CONDUCT: "Finance Code of Conduct",
    AttestationType.LEGAL_REPRESENTATION: "Legal Representation",
    AttestationType.CERTIFICATION_404: "404 Certification",
}


class RoleName(StrEnum):
    SUBMITTER = "Submitter"
    REVIEWER = "Reviewer"
    COMPLIANCE_ADMIN = "ComplianceAdmin"
    SYSTEM_ADMIN = "SystemAdmin"


class AuditAction(StrEnum):
    CREATE = "Create"
    EDIT = "Edit"
    SUBMIT = "Submit"
    REOPEN = "Reopen"
    RETURN = "Return"
    ACCEPT = "Accept"
    ARCHIVE = "Archive"
    ATTACHMENT_UPLOAD = "AttachmentUpload"
    ATTACHMENT_DELETE = "AttachmentDelete"
    EXPORT = "Export"
    ADMIN_CHANGE = "AdminChange"
    LOGIN = "Login"
    ROLE_CHANGE = "RoleChange"
    REMINDER_SENT = "ReminderSent"
    MIGRATION_IMPORT = "MigrationImport"


# The 10 legacy 302 questions. QuestionCode values are stable contract keys and
# must not change once data exists -- they are referenced by migrated XML rows.
QUESTION_CATALOG = [
    ("ORG_CHANGE", "Organizational Changes", 10),
    ("PROCESS_CHANGE", "Significant business process changes", 20),
    ("KEY_PERSONNEL_CHANGE", "Key personnel changes", 30),
    ("SYSTEM_CHANGE", "System changes", 40),
    ("EXTERNAL_AUDIT_FINDING", "External audit findings", 50),
    ("INTERNAL_AUDIT_FINDING", "Internal audit findings", 60),
    ("ACCOUNTING_ADJUSTMENTS", "Accounting adjustments", 70),
    ("FRAUD_INDICATORS", "Fraud indicators", 80),
    ("CONTROL_REMEDIATION", "Control remediation", 90),
    ("CONTROL_DEFICIENCIES", "Identification of control deficiencies", 100),
]

GROUP1_EXCEPTION_CODE = "GROUP1_EXCEPTION_250K"
GROUP2_EXCEPTION_CODE = "GROUP2_EXCEPTION_450K"


class ReminderLevel(StrEnum):
    ADVANCE = "Advance"
    DUE = "Due"
    OVERDUE = "Overdue"
    ESCALATION = "Escalation"
