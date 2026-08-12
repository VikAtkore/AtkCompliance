from datetime import datetime, timezone
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    CreatedUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    CreatedBy: Mapped[str | None] = mapped_column(String(255))
    ModifiedUtc: Mapped[datetime | None] = mapped_column(DateTime, onupdate=utcnow)
    ModifiedBy: Mapped[str | None] = mapped_column(String(255))
