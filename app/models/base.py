from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db

# SQL Server uses BIGINT IDENTITY; SQLite only auto-increments INTEGER PRIMARY KEY.
# This variant keeps local development on SQLite working without changing prod DDL.
BigIntPK = BigInteger().with_variant(Integer, "sqlite")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    CreatedUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    CreatedBy: Mapped[str | None] = mapped_column(String(255))
    ModifiedUtc: Mapped[datetime | None] = mapped_column(DateTime, onupdate=utcnow)
    ModifiedBy: Mapped[str | None] = mapped_column(String(255))
