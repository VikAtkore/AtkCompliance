"""Immutable audit trail. Rows are insert-only -- no update or delete path."""
from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Index, Text
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db
from .base import BigIntPK, utcnow


class AuditLog(db.Model):
    __tablename__ = "AuditLog"
    __table_args__ = (Index("IX_AuditLog_Entity", "EntityName", "EntityKey", "EventUtc"),)

    AuditLogId: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    EntityName: Mapped[str] = mapped_column(String(100), nullable=False)
    EntityKey: Mapped[str] = mapped_column(String(100), nullable=False)
    Action: Mapped[str] = mapped_column(String(100), nullable=False)
    Actor: Mapped[str] = mapped_column(String(255), nullable=False)
    ActorRoles: Mapped[str | None] = mapped_column(String(255))
    EventUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    IpAddress: Mapped[str | None] = mapped_column(String(64))
    CorrelationId: Mapped[str | None] = mapped_column(String(64))
    BeforeJson: Mapped[str | None] = mapped_column(Text)
    AfterJson: Mapped[str | None] = mapped_column(Text)
    DetailsJson: Mapped[str | None] = mapped_column(Text)
