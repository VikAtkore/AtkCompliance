"""Permission catalogue and the role -> permission matrix.

Authorization is SQL-backed: Entra ID proves *who* the user is, the UserRole
table decides *what* they may do. Permissions are checked, never role names --
that keeps route code stable if the role model is extended later.
"""
from ..constants import RoleName


class P:
    # Submissions
    SUBMISSION_CREATE = "submission.create"
    SUBMISSION_EDIT_OWN = "submission.edit.own"
    SUBMISSION_EDIT_ANY = "submission.edit.any"
    SUBMISSION_VIEW_OWN = "submission.view.own"
    SUBMISSION_VIEW_SCOPED = "submission.view.scoped"
    SUBMISSION_VIEW_ALL = "submission.view.all"
    SUBMISSION_SUBMIT = "submission.submit"
    SUBMISSION_REOPEN = "submission.reopen"
    SUBMISSION_RETURN = "submission.return"
    SUBMISSION_ACCEPT = "submission.accept"
    SUBMISSION_ARCHIVE = "submission.archive"
    SUBMISSION_DELETE_DRAFT = "submission.delete.draft"

    # Attachments
    ATTACHMENT_UPLOAD = "attachment.upload"
    ATTACHMENT_VIEW_OWN = "attachment.view.own"
    ATTACHMENT_VIEW_SCOPED = "attachment.view.scoped"
    ATTACHMENT_DELETE = "attachment.delete"

    # Reporting
    REPORT_VIEW = "report.view"
    REPORT_EXPORT = "report.export"
    REPORT_VIEW_MISSING = "report.view.missing"

    # Administration
    PERIOD_MANAGE = "admin.period.manage"
    ENTITY_MANAGE = "admin.entity.manage"
    REFDOC_MANAGE = "admin.refdoc.manage"
    REMINDER_MANAGE = "admin.reminder.manage"
    REMINDER_RUN = "admin.reminder.run"
    ROLE_MANAGE = "admin.role.manage"
    AUDIT_VIEW = "admin.audit.view"

    # System
    MIGRATION_RUN = "system.migration.run"
    CONFIG_VIEW = "system.config.view"
    JOB_MANAGE = "system.job.manage"
    HEALTH_DETAIL = "system.health.detail"


SUBMITTER_PERMISSIONS = {
    P.SUBMISSION_CREATE, P.SUBMISSION_EDIT_OWN, P.SUBMISSION_VIEW_OWN,
    P.SUBMISSION_SUBMIT, P.SUBMISSION_DELETE_DRAFT,
    P.ATTACHMENT_UPLOAD, P.ATTACHMENT_VIEW_OWN,
}

REVIEWER_PERMISSIONS = SUBMITTER_PERMISSIONS | {
    P.SUBMISSION_VIEW_SCOPED, P.SUBMISSION_RETURN, P.SUBMISSION_ACCEPT,
    P.ATTACHMENT_VIEW_SCOPED,
    P.REPORT_VIEW, P.REPORT_EXPORT, P.REPORT_VIEW_MISSING,
}

COMPLIANCE_ADMIN_PERMISSIONS = REVIEWER_PERMISSIONS | {
    P.SUBMISSION_VIEW_ALL, P.SUBMISSION_EDIT_ANY, P.SUBMISSION_REOPEN,
    P.SUBMISSION_ARCHIVE, P.ATTACHMENT_DELETE,
    P.PERIOD_MANAGE, P.ENTITY_MANAGE, P.REFDOC_MANAGE,
    P.REMINDER_MANAGE, P.REMINDER_RUN, P.ROLE_MANAGE, P.AUDIT_VIEW,
}

SYSTEM_ADMIN_PERMISSIONS = COMPLIANCE_ADMIN_PERMISSIONS | {
    P.MIGRATION_RUN, P.CONFIG_VIEW, P.JOB_MANAGE, P.HEALTH_DETAIL,
}

ROLE_PERMISSIONS = {
    RoleName.SUBMITTER: SUBMITTER_PERMISSIONS,
    RoleName.REVIEWER: REVIEWER_PERMISSIONS,
    RoleName.COMPLIANCE_ADMIN: COMPLIANCE_ADMIN_PERMISSIONS,
    RoleName.SYSTEM_ADMIN: SYSTEM_ADMIN_PERMISSIONS,
}


def permissions_for(role_names) -> set[str]:
    granted: set[str] = set()
    for name in role_names:
        granted |= ROLE_PERMISSIONS.get(name, set())
    return granted
