"""Reminder configuration.

The legacy 'Reminder Workflow' list exposed only Title and Reminder Date --
recipients, templates and escalation were not visible. This model makes all of
that explicit and administrator-configurable rather than hard-coded.
"""
from datetime import datetime
from sqlalchemy import (String, Boolean, Integer, BigInteger, DateTime, ForeignKey,
                        Index, Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from .base import TimestampMixin, BigIntPK


class ReminderMilestone(db.Model, TimestampMixin):
    __tablename__ = "ReminderMilestone"

    ReminderMilestoneId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    PeriodId: Mapped[int | None] = mapped_column(ForeignKey("CertificationPeriod.PeriodId"))
    Title: Mapped[str] = mapped_column(String(255), nullable=False)
    ReminderDate: Mapped[datetime | None] = mapped_column(DateTime)
    OffsetDaysFromDue: Mapped[int | None] = mapped_column(Integer)
    ReminderLevel: Mapped[str | None] = mapped_column(String(50))
    TemplateId: Mapped[int | None] = mapped_column(ForeignKey("ReminderTemplate.TemplateId"))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    LegacyListItemId: Mapped[int | None] = mapped_column(Integer)

    period: Mapped["CertificationPeriod"] = relationship(back_populates="milestones")
    template: Mapped["ReminderTemplate"] = relationship()
    recipients: Mapped[list["ReminderRecipient"]] = relationship(
        back_populates="milestone", cascade="all, delete-orphan")
    runs: Mapped[list["ReminderRunLog"]] = relationship(back_populates="milestone")


class ReminderRecipient(db.Model):
    __tablename__ = "ReminderRecipient"

    ReminderRecipientId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ReminderMilestoneId: Mapped[int] = mapped_column(
        ForeignKey("ReminderMilestone.ReminderMilestoneId"), nullable=False)
    EntityId: Mapped[int | None] = mapped_column(ForeignKey("EntityMaster.EntityId"))
    RoleName: Mapped[str | None] = mapped_column(String(50))
    UserPrincipalName: Mapped[str | None] = mapped_column(String(255))
    Email: Mapped[str | None] = mapped_column(String(255))
    EscalationLevel: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    milestone: Mapped[ReminderMilestone] = relationship(back_populates="recipients")


class ReminderTemplate(db.Model, TimestampMixin):
    __tablename__ = "ReminderTemplate"

    TemplateId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Name: Mapped[str] = mapped_column(String(255), nullable=False)
    Subject: Mapped[str] = mapped_column(String(500), nullable=False)
    BodyHtml: Mapped[str] = mapped_column(Text, nullable=False)
    TargetAudience: Mapped[str | None] = mapped_column(String(100))
    CertificationType: Mapped[str | None] = mapped_column(String(100))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ReminderRunLog(db.Model):
    __tablename__ = "ReminderRunLog"
    __table_args__ = (Index("IX_ReminderRunLog_Run", "RunUtc"),)

    RunLogId: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    ReminderMilestoneId: Mapped[int | None] = mapped_column(
        ForeignKey("ReminderMilestone.ReminderMilestoneId"))
    RunUtc: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    RecipientEmail: Mapped[str | None] = mapped_column(String(255))
    SubmissionId: Mapped[int | None] = mapped_column(ForeignKey("Submission.SubmissionId"))
    Status: Mapped[str] = mapped_column(String(50), nullable=False)  # Sent | Failed | Skipped
    ErrorMessage: Mapped[str | None] = mapped_column(Text)

    milestone: Mapped[ReminderMilestone] = relationship(back_populates="runs")
