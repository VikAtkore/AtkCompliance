# Configuration Model

Four classes — `BaseConfig` → `Development` / `Testing` / `Production` — selected by `ACC_ENV`. Every value is environment-driven; `ProductionConfig.validate()` fails fast at startup if any of the five required secrets is absent, so a misconfigured deployment never serves traffic.

| Group | Variables | Notes |
|---|---|---|
| Core | `ACC_ENV`, `ACC_SECRET_KEY`, `ACC_MAX_UPLOAD_BYTES` | Secret key is **required** in production |
| Database | `ACC_DATABASE_URI`, `ACC_DB_POOL_SIZE`, `ACC_DB_MAX_OVERFLOW`, `ACC_DB_POOL_RECYCLE` | `pool_pre_ping` on — survives SQL Server failover |
| Entra ID | `ACC_ENTRA_TENANT_ID`, `ACC_ENTRA_CLIENT_ID`, `ACC_ENTRA_CLIENT_SECRET`, `ACC_ENTRA_REDIRECT_PATH`, `ACC_ENTRA_POST_LOGOUT_URI` | All required in production |
| SharePoint | `ACC_SPO_HOSTNAME`, `ACC_SPO_SITE_PATH`, `ACC_SPO_SITE_ID`, `ACC_SPO_DRIVE_ID`, `ACC_SPO_ATTACHMENT_ROOT`, `ACC_SPO_REFERENCE_ROOT` | Site/drive IDs resolvable once via `GraphClient` and then pinned |
| Business rules | `ACC_GROUP1_THRESHOLD` (250000), `ACC_GROUP2_THRESHOLD` (450000), `ACC_NO_EXCEPTION_TEXT`, `ACC_REQUIRE_ACK` | **Thresholds are configuration, not code** — a policy change is an env change, not a release |
| Jobs | `ACC_ENABLE_SCHEDULER`, `ACC_REMINDER_CRON`, `ACC_ARCHIVE_CRON`, `ACC_MAIL_SENDER_UPN`, `ACC_REMINDER_DRY_RUN` | Cron expressions are UTC |
| Logging | `ACC_LOG_DIR`, `ACC_LOG_LEVEL`, `ACC_LOG_MAX_BYTES`, `ACC_LOG_BACKUP_COUNT` | Rotating file handler, correlation ID in every line |

## Deliberate choices

- **`ACC_REMINDER_DRY_RUN` defaults to `true`.** Reminders log what they *would* send until you explicitly turn sending on. Given that the legacy recipient list was never visible in SharePoint, no mail should go out until Compliance has reviewed the configured recipients.
- **Thresholds are configuration.** `$250,000` and `$450,000` appear in exactly one place and flow into the seeded question text and the validation messages together.
- **`ACC_ENABLE_SCHEDULER` is per-worker.** IIS may run several worker processes; enabling the scheduler in all of them sends duplicate reminders. Enable it on one worker, or drive the jobs from Windows Scheduled Tasks calling `flask run-reminders`.
- **Attachment allow-list.** Uploads are restricted by extension and size (25 MB default) before any byte reaches SharePoint.
- **`DevAuthProvider` is fenced.** It raises if instantiated while `ACC_ENV=production`.

## Storage layout in SharePoint Online

```
/sites/Compliance/Shared Documents/
    ComplianceEvidence/{QuarterLabel}/{SubmissionId}/{filename}
    ReferenceDocuments/{QuarterLabel}/...
```

Quarter-then-submission keeps a cycle's evidence contiguous for retention and legal hold. Filenames are sanitized; the original name is preserved in `Attachment.OriginalFileName`, and a SHA-256 of every uploaded file is stored for integrity verification.
