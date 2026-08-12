"""Background job registration (APScheduler).

Only one IIS worker process should run the scheduler. Set ACC_ENABLE_SCHEDULER
on a single dedicated worker, or run these as Windows Scheduled Tasks calling
the CLI entry points in scripts/.
"""
import logging
from datetime import date
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

log = logging.getLogger(__name__)


def _cron(expression: str) -> CronTrigger:
    minute, hour, day, month, day_of_week = expression.split()
    return CronTrigger(minute=minute, hour=hour, day=day, month=month,
                       day_of_week=day_of_week, timezone="UTC")


def register_jobs(app) -> BackgroundScheduler | None:
    if not app.config.get("ENABLE_SCHEDULER"):
        log.info("Scheduler disabled for this worker.")
        return None

    scheduler = BackgroundScheduler(timezone="UTC")

    def reminder_job():
        from .services import ReminderService
        with app.app_context():
            summary = ReminderService(app.config).run(date.today())
            log.info("Reminder run complete: %s", summary)

    def archive_job():
        from .extensions import db
        from .models import Submission, CertificationPeriod
        from .constants import SubmissionStatus
        from .models.base import utcnow
        with app.app_context():
            closed = db.session.query(CertificationPeriod).filter(
                CertificationPeriod.IsArchived.is_(True)).all()
            for period in closed:
                rows = db.session.query(Submission).filter(
                    Submission.PeriodId == period.PeriodId,
                    Submission.Status == SubmissionStatus.ACCEPTED).all()
                for row in rows:
                    row.Status = SubmissionStatus.ARCHIVED
                    row.ArchivedUtc = utcnow()
            db.session.commit()

    scheduler.add_job(reminder_job, _cron(app.config["REMINDER_JOB_CRON"]),
                      id="reminder-evaluation", replace_existing=True)
    scheduler.add_job(archive_job, _cron(app.config["ARCHIVE_JOB_CRON"]),
                      id="archive-cycle", replace_existing=True)
    scheduler.start()
    app.extensions["scheduler"] = scheduler
    return scheduler
