"""Submission, QuestionnaireResponse, Attestation, Attachment."""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (String, Boolean, Integer, BigInteger, DateTime, Numeric,
                        ForeignKey, Index, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from ..constants import SubmissionStatus
from .base import TimestampMixin


class Submission(db.Model, TimestampMixin):
    __tablename__ = "Submission"
    __table_args__ = (
        Index("IX_Submission_Period_Status", "PeriodId", "Status"),
        Index("IX_Submission_Entity", "EntityId"),
        Index("IX_Submission_Upn", "EmployeeUserPrincipalName"),
    )

    SubmissionId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    PeriodId: Mapped[int] = mapped_column(ForeignKey("CertificationPeriod.PeriodId"), nullable=False)
    EntityId: Mapped[int | None] = mapped_column(ForeignKey("EntityMaster.EntityId"))

    # Identity / context block (legacy header fields)
    EmployeeName: Mapped[str] = mapped_column(String(255), nullable=False)          # Yourname
    EmployeeUserPrincipalName: Mapped[str | None] = mapped_column(String(255))
    Region: Mapped[str | None] = mapped_column(String(255))                          # region
    BusinessSegment: Mapped[str | None] = mapped_column(String(255))                 # businesssgement
    BusinessUnit: Mapped[str | None] = mapped_column(String(255))                    # BusinessUnit
    Location: Mapped[str | None] = mapped_column(String(255))                        # location
    PreparerRole: Mapped[str] = mapped_column(String(255), nullable=False)           # preparersrole

    # Exception classification
    Group1Entity: Mapped[bool | None] = mapped_column(Boolean)
    Group2Entity: Mapped[bool | None] = mapped_column(Boolean)
    ExceptionAmount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))

    Status: Mapped[str] = mapped_column(String(50), default=SubmissionStatus.DRAFT, nullable=False)
    ReviewerComment: Mapped[str | None] = mapped_column(Text)
    ReviewedBy: Mapped[str | None] = mapped_column(String(255))
    ReviewedUtc: Mapped[datetime | None] = mapped_column(DateTime)

    # Legacy traceability -- preserved so every migrated row maps to source XML
    LegacyXmlFileName: Mapped[str | None] = mapped_column(String(512))
    LegacyXmlPath: Mapped[str | None] = mapped_column(String(1024))
    LegacySourceLibrary: Mapped[str | None] = mapped_column(String(255))

    SubmittedUtc: Mapped[datetime | None] = mapped_column(DateTime)
    ArchivedUtc: Mapped[datetime | None] = mapped_column(DateTime)
    RowVersion: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    period: Mapped["CertificationPeriod"] = relationship(back_populates="submissions")
    entity: Mapped["EntityMaster"] = relationship(back_populates="submissions")
    responses: Mapped[list["QuestionnaireResponse"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan")
    attestations: Mapped[list["Attestation"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan")
    representatives: Mapped[list["SubmissionRepresentative"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan")

    @property
    def is_editable(self) -> bool:
        return self.Status in (SubmissionStatus.DRAFT, SubmissionStatus.RETURNED)

    @property
    def has_exception(self) -> bool:
        return any(r.Answer for r in self.responses) or any(
            a.ExceptionText and a.ExceptionText.strip().lower() != "none noted"
            for a in self.attestations)


class SubmissionRepresentative(db.Model):
    """Legacy Rep_Names repeating field, normalized."""
    __tablename__ = "SubmissionRepresentative"

    RepresentativeId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SubmissionId: Mapped[int] = mapped_column(ForeignKey("Submission.SubmissionId"), nullable=False)
    RepresentativeName: Mapped[str] = mapped_column(String(255), nullable=False)
    RepresentativeTitle: Mapped[str | None] = mapped_column(String(255))
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    submission: Mapped[Submission] = relationship(back_populates="representatives")


class QuestionnaireResponse(db.Model):
    __tablename__ = "QuestionnaireResponse"
    __table_args__ = (Index("IX_Questionnaire_Submission", "SubmissionId"),)

    ResponseId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SubmissionId: Mapped[int] = mapped_column(ForeignKey("Submission.SubmissionId"), nullable=False)
    QuestionCode: Mapped[str] = mapped_column(String(100), nullable=False)
    QuestionText: Mapped[str] = mapped_column(String(500), nullable=False)
    Answer: Mapped[bool | None] = mapped_column(Boolean)
    Explanation: Mapped[str | None] = mapped_column(Text)
    RequiresExplanationWhenYes: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    submission: Mapped[Submission] = relationship(back_populates="responses")


class Attestation(db.Model):
    __tablename__ = "Attestation"
    __table_args__ = (Index("IX_Attestation_Submission_Type", "SubmissionId", "AttestationType"),)

    AttestationId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SubmissionId: Mapped[int] = mapped_column(ForeignKey("Submission.SubmissionId"), nullable=False)
    AttestationType: Mapped[str] = mapped_column(String(100), nullable=False)
    Selected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    Acknowledged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    AcknowledgedBy: Mapped[str | None] = mapped_column(String(255))
    AcknowledgedUtc: Mapped[datetime | None] = mapped_column(DateTime)
    ReferenceDocumentUrl: Mapped[str | None] = mapped_column(String(1024))
    ExceptionText: Mapped[str | None] = mapped_column(Text)

    submission: Mapped[Submission] = relationship(back_populates="attestations")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="attestation")


class Attachment(db.Model):
    """Metadata only. Bytes live in SharePoint Online, addressed via Graph."""
    __tablename__ = "Attachment"
    __table_args__ = (Index("IX_Attachment_Submission", "SubmissionId"),)

    AttachmentId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SubmissionId: Mapped[int] = mapped_column(ForeignKey("Submission.SubmissionId"), nullable=False)
    AttestationId: Mapped[int | None] = mapped_column(ForeignKey("Attestation.AttestationId"))
    FieldCode: Mapped[str | None] = mapped_column(String(100))
    OriginalFileName: Mapped[str] = mapped_column(String(512), nullable=False)
    ContentType: Mapped[str | None] = mapped_column(String(255))
    # Graph addressing -- drive + item is the durable pointer; StorageUrl is display only.
    GraphDriveId: Mapped[str | None] = mapped_column(String(255))
    GraphItemId: Mapped[str | None] = mapped_column(String(255))
    StorageUrl: Mapped[str] = mapped_column(String(1024), nullable=False)
    FileSizeBytes: Mapped[int | None] = mapped_column(BigInteger)
    Sha256: Mapped[str | None] = mapped_column(String(64))
    UploadedBy: Mapped[str | None] = mapped_column(String(255))
    UploadedUtc: Mapped[datetime | None] = mapped_column(DateTime)
    IsDeleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    LegacyBase64FieldName: Mapped[str | None] = mapped_column(String(255))

    submission: Mapped[Submission] = relationship(back_populates="attachments")
    attestation: Mapped[Attestation] = relationship(back_populates="attachments")
