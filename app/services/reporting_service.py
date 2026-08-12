"""ReportingService -- reviewer dashboard queries and audit-ready Excel export."""
import io
from datetime import date
from openpyxl import Workbook
from sqlalchemy import select, func
from ..extensions import db
from ..models import Submission, EntityMaster, CertificationPeriod, Attachment
from ..constants import SubmissionStatus, AuditAction
from .submission_service import SubmissionService
from .audit_service import AuditService

FILTERABLE = ("period_id", "entity_id", "region", "business_unit", "location",
              "status", "preparer_role", "has_exception", "has_attachment")

EXPORT_COLUMNS = [
    ("Quarter", lambda s: s.period.QuarterLabel if s.period else None),
    ("Entity", lambda s: s.entity.Title if s.entity else None),
    ("Entity Number", lambda s: s.entity.EntityNumber if s.entity else None),
    ("Employee", lambda s: s.EmployeeName),
    ("UPN", lambda s: s.EmployeeUserPrincipalName),
    ("Region", lambda s: s.Region),
    ("Business Segment", lambda s: s.BusinessSegment),
    ("Business Unit", lambda s: s.BusinessUnit),
    ("Location", lambda s: s.Location),
    ("Preparer Role", lambda s: s.PreparerRole),
    ("Group 1", lambda s: s.Group1Entity),
    ("Group 2", lambda s: s.Group2Entity),
    ("Status", lambda s: s.Status),
    ("Submitted (UTC)", lambda s: s.SubmittedUtc),
    ("Exception Present", lambda s: s.has_exception),
    ("Attachments", lambda s: len([a for a in s.attachments if not a.IsDeleted])),
    ("Legacy XML File", lambda s: s.LegacyXmlFileName),
]


class ReportingService:
    @staticmethod
    def search(current_user, filters: dict, page: int = 1, page_size: int = 50):
        stmt = SubmissionService.scoped_query(current_user)

        if filters.get("period_id"):
            stmt = stmt.where(Submission.PeriodId == filters["period_id"])
        if filters.get("entity_id"):
            stmt = stmt.where(Submission.EntityId == filters["entity_id"])
        if filters.get("region"):
            stmt = stmt.where(Submission.Region == filters["region"])
        if filters.get("business_unit"):
            stmt = stmt.where(Submission.BusinessUnit == filters["business_unit"])
        if filters.get("location"):
            stmt = stmt.where(Submission.Location == filters["location"])
        if filters.get("status"):
            stmt = stmt.where(Submission.Status == filters["status"])
        if filters.get("preparer_role"):
            stmt = stmt.where(Submission.PreparerRole == filters["preparer_role"])

        total = db.session.scalar(
            select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.session.scalars(
            stmt.order_by(Submission.SubmittedUtc.desc().nullslast())
            .offset((page - 1) * page_size).limit(page_size)).all()
        return {"total": total, "page": page, "pageSize": page_size, "items": rows}

    @staticmethod
    def status_summary(current_user, period_id: int) -> dict:
        stmt = SubmissionService.scoped_query(current_user).where(
            Submission.PeriodId == period_id)
        rows = db.session.scalars(stmt).all()
        counts = {s.value: 0 for s in SubmissionStatus}
        for r in rows:
            counts[r.Status] = counts.get(r.Status, 0) + 1
        return {"periodId": period_id, "total": len(rows), "byStatus": counts}

    @staticmethod
    def export_xlsx(current_user, filters: dict, actor_upn: str) -> bytes:
        result = ReportingService.search(current_user, filters, page=1, page_size=100000)
        wb = Workbook()
        ws = wb.active
        ws.title = "Submissions"
        ws.append([label for label, _ in EXPORT_COLUMNS])
        for submission in result["items"]:
            ws.append([getter(submission) for _, getter in EXPORT_COLUMNS])
        ws.freeze_panes = "A2"

        buffer = io.BytesIO()
        wb.save(buffer)

        AuditService.record("Report", "SubmissionExport", AuditAction.EXPORT,
                            actor=actor_upn,
                            details={"filters": filters, "rowCount": result["total"]})
        return buffer.getvalue()
