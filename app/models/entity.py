"""EntityMaster -- migrated from the legacy SharePoint 'Vlookup' list."""
from sqlalchemy import String, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from .base import TimestampMixin


class EntityMaster(db.Model, TimestampMixin):
    __tablename__ = "EntityMaster"
    __table_args__ = (
        Index("IX_EntityMaster_Number", "EntityNumber"),
        Index("IX_EntityMaster_Active", "IsActive"),
    )

    EntityId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    Title: Mapped[str] = mapped_column(String(255), nullable=False)          # Vlookup: Title
    EntityNumber: Mapped[str | None] = mapped_column(String(50))             # Vlookup: Entity Number
    PullName: Mapped[str | None] = mapped_column(String(255))                # Vlookup: Pull Name
    SubmitName: Mapped[str | None] = mapped_column(String(255))              # Vlookup: Submit
    SubmittedCode: Mapped[str | None] = mapped_column(String(50))            # Vlookup: Submitted
    Region: Mapped[str | None] = mapped_column(String(255))
    BusinessSegment: Mapped[str | None] = mapped_column(String(255))
    BusinessUnit: Mapped[str | None] = mapped_column(String(255))
    Location: Mapped[str | None] = mapped_column(String(255))
    # Group classification drives which exception threshold question is shown.
    IsGroup1: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    IsGroup2: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    LegacyListItemId: Mapped[int | None] = mapped_column(Integer)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="entity")
