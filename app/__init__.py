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

    _ensure_local_folders(app)
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


def _ensure_local_folders(app: Flask) -> None:
    """SQLite development databases live in the instance folder.

    Flask-SQLAlchemy resolves a *relative* sqlite path against
    app.instance_path, so the folder must exist before the engine connects.
    An absolute path (or SQL Server) needs nothing from us.
    """
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri.startswith("sqlite") or ":memory:" in uri:
        return
    os.makedirs(app.instance_path, exist_ok=True)
    path = uri.split("///", 1)[-1]
    if os.path.isabs(path) and os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)


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
    from .certifications import bp as certifications_bp
    from .admin import bp as admin_bp
    from .reports import bp as reports_bp
    from .reminders import bp as reminders_bp
    from .migration import bp as migration_bp

    for blueprint in (auth_bp, submissions_bp, certifications_bp, admin_bp,
                      reports_bp, reminders_bp, migration_bp):
        app.register_blueprint(blueprint)

    from .navigation import visible_navigation
    from .auth.decorators import login_required
    from .services import EntityService, PeriodService
    from .services.attestation_service import AttestationService
    from flask import render_template

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

    @app.get("/")
    def index():
        # Placeholder summary counts for dashboard cards
        counts = {
            "my_certifications": 3,
            "create_certification": 0,
            "reports": 7,
            "administration": 1,
        }
        return render_template("index.html", counts=counts)

    @app.get("/reports")
    def reports_ui():
        return render_template("reports/index.html")

    @app.get("/admin")
    def admin_ui():
        return render_template("admin/index.html")


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

    @app.cli.command("dev-init")
    def dev_init():
        """Create the local schema and load sample data. Development only."""
        if os.environ.get("ACC_ENV", "").lower() == "production":
            raise click.ClickException("dev-init cannot be run against production.")
        from datetime import date
        from .models import (Role, CertificationPeriod, EntityMaster, AppUser,
                             UserRole, ReminderTemplate, ReminderMilestone)
        from .constants import RoleName, ReminderLevel

        db.create_all()

        for name in RoleName:
            if not db.session.query(Role).filter(Role.RoleName == name.value).first():
                db.session.add(Role(RoleName=name.value, Description=f"{name.value} role"))
        db.session.commit()

        if not db.session.query(CertificationPeriod).first():
            db.session.add(CertificationPeriod(
                QuarterLabel="Q1 2026", FiscalYear=2026, QuarterNumber=1,
                StartDate=date(2026, 1, 1), DueDate=date(2026, 2, 15),
                IsOpen=True, Enable404=False))
            db.session.add(CertificationPeriod(
                QuarterLabel="Q4 2025", FiscalYear=2025, QuarterNumber=4,
                StartDate=date(2025, 10, 1), DueDate=date(2025, 11, 15),
                IsOpen=False, Enable404=True))

        if not db.session.query(EntityMaster).first():
            db.session.add_all([
                EntityMaster(Title="Atkore Mokena", EntityNumber="1001",
                             PullName="Mokena", Region="North America",
                             BusinessSegment="Electrical", BusinessUnit="Conduit",
                             Location="Mokena", IsGroup1=False, IsGroup2=True),
                EntityMaster(Title="Atkore Harvey", EntityNumber="1002",
                             PullName="Harvey", Region="North America",
                             BusinessSegment="Electrical", BusinessUnit="Cable",
                             Location="Harvey", IsGroup1=True, IsGroup2=False),
                EntityMaster(Title="Atkore Safety & Infrastructure", EntityNumber="2001",
                             PullName="S&I", Region="North America",
                             BusinessSegment="Safety & Infrastructure",
                             BusinessUnit="Mechanical", Location="Phoenix",
                             IsGroup1=True, IsGroup2=False),
            ])

        if not db.session.query(ReminderTemplate).first():
            template = ReminderTemplate(
                Name="Standard certification reminder",
                Subject="Action required: quarterly compliance certification",
                BodyHtml="<p>Your quarterly compliance certification is due. "
                         "Please complete it in the Compliance Portal.</p>",
                TargetAudience="Submitter")
            db.session.add(template)
            db.session.flush()
            db.session.add(ReminderMilestone(
                Title="14 days before due date", OffsetDaysFromDue=-14,
                ReminderLevel=ReminderLevel.ADVANCE, TemplateId=template.TemplateId))
        db.session.commit()

        upn = app.config.get("DEV_UPN", "dev.user@atkore.com").lower()
        user = db.session.query(AppUser).filter(
            AppUser.UserPrincipalName == upn).first()
        if user is None:
            user = AppUser(UserPrincipalName=upn,
                           DisplayName=app.config.get("DEV_DISPLAY_NAME", "Dev User"),
                           Email=upn)
            db.session.add(user)
            db.session.flush()
        for name in RoleName:
            role = db.session.query(Role).filter(Role.RoleName == name.value).first()
            exists = db.session.query(UserRole).filter(
                UserRole.UserId == user.UserId, UserRole.RoleId == role.RoleId).first()
            if not exists:
                db.session.add(UserRole(UserId=user.UserId, RoleId=role.RoleId,
                                        GrantedBy="dev-init"))
        db.session.commit()
        click.echo(f"Database: {db.engine.url}")
        click.echo(f"Instance folder: {app.instance_path}")
        click.echo(f"Local database ready. Signed-in dev user: {upn} (all four roles).")

    @app.cli.command("grant-role")
    @click.argument("upn")
    @click.argument("role_name")
    def grant_role(upn, role_name):
        """Grant a portal role: flask grant-role user@atkore.com Reviewer"""
        from .models import AppUser, Role, UserRole
        user = db.session.query(AppUser).filter(
            AppUser.UserPrincipalName == upn.lower()).first()
        role = db.session.query(Role).filter(Role.RoleName == role_name).first()
        if user is None:
            raise click.ClickException(f"No user {upn}. They must sign in once first.")
        if role is None:
            raise click.ClickException(f"Unknown role {role_name}.")
        db.session.add(UserRole(UserId=user.UserId, RoleId=role.RoleId,
                                GrantedBy="cli"))
        db.session.commit()
        click.echo(f"Granted {role_name} to {upn}.")

    @app.cli.command("list-routes")
    def list_routes():
        """Print every registered endpoint."""
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
            click.echo(f"{methods:<22} {rule}")
