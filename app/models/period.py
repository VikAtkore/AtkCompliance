"""CertificationPeriod -- replaces the per-quarter InfoPath form library."""
from datetime import date
from sqlalchemy import String, Boolean, Integer, Date, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from .base import TimestampMixin


class CertificationPeriod(db.Model, TimestampMixin):
    __tablename__ = "CertificationPeriod"
    __table_args__ = (UniqueConstraint("FiscalYear", "QuarterNumber", name="UQ_Period_Year_Quarter"),)

    PeriodId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    QuarterLabel: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. "Q1 2026"
    FiscalYear: Mapped[int | None] = mapped_column(Integer)
    QuarterNumber: Mapped[int | None] = mapped_column(Integer)
    StartDate: Mapped[date | None] = mapped_column(Date)
    DueDate: Mapped[date | None] = mapped_column(Date)
    IsOpen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Q4 / annual cycles enable the 404 Certification module.
    Enable404: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    IsArchived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="period")
    reference_documents: Mapped[list["ReferenceDocument"]] = relationship(back_populates="period")
    milestones: Mapped[list["ReminderMilestone"]] = relationship(back_populates="period")


class ReferenceDocument(db.Model, TimestampMixin):
    """Per-quarter acknowledgement documents, stored in SharePoint Online."""
    __tablename__ = "ReferenceDocument"

    ReferenceDocumentId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    PeriodId: Mapped[int | None] = mapped_column(ForeignKey("CertificationPeriod.PeriodId"))
    AttestationType: Mapped[str] = mapped_column(String(100), nullable=False)
    Title: Mapped[str] = mapped_column(String(255), nullable=False)
    StorageUrl: Mapped[str] = mapped_column(String(1024), nullable=False)
    GraphItemId: Mapped[str | None] = mapped_column(String(255))
    DisplayOrder: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    period: Mapped["CertificationPeriod"] = relationship(back_populates="reference_documents")
