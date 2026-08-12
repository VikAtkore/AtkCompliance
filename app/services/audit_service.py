"""Immutable audit writes. Every state change routes through here."""
import json
import uuid
from flask import g, has_request_context, request
from ..extensions import db
from ..models import AuditLog
from ..models.base import utcnow

_REDACTED_FIELDS = {"ENTRA_CLIENT_SECRET", "ACC_SECRET_KEY", "password", "secret"}


def _serialize(obj) -> str | None:
    if obj is None:
        return None
    if isinstance(obj, str):
        return obj
    safe = {k: ("***" if k in _REDACTED_FIELDS else v) for k, v in dict(obj).items()}
    return json.dumps(safe, default=str, sort_keys=True)


def snapshot(model, fields: list[str]) -> dict:
    return {f: getattr(model, f, None) for f in fields}


class AuditService:
    @staticmethod
    def record(entity_name: str, entity_key: str, action: str, actor: str | None = None,
               before=None, after=None, details=None, commit: bool = True) -> AuditLog:
        current = getattr(g, "current_user", None) if has_request_context() else None
        entry = AuditLog(
            EntityName=entity_name,
            EntityKey=str(entity_key),
            Action=str(action),
            Actor=actor or (current.upn if current else "system"),
            ActorRoles=",".join(sorted(current.roles)) if current else None,
            EventUtc=utcnow(),
            IpAddress=request.remote_addr if has_request_context() else None,
            CorrelationId=getattr(g, "correlation_id", None) if has_request_context()
            else str(uuid.uuid4()),
            BeforeJson=_serialize(before),
            AfterJson=_serialize(after),
            DetailsJson=_serialize(details),
        )
        db.session.add(entry)
        if commit:
            db.session.commit()
        return entry
