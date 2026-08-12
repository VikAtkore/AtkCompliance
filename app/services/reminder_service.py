"""ReminderService -- evaluates milestones, finds missing submissions, notifies.

Recipients and templates are configuration, not code: the legacy SharePoint
workflow never exposed its notification logic, so nothing here is assumed.
"""
import logging
from datetime import date, timedelta
from sqlalchemy import select
from ..extensions import db
from ..models import (ReminderMilestone, ReminderRecipient, ReminderRunLog,
                      CertificationPeriod, EntityMaster, Submission, AppUser)
from ..constants import SubmissionStatus, AuditAction, ReminderLevel
from ..models.base import utcnow
from .audit_service import AuditService
from .graph_client import GraphClient, GraphError

log = logging.getLogger(__name__)


class ReminderService:
    def __init__(self, config: dict, graph: GraphClient | None = None):
        self.config = config
        self.dry_run = config.get("REMINDER_DRY_RUN", True)
        self.sender = config.get("MAIL_SENDER_UPN")
        self._graph = graph

    @property
    def graph(self) -> GraphClient:
        if self._graph is None:
            self._graph = GraphClient(
                tenant_id=self.config["ENTRA_TENANT_ID"],
                client_id=self.config["ENTRA_CLIENT_ID"],
                client_secret=self.config["ENTRA_CLIENT_SECRET"],
                base_url=self.config["GRAPH_BASE_URL"],
            )
        return self._graph

    # ---- Milestone evaluation ----
    def due_milestones(self, as_of: date | None = None) -> list[ReminderMilestone]:
        as_of = as_of or date.today()
        milestones = db.session.scalars(
            select(ReminderMilestone).where(ReminderMilestone.IsActive.is_(True))
        ).all()

        due = []
        for m in milestones:
            target = self._effective_date(m)
            if target and target == as_of:
                due.append(m)
        return due

    @staticmethod
    def _effective_date(milestone: ReminderMilestone) -> date | None:
        if milestone.ReminderDate:
            return milestone.ReminderDate.date()
        if milestone.OffsetDaysFromDue is not None and milestone.period \
                and milestone.period.DueDate:
            return milestone.period.DueDate + timedelta(days=milestone.OffsetDaysFromDue)
        return None

    # ---- Gap analysis ----
    @staticmethod
    def missing_submissions(period_id: int) -> list[EntityMaster]:
        submitted_entity_ids = set(db.session.scalars(
            select(Submission.EntityId).where(
                Submission.PeriodId == period_id,
                Submission.Status != SubmissionStatus.DRAFT)
        ).all())
        entities = db.session.scalars(
            select(EntityMaster).where(EntityMaster.IsActive.is_(True))).all()
        return [e for e in entities if e.EntityId not in submitted_entity_ids]

    # ---- Execution ----
    def run(self, as_of: date | None = None) -> dict:
        summary = {"milestones": 0, "sent": 0, "skipped": 0, "failed": 0,
                   "dryRun": self.dry_run}
        for milestone in self.due_milestones(as_of):
            summary["milestones"] += 1
            for recipient in milestone.recipients:
                if not recipient.IsActive:
                    summary["skipped"] += 1
                    continue
                address = recipient.Email or recipient.UserPrincipalName
                if not address:
                    self._log_run(milestone, None, "Skipped", "No resolvable address.")
                    summary["skipped"] += 1
                    continue
                try:
                    if self.dry_run:
                        self._log_run(milestone, address, "Skipped", "Dry-run mode.")
                        summary["skipped"] += 1
                    else:
                        self._send(milestone, address)
                        self._log_run(milestone, address, "Sent", None)
                        summary["sent"] += 1
                except GraphError as exc:
                    self._log_run(milestone, address, "Failed", str(exc))
                    summary["failed"] += 1
        db.session.commit()
        AuditService.record("ReminderRun", str(as_of or date.today()),
                            AuditAction.REMINDER_SENT, details=summary)
        return summary

    def _send(self, milestone: ReminderMilestone, address: str) -> None:
        template = milestone.template
        subject = template.Subject if template else milestone.Title
        body = template.BodyHtml if template else (
            f"<p>Reminder: {milestone.Title}</p>")
        self.graph.request(
            "POST", f"/users/{self.sender}/sendMail",
            json={"message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [{"emailAddress": {"address": address}}],
            }, "saveToSentItems": True},
        )

    def _log_run(self, milestone, address, status, error) -> None:
        db.session.add(ReminderRunLog(
            ReminderMilestoneId=milestone.ReminderMilestoneId, RunUtc=utcnow(),
            RecipientEmail=address, Status=status, ErrorMessage=error))
