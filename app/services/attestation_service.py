"""AttestationService -- which modules apply, and their reference documents."""
from sqlalchemy import select
from ..extensions import db
from ..models import Attestation, ReferenceDocument, CertificationPeriod
from ..constants import AttestationType, ATTESTATION_LABELS
from ..models.base import utcnow


class AttestationService:
    @staticmethod
    def available_types(period: CertificationPeriod) -> list[str]:
        types = [t.value for t in AttestationType]
        if not period.Enable404:
            types = [t for t in types if t != AttestationType.CERTIFICATION_404]
        return types

    @staticmethod
    def reference_documents(period_id: int, attestation_type: str) -> list[ReferenceDocument]:
        return list(db.session.scalars(
            select(ReferenceDocument)
            .where(ReferenceDocument.PeriodId == period_id,
                   ReferenceDocument.AttestationType == attestation_type,
                   ReferenceDocument.IsActive.is_(True))
            .order_by(ReferenceDocument.DisplayOrder)
        ))

    @staticmethod
    def set_selection(submission, selected_types: list[str], actor_upn: str) -> None:
        wanted = set(selected_types)
        for a in submission.attestations:
            was_selected = a.Selected
            a.Selected = a.AttestationType in wanted
            if was_selected and not a.Selected:
                a.Acknowledged = False
                a.AcknowledgedBy = None
                a.AcknowledgedUtc = None
        db.session.commit()

    @staticmethod
    def acknowledge(attestation: Attestation, actor_upn: str,
                    exception_text: str | None = None) -> Attestation:
        attestation.Acknowledged = True
        attestation.AcknowledgedBy = actor_upn
        attestation.AcknowledgedUtc = utcnow()
        if exception_text is not None:
            attestation.ExceptionText = exception_text
        db.session.commit()
        return attestation

    @staticmethod
    def label(attestation_type: str) -> str:
        return ATTESTATION_LABELS.get(attestation_type, attestation_type)
