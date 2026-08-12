"""Migration staging tables -- legacy artifacts land here before mapping."""
from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db
from .base import utcnow


class LegacyXmlSubmissionStage(db.Model):
    __tablename__ = "LegacyXmlSubmissionStage"

    StageId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    SourceLibrary: Mapped[str | None] = mapped_column(String(255))
    SourceFileName: Mapped[str] = mapped_column(String(512), nullable=False)
    SourcePath: Mapped[str | None] = mapped_column(String(1024))
    RawXml: Mapped[str | None] = mapped_column(Text)
    ParseStatus: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)
    ParseError: Mapped[str | None] = mapped_column(Text)
    MappedSubmissionId: Mapped[int | None] = mapped_column(BigInteger)
    ImportedUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class LegacyVlookupStage(db.Model):
    __tablename__ = "LegacyVlookupStage"

    StageId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Title: Mapped[str | None] = mapped_column(String(255))
    EntityNumber: Mapped[str | None] = mapped_column(String(50))
    PullName: Mapped[str | None] = mapped_column(String(255))
    SubmitName: Mapped[str | None] = mapped_column(String(255))
    SubmittedCode: Mapped[str | None] = mapped_column(String(50))
    LegacyListItemId: Mapped[int | None] = mapped_column(Integer)
    MergeStatus: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)
    MergedEntityId: Mapped[int | None] = mapped_column(Integer)
    ImportedUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class LegacyAttachmentStage(db.Model):
    __tablename__ = "LegacyAttachmentStage"

    StageId: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    XmlStageId: Mapped[int | None] = mapped_column(BigInteger)
    FieldName: Mapped[str | None] = mapped_column(String(255))
    DecodedFileName: Mapped[str | None] = mapped_column(String(512))
    FileSizeBytes: Mapped[int | None] = mapped_column(BigInteger)
    Sha256: Mapped[str | None] = mapped_column(String(64))
    ExtractStatus: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)
    ExtractError: Mapped[str | None] = mapped_column(Text)
    GraphItemId: Mapped[str | None] = mapped_column(String(255))
    StorageUrl: Mapped[str | None] = mapped_column(String(1024))
    MappedAttachmentId: Mapped[int | None] = mapped_column(BigInteger)


class LegacyReminderStage(db.Model):
    __tablename__ = "LegacyReminderStage"

    StageId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    Title: Mapped[str | None] = mapped_column(String(255))
    ReminderDate: Mapped[datetime | None] = mapped_column(DateTime)
    LegacyListItemId: Mapped[int | None] = mapped_column(Integer)
    MapStatus: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)
    MappedMilestoneId: Mapped[int | None] = mapped_column(Integer)
    IsReviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
