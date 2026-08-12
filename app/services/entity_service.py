"""EntityService and PeriodService -- admin master data operations."""
from sqlalchemy import select
from ..extensions import db
from ..models import EntityMaster, CertificationPeriod, ReferenceDocument
from ..constants import AuditAction
from .audit_service import AuditService, snapshot

ENTITY_FIELDS = ["Title", "EntityNumber", "PullName", "SubmitName", "SubmittedCode",
                 "Region", "BusinessSegment", "BusinessUnit", "Location",
                 "IsGroup1", "IsGroup2", "IsActive"]
PERIOD_FIELDS = ["QuarterLabel", "FiscalYear", "QuarterNumber", "StartDate",
                 "DueDate", "IsOpen", "Enable404", "IsArchived"]


class EntityService:
    @staticmethod
    def list_active():
        return list(db.session.scalars(
            select(EntityMaster).where(EntityMaster.IsActive.is_(True))
            .order_by(EntityMaster.Title)))

    @staticmethod
    def create(data: dict, actor_upn: str) -> EntityMaster:
        entity = EntityMaster(**{k: v for k, v in data.items() if k in ENTITY_FIELDS})
        entity.CreatedBy = actor_upn
        db.session.add(entity)
        db.session.commit()
        AuditService.record("EntityMaster", entity.EntityId, AuditAction.ADMIN_CHANGE,
                            actor=actor_upn, after=snapshot(entity, ENTITY_FIELDS))
        return entity

    @staticmethod
    def update(entity: EntityMaster, data: dict, actor_upn: str) -> EntityMaster:
        before = snapshot(entity, ENTITY_FIELDS)
        for k, v in data.items():
            if k in ENTITY_FIELDS:
                setattr(entity, k, v)
        entity.ModifiedBy = actor_upn
        db.session.commit()
        AuditService.record("EntityMaster", entity.EntityId, AuditAction.ADMIN_CHANGE,
                            actor=actor_upn, before=before,
                            after=snapshot(entity, ENTITY_FIELDS))
        return entity


class PeriodService:
    @staticmethod
    def open_periods():
        return list(db.session.scalars(
            select(CertificationPeriod).where(CertificationPeriod.IsOpen.is_(True))
            .order_by(CertificationPeriod.DueDate)))

    @staticmethod
    def create(data: dict, actor_upn: str) -> CertificationPeriod:
        period = CertificationPeriod(**{k: v for k, v in data.items() if k in PERIOD_FIELDS})
        period.CreatedBy = actor_upn
        db.session.add(period)
        db.session.commit()
        AuditService.record("CertificationPeriod", period.PeriodId,
                            AuditAction.ADMIN_CHANGE, actor=actor_upn,
                            after=snapshot(period, PERIOD_FIELDS))
        return period

    @staticmethod
    def update(period: CertificationPeriod, data: dict, actor_upn: str) -> CertificationPeriod:
        before = snapshot(period, PERIOD_FIELDS)
        for k, v in data.items():
            if k in PERIOD_FIELDS:
                setattr(period, k, v)
        period.ModifiedBy = actor_upn
        db.session.commit()
        AuditService.record("CertificationPeriod", period.PeriodId,
                            AuditAction.ADMIN_CHANGE, actor=actor_upn, before=before,
                            after=snapshot(period, PERIOD_FIELDS))
        return period
