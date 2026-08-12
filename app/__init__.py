"""Application factory for the Atkore Compliance Certification Portal."""
import logging
import os
import uuid
from logging.handlers import RotatingFileHandler
from flask import Flask, g, jsonify, request
from sqlalchemy import text
from config import get_config
from .extensions import db, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    if hasattr(config_class, "validate"):
        config_class.validate()

    _configure_logging(app)
    db.init_app(app)
    migrate.init_app(app, db)

    from . import models  # noqa: F401  -- ensures metadata is registered
    _register_blueprints(app)
    _register_hooks(app)
    _register_errors(app)
    _register_cli(app)

    from .jobs import register_jobs
    register_jobs(app)

    return app


def _configure_logging(app: Flask) -> None:
    log_dir = app.config.get("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_dir, "application.log"),
        maxBytes=app.config.get("LOG_MAX_BYTES", 10 * 1024 * 1024),
        backupCount=app.config.get("LOG_BACKUP_COUNT", 10), encoding="utf-8")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s [%(correlation_id)s] %(name)s: %(message)s"))

    class _CorrelationFilter(logging.Filter):
        def filter(self, record):
            record.correlation_id = getattr(g, "correlation_id", "-") \
                if request else "-"
            return True

    handler.addFilter(_CorrelationFilter())
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))


def _register_blueprints(app: Flask) -> None:
    from .auth import bp as auth_bp
    from .submissions import bp as submissions_bp
    from .admin import bp as admin_bp
    from .reports import bp as reports_bp
    from .reminders import bp as reminders_bp
    from .migration import bp as migration_bp

    for blueprint in (auth_bp, submissions_bp, admin_bp, reports_bp,
                      reminders_bp, migration_bp):
        app.register_blueprint(blueprint)

    from .navigation import visible_navigation
    from .auth.decorators import login_required
    from .services import EntityService, PeriodService
    from .services.attestation_service import AttestationService

    @app.get("/api/navigation")
    @login_required
    def navigation():
        return jsonify(items=visible_navigation(g.current_user))

    @app.get("/api/lookup/periods")
    @login_required
    def lookup_periods():
        return jsonify(items=[{
            "periodId": p.PeriodId, "quarterLabel": p.QuarterLabel,
            "dueDate": p.DueDate.isoformat() if p.DueDate else None,
            "enable404": p.Enable404,
        } for p in PeriodService.open_periods()])

    @app.get("/api/lookup/entities")
    @login_required
    def lookup_entities():
        return jsonify(items=[{
            "entityId": e.EntityId, "title": e.Title, "entityNumber": e.EntityNumber,
            "region": e.Region, "businessSegment": e.BusinessSegment,
            "businessUnit": e.BusinessUnit, "location": e.Location,
            "isGroup1": e.IsGroup1, "isGroup2": e.IsGroup2,
        } for e in EntityService.list_active()])

    @app.get("/api/lookup/reference-documents")
    @login_required
    def lookup_reference_documents():
        period_id = request.args.get("period_id", type=int)
        att_type = request.args.get("attestation_type", "")
        docs = AttestationService.reference_documents(period_id, att_type)
        return jsonify(items=[{
            "referenceDocumentId": d.ReferenceDocumentId, "title": d.Title,
            "storageUrl": d.StorageUrl,
        } for d in docs])

    @app.get(app.config.get("HEALTHCHECK_PATH", "/health"))
    def health():
        status = {"status": "ok", "database": "unknown"}
        try:
            db.session.execute(text("SELECT 1"))
            status["database"] = "ok"
        except Exception:  # noqa: BLE001 -- health must never raise
            status["status"] = "degraded"
            status["database"] = "unavailable"
        return jsonify(status), 200 if status["status"] == "ok" else 503


def _register_hooks(app: Flask) -> None:
    from .auth.identity import load_current_user

    @app.before_request
    def _before():
        g.correlation_id = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        g.current_user = None
        load_current_user()

    @app.after_request
    def _after(response):
        response.headers["X-Correlation-Id"] = getattr(g, "correlation_id", "-")
        return response


def _register_errors(app: Flask) -> None:
    @app.errorhandler(404)
    def _not_found(_):
        return jsonify(error="not_found"), 404

    @app.errorhandler(413)
    def _too_large(_):
        return jsonify(error="payload_too_large"), 413

    @app.errorhandler(500)
    def _server_error(exc):
        app.logger.exception("Unhandled error: %s", exc)
        return jsonify(error="internal_error",
                       correlationId=getattr(g, "correlation_id", None)), 500


def _register_cli(app: Flask) -> None:
    import click

    @app.cli.command("seed-roles")
    def seed_roles():
        """Insert the four fixed portal roles."""
        from .models import Role
        from .constants import RoleName
        for name in RoleName:
            if not db.session.query(Role).filter(Role.RoleName == name.value).first():
                db.session.add(Role(RoleName=name.value, Description=f"{name.value} role"))
        db.session.commit()
        click.echo("Roles seeded.")

    @app.cli.command("run-reminders")
    def run_reminders():
        """Execute the reminder evaluation job once."""
        from .services import ReminderService
        click.echo(ReminderService(app.config).run())
