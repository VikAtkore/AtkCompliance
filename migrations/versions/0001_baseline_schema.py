"""Baseline schema for the Atkore Compliance Certification Portal.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ---- Master data ----
    op.create_table(
        "EntityMaster",
        sa.Column("EntityId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("Title", sa.String(255), nullable=False),
        sa.Column("EntityNumber", sa.String(50)),
        sa.Column("PullName", sa.String(255)),
        sa.Column("SubmitName", sa.String(255)),
        sa.Column("SubmittedCode", sa.String(50)),
        sa.Column("Region", sa.String(255)),
        sa.Column("BusinessSegment", sa.String(255)),
        sa.Column("BusinessUnit", sa.String(255)),
        sa.Column("Location", sa.String(255)),
        sa.Column("IsGroup1", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("IsGroup2", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("LegacyListItemId", sa.Integer),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )
    op.create_index("IX_EntityMaster_Number", "EntityMaster", ["EntityNumber"])
    op.create_index("IX_EntityMaster_Active", "EntityMaster", ["IsActive"])

    op.create_table(
        "CertificationPeriod",
        sa.Column("PeriodId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("QuarterLabel", sa.String(50), nullable=False),
        sa.Column("FiscalYear", sa.Integer),
        sa.Column("QuarterNumber", sa.Integer),
        sa.Column("StartDate", sa.Date),
        sa.Column("DueDate", sa.Date),
        sa.Column("IsOpen", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("Enable404", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("IsArchived", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
        sa.UniqueConstraint("FiscalYear", "QuarterNumber", name="UQ_Period_Year_Quarter"),
    )

    op.create_table(
        "ReferenceDocument",
        sa.Column("ReferenceDocumentId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("PeriodId", sa.Integer, sa.ForeignKey("CertificationPeriod.PeriodId")),
        sa.Column("AttestationType", sa.String(100), nullable=False),
        sa.Column("Title", sa.String(255), nullable=False),
        sa.Column("StorageUrl", sa.String(1024), nullable=False),
        sa.Column("GraphItemId", sa.String(255)),
        sa.Column("DisplayOrder", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )

    # ---- Identity ----
    op.create_table(
        "AppUser",
        sa.Column("UserId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ObjectId", sa.String(64), unique=True),
        sa.Column("UserPrincipalName", sa.String(255), nullable=False, unique=True),
        sa.Column("DisplayName", sa.String(255), nullable=False),
        sa.Column("Email", sa.String(255)),
        sa.Column("Department", sa.String(255)),
        sa.Column("JobTitle", sa.String(255)),
        sa.Column("ManagerUpn", sa.String(255)),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("LastLoginUtc", sa.DateTime),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )

    op.create_table(
        "Role",
        sa.Column("RoleId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("RoleName", sa.String(50), nullable=False, unique=True),
        sa.Column("Description", sa.String(500)),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )

    op.create_table(
        "UserRole",
        sa.Column("UserRoleId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("UserId", sa.Integer, sa.ForeignKey("AppUser.UserId"), nullable=False),
        sa.Column("RoleId", sa.Integer, sa.ForeignKey("Role.RoleId"), nullable=False),
        sa.Column("ScopeRegion", sa.String(255)),
        sa.Column("ScopeBusinessUnit", sa.String(255)),
        sa.Column("ScopeEntityId", sa.Integer, sa.ForeignKey("EntityMaster.EntityId")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("GrantedBy", sa.String(255)),
        sa.Column("GrantedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
        sa.UniqueConstraint("UserId", "RoleId", "ScopeRegion", "ScopeBusinessUnit",
                            "ScopeEntityId", name="UQ_UserRole_Scope"),
    )
    op.create_index("IX_UserRole_User", "UserRole", ["UserId", "IsActive"])

    # ---- Submission core ----
    op.create_table(
        "Submission",
        sa.Column("SubmissionId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("PeriodId", sa.Integer, sa.ForeignKey("CertificationPeriod.PeriodId"),
                  nullable=False),
        sa.Column("EntityId", sa.Integer, sa.ForeignKey("EntityMaster.EntityId")),
        sa.Column("EmployeeName", sa.String(255), nullable=False),
        sa.Column("EmployeeUserPrincipalName", sa.String(255)),
        sa.Column("Region", sa.String(255)),
        sa.Column("BusinessSegment", sa.String(255)),
        sa.Column("BusinessUnit", sa.String(255)),
        sa.Column("Location", sa.String(255)),
        sa.Column("PreparerRole", sa.String(255), nullable=False),
        sa.Column("Group1Entity", sa.Boolean),
        sa.Column("Group2Entity", sa.Boolean),
        sa.Column("ExceptionAmount", sa.Numeric(18, 2)),
        sa.Column("Status", sa.String(50), nullable=False, server_default="Draft"),
        sa.Column("ReviewerComment", sa.Text),
        sa.Column("ReviewedBy", sa.String(255)),
        sa.Column("ReviewedUtc", sa.DateTime),
        sa.Column("LegacyXmlFileName", sa.String(512)),
        sa.Column("LegacyXmlPath", sa.String(1024)),
        sa.Column("LegacySourceLibrary", sa.String(255)),
        sa.Column("SubmittedUtc", sa.DateTime),
        sa.Column("ArchivedUtc", sa.DateTime),
        sa.Column("RowVersion", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )
    op.create_index("IX_Submission_Period_Status", "Submission", ["PeriodId", "Status"])
    op.create_index("IX_Submission_Entity", "Submission", ["EntityId"])
    op.create_index("IX_Submission_Upn", "Submission", ["EmployeeUserPrincipalName"])

    op.create_table(
        "SubmissionRepresentative",
        sa.Column("RepresentativeId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("SubmissionId", sa.BigInteger, sa.ForeignKey("Submission.SubmissionId"),
                  nullable=False),
        sa.Column("RepresentativeName", sa.String(255), nullable=False),
        sa.Column("RepresentativeTitle", sa.String(255)),
        sa.Column("DisplayOrder", sa.Integer, nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "QuestionnaireResponse",
        sa.Column("ResponseId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("SubmissionId", sa.BigInteger, sa.ForeignKey("Submission.SubmissionId"),
                  nullable=False),
        sa.Column("QuestionCode", sa.String(100), nullable=False),
        sa.Column("QuestionText", sa.String(500), nullable=False),
        sa.Column("Answer", sa.Boolean),
        sa.Column("Explanation", sa.Text),
        sa.Column("RequiresExplanationWhenYes", sa.Boolean, nullable=False,
                  server_default=sa.text("1")),
        sa.Column("DisplayOrder", sa.Integer, nullable=False, server_default=sa.text("0")),
    )
    op.create_index("IX_Questionnaire_Submission", "QuestionnaireResponse", ["SubmissionId"])

    op.create_table(
        "Attestation",
        sa.Column("AttestationId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("SubmissionId", sa.BigInteger, sa.ForeignKey("Submission.SubmissionId"),
                  nullable=False),
        sa.Column("AttestationType", sa.String(100), nullable=False),
        sa.Column("Selected", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("Acknowledged", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("AcknowledgedBy", sa.String(255)),
        sa.Column("AcknowledgedUtc", sa.DateTime),
        sa.Column("ReferenceDocumentUrl", sa.String(1024)),
        sa.Column("ExceptionText", sa.Text),
    )
    op.create_index("IX_Attestation_Submission_Type", "Attestation",
                    ["SubmissionId", "AttestationType"])

    op.create_table(
        "Attachment",
        sa.Column("AttachmentId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("SubmissionId", sa.BigInteger, sa.ForeignKey("Submission.SubmissionId"),
                  nullable=False),
        sa.Column("AttestationId", sa.BigInteger, sa.ForeignKey("Attestation.AttestationId")),
        sa.Column("FieldCode", sa.String(100)),
        sa.Column("OriginalFileName", sa.String(512), nullable=False),
        sa.Column("ContentType", sa.String(255)),
        sa.Column("GraphDriveId", sa.String(255)),
        sa.Column("GraphItemId", sa.String(255)),
        sa.Column("StorageUrl", sa.String(1024), nullable=False),
        sa.Column("FileSizeBytes", sa.BigInteger),
        sa.Column("Sha256", sa.String(64)),
        sa.Column("UploadedBy", sa.String(255)),
        sa.Column("UploadedUtc", sa.DateTime),
        sa.Column("IsDeleted", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("LegacyBase64FieldName", sa.String(255)),
    )
    op.create_index("IX_Attachment_Submission", "Attachment", ["SubmissionId"])

    # ---- Reminders ----
    op.create_table(
        "ReminderTemplate",
        sa.Column("TemplateId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("Name", sa.String(255), nullable=False),
        sa.Column("Subject", sa.String(500), nullable=False),
        sa.Column("BodyHtml", sa.Text, nullable=False),
        sa.Column("TargetAudience", sa.String(100)),
        sa.Column("CertificationType", sa.String(100)),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )

    op.create_table(
        "ReminderMilestone",
        sa.Column("ReminderMilestoneId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("PeriodId", sa.Integer, sa.ForeignKey("CertificationPeriod.PeriodId")),
        sa.Column("Title", sa.String(255), nullable=False),
        sa.Column("ReminderDate", sa.DateTime),
        sa.Column("OffsetDaysFromDue", sa.Integer),
        sa.Column("ReminderLevel", sa.String(50)),
        sa.Column("TemplateId", sa.Integer, sa.ForeignKey("ReminderTemplate.TemplateId")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
        sa.Column("LegacyListItemId", sa.Integer),
        sa.Column("CreatedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("CreatedBy", sa.String(255)),
        sa.Column("ModifiedUtc", sa.DateTime),
        sa.Column("ModifiedBy", sa.String(255)),
    )

    op.create_table(
        "ReminderRecipient",
        sa.Column("ReminderRecipientId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("ReminderMilestoneId", sa.Integer,
                  sa.ForeignKey("ReminderMilestone.ReminderMilestoneId"), nullable=False),
        sa.Column("EntityId", sa.Integer, sa.ForeignKey("EntityMaster.EntityId")),
        sa.Column("RoleName", sa.String(50)),
        sa.Column("UserPrincipalName", sa.String(255)),
        sa.Column("Email", sa.String(255)),
        sa.Column("EscalationLevel", sa.Integer, nullable=False, server_default=sa.text("1")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )

    op.create_table(
        "ReminderRunLog",
        sa.Column("RunLogId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("ReminderMilestoneId", sa.Integer,
                  sa.ForeignKey("ReminderMilestone.ReminderMilestoneId")),
        sa.Column("RunUtc", sa.DateTime, nullable=False),
        sa.Column("RecipientEmail", sa.String(255)),
        sa.Column("SubmissionId", sa.BigInteger, sa.ForeignKey("Submission.SubmissionId")),
        sa.Column("Status", sa.String(50), nullable=False),
        sa.Column("ErrorMessage", sa.Text),
    )
    op.create_index("IX_ReminderRunLog_Run", "ReminderRunLog", ["RunUtc"])

    # ---- Audit ----
    op.create_table(
        "AuditLog",
        sa.Column("AuditLogId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("EntityName", sa.String(100), nullable=False),
        sa.Column("EntityKey", sa.String(100), nullable=False),
        sa.Column("Action", sa.String(100), nullable=False),
        sa.Column("Actor", sa.String(255), nullable=False),
        sa.Column("ActorRoles", sa.String(255)),
        sa.Column("EventUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
        sa.Column("IpAddress", sa.String(64)),
        sa.Column("CorrelationId", sa.String(64)),
        sa.Column("BeforeJson", sa.Text),
        sa.Column("AfterJson", sa.Text),
        sa.Column("DetailsJson", sa.Text),
    )
    op.create_index("IX_AuditLog_Entity", "AuditLog",
                    ["EntityName", "EntityKey", "EventUtc"])

    # ---- Migration staging ----
    op.create_table(
        "LegacyXmlSubmissionStage",
        sa.Column("StageId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("SourceLibrary", sa.String(255)),
        sa.Column("SourceFileName", sa.String(512), nullable=False),
        sa.Column("SourcePath", sa.String(1024)),
        sa.Column("RawXml", sa.Text),
        sa.Column("ParseStatus", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("ParseError", sa.Text),
        sa.Column("MappedSubmissionId", sa.BigInteger),
        sa.Column("ImportedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
    )

    op.create_table(
        "LegacyVlookupStage",
        sa.Column("StageId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("Title", sa.String(255)),
        sa.Column("EntityNumber", sa.String(50)),
        sa.Column("PullName", sa.String(255)),
        sa.Column("SubmitName", sa.String(255)),
        sa.Column("SubmittedCode", sa.String(50)),
        sa.Column("LegacyListItemId", sa.Integer),
        sa.Column("MergeStatus", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("MergedEntityId", sa.Integer),
        sa.Column("ImportedUtc", sa.DateTime, nullable=False,
                  server_default=sa.text("SYSUTCDATETIME()")),
    )

    op.create_table(
        "LegacyAttachmentStage",
        sa.Column("StageId", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("XmlStageId", sa.BigInteger),
        sa.Column("FieldName", sa.String(255)),
        sa.Column("DecodedFileName", sa.String(512)),
        sa.Column("FileSizeBytes", sa.BigInteger),
        sa.Column("Sha256", sa.String(64)),
        sa.Column("ExtractStatus", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("ExtractError", sa.Text),
        sa.Column("GraphItemId", sa.String(255)),
        sa.Column("StorageUrl", sa.String(1024)),
        sa.Column("MappedAttachmentId", sa.BigInteger),
    )

    op.create_table(
        "LegacyReminderStage",
        sa.Column("StageId", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("Title", sa.String(255)),
        sa.Column("ReminderDate", sa.DateTime),
        sa.Column("LegacyListItemId", sa.Integer),
        sa.Column("MapStatus", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("MappedMilestoneId", sa.Integer),
        sa.Column("IsReviewed", sa.Boolean, nullable=False, server_default=sa.text("0")),
    )


def downgrade():
    for table in ("LegacyReminderStage", "LegacyAttachmentStage", "LegacyVlookupStage",
                  "LegacyXmlSubmissionStage", "AuditLog", "ReminderRunLog",
                  "ReminderRecipient", "ReminderMilestone", "ReminderTemplate",
                  "Attachment", "Attestation", "QuestionnaireResponse",
                  "SubmissionRepresentative", "Submission", "UserRole", "Role",
                  "AppUser", "ReferenceDocument", "CertificationPeriod", "EntityMaster"):
        op.drop_table(table)
