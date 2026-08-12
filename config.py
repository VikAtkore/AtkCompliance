"""Configuration model for the Atkore Compliance Certification Portal.

All secrets are read from environment variables. Nothing sensitive is
committed to source control -- see .env.example for the full contract.
"""
import os
from datetime import timedelta


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class BaseConfig:
    # ---- Core Flask ----
    SECRET_KEY = os.environ.get("ACC_SECRET_KEY", "dev-only-change-me")
    PREFERRED_URL_SCHEME = "https"
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = _int("ACC_MAX_UPLOAD_BYTES", 25 * 1024 * 1024)

    # ---- Session ----
    SESSION_COOKIE_NAME = "acc_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=_int("ACC_SESSION_MINUTES", 480))

    # ---- Database (SQL Server via pyodbc) ----
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "ACC_DATABASE_URI",
        "mssql+pyodbc://@ATKSQL01/AtkoreCompliance"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": _int("ACC_DB_POOL_RECYCLE", 1800),
        "pool_size": _int("ACC_DB_POOL_SIZE", 10),
        "max_overflow": _int("ACC_DB_MAX_OVERFLOW", 20),
    }

    # ---- Authentication: Microsoft Entra ID (MSAL) ----
    AUTH_PROVIDER = os.environ.get("ACC_AUTH_PROVIDER", "entra")  # entra | windows | dev
    ENTRA_TENANT_ID = os.environ.get("ACC_ENTRA_TENANT_ID", "")
    ENTRA_CLIENT_ID = os.environ.get("ACC_ENTRA_CLIENT_ID", "")
    ENTRA_CLIENT_SECRET = os.environ.get("ACC_ENTRA_CLIENT_SECRET", "")
    ENTRA_AUTHORITY = os.environ.get(
        "ACC_ENTRA_AUTHORITY",
        f"https://login.microsoftonline.com/{os.environ.get('ACC_ENTRA_TENANT_ID', '')}",
    )
    ENTRA_REDIRECT_PATH = os.environ.get("ACC_ENTRA_REDIRECT_PATH", "/auth/callback")
    ENTRA_POST_LOGOUT_URI = os.environ.get("ACC_ENTRA_POST_LOGOUT_URI", "")
    # Delegated sign-in scopes. Graph file scopes are requested on the app
    # identity (client credentials), not on the user token.
    ENTRA_SIGNIN_SCOPES = ["User.Read"]
    ENTRA_GRAPH_APP_SCOPE = ["https://graph.microsoft.com/.default"]
    # Optional: map Entra security groups (object IDs) to portal roles.
    ENTRA_GROUP_ROLE_MAP = {}

    # ---- Microsoft Graph / SharePoint Online attachment storage ----
    GRAPH_BASE_URL = os.environ.get("ACC_GRAPH_BASE_URL", "https://graph.microsoft.com/v1.0")
    SPO_HOSTNAME = os.environ.get("ACC_SPO_HOSTNAME", "atkore.sharepoint.com")
    SPO_SITE_PATH = os.environ.get("ACC_SPO_SITE_PATH", "/sites/Compliance")
    SPO_SITE_ID = os.environ.get("ACC_SPO_SITE_ID", "")
    SPO_DRIVE_ID = os.environ.get("ACC_SPO_DRIVE_ID", "")
    SPO_ATTACHMENT_ROOT = os.environ.get("ACC_SPO_ATTACHMENT_ROOT", "ComplianceEvidence")
    SPO_REFERENCE_DOC_ROOT = os.environ.get("ACC_SPO_REFERENCE_ROOT", "ReferenceDocuments")
    SPO_LARGE_FILE_THRESHOLD = _int("ACC_SPO_LARGE_FILE_BYTES", 4 * 1024 * 1024)
    SPO_UPLOAD_CHUNK_BYTES = _int("ACC_SPO_CHUNK_BYTES", 5 * 320 * 1024)
    ALLOWED_UPLOAD_EXTENSIONS = {
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv",
        ".ppt", ".pptx", ".msg", ".txt", ".png", ".jpg", ".jpeg",
    }

    # ---- Compliance business rules ----
    GROUP1_EXCEPTION_THRESHOLD = _int("ACC_GROUP1_THRESHOLD", 250000)
    GROUP2_EXCEPTION_THRESHOLD = _int("ACC_GROUP2_THRESHOLD", 450000)
    DEFAULT_NO_EXCEPTION_TEXT = os.environ.get("ACC_NO_EXCEPTION_TEXT", "None noted")
    REQUIRE_ACKNOWLEDGEMENT = _bool("ACC_REQUIRE_ACK", True)

    # ---- Reminder jobs ----
    ENABLE_SCHEDULER = _bool("ACC_ENABLE_SCHEDULER", False)
    REMINDER_JOB_CRON = os.environ.get("ACC_REMINDER_CRON", "0 13 * * *")  # UTC
    ARCHIVE_JOB_CRON = os.environ.get("ACC_ARCHIVE_CRON", "0 5 1 * *")
    MAIL_SENDER_UPN = os.environ.get("ACC_MAIL_SENDER_UPN", "compliance-noreply@atkore.com")
    REMINDER_DRY_RUN = _bool("ACC_REMINDER_DRY_RUN", True)

    # ---- Logging / ops ----
    LOG_DIR = os.environ.get("ACC_LOG_DIR", "logs")
    LOG_LEVEL = os.environ.get("ACC_LOG_LEVEL", "INFO")
    LOG_MAX_BYTES = _int("ACC_LOG_MAX_BYTES", 10 * 1024 * 1024)
    LOG_BACKUP_COUNT = _int("ACC_LOG_BACKUP_COUNT", 10)
    HEALTHCHECK_PATH = "/health"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    AUTH_PROVIDER = os.environ.get("ACC_AUTH_PROVIDER", "dev")
    REMINDER_DRY_RUN = True


class TestingConfig(BaseConfig):
    TESTING = True
    AUTH_PROVIDER = "dev"
    SQLALCHEMY_DATABASE_URI = os.environ.get("ACC_TEST_DATABASE_URI", "sqlite+pysqlite:///:memory:")
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    ENABLE_SCHEDULER = False


class ProductionConfig(BaseConfig):
    DEBUG = False

    @classmethod
    def validate(cls):
        missing = [k for k in ("ACC_SECRET_KEY", "ACC_DATABASE_URI", "ACC_ENTRA_TENANT_ID",
                               "ACC_ENTRA_CLIENT_ID", "ACC_ENTRA_CLIENT_SECRET")
                   if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    name = name or os.environ.get("ACC_ENV", "development")
    return CONFIG_MAP.get(name, DevelopmentConfig)
