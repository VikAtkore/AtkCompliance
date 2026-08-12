# REST Endpoint Inventory — Phase 1

46 endpoints. Phase 1 is JSON-only; Phase 2 templates consume these same shapes.
Every endpoint below is guarded by a **permission**, never a role name.

## Authentication — `/auth`

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/auth/login` | anonymous | Redirect to Entra ID with CSRF state |
| GET/POST | `/auth/callback` | anonymous | Validate state, exchange code, JIT-provision `AppUser` |
| GET | `/auth/logout` | anonymous | Clear session, redirect to Entra sign-out |
| GET | `/auth/me` | signed in | Current identity, roles, permissions, data scope |

## Submissions — `/api/submissions`

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/api/submissions` | `submission.view.own` | List submissions visible to caller (scoped) |
| POST | `/api/submissions` | `submission.create` | Start a draft; seeds 10 questions + attestations |
| GET | `/api/submissions/{id}` | ownership or scope | Full submission detail |
| PATCH | `/api/submissions/{id}` | `submission.edit.own` | Update header/context fields |
| PUT | `/api/submissions/{id}/attestations` | `submission.edit.own` | Set selected certification modules |
| POST | `/api/submissions/{id}/attestations/{aid}/acknowledge` | `submission.edit.own` | Record acknowledgement + exception text |
| PUT | `/api/submissions/{id}/responses` | `submission.edit.own` | Save questionnaire answers and explanations |
| POST | `/api/submissions/{id}/validate` | ownership or scope | Dry-run validation (drives the wizard's summary) |
| POST | `/api/submissions/{id}/submit` | `submission.submit` | Validate + transition to Submitted (422 on failure) |
| POST | `/api/submissions/{id}/reopen` | `submission.reopen` | Admin reopen with recorded reason |
| POST | `/api/submissions/{id}/attachments` | `attachment.upload` | Upload evidence to SharePoint Online |
| GET | `/api/submissions/{id}/attachments` | ownership or scope | List non-deleted attachments |
| GET | `/api/submissions/{id}/attachments/{aid}/download` | ownership or scope | Short-lived Graph pre-authenticated URL |

## Reporting — `/api/reports`

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/api/reports/submissions` | `report.view` | Filtered, paged reviewer queue |
| GET | `/api/reports/summary` | `report.view` | Status counts for a period |
| GET | `/api/reports/missing` | `report.view.missing` | Entities with no submission this period |
| GET | `/api/reports/export` | `report.export` | Audit-ready `.xlsx` (17 columns; export is audited) |

## Administration — `/api/admin`

| Method | Path | Permission |
|---|---|---|
| GET / POST | `/api/admin/periods` | `admin.period.manage` |
| PATCH | `/api/admin/periods/{id}` | `admin.period.manage` |
| GET / POST | `/api/admin/entities` | `admin.entity.manage` |
| PATCH | `/api/admin/entities/{id}` | `admin.entity.manage` |
| GET / POST | `/api/admin/reference-documents` | `admin.refdoc.manage` |
| GET | `/api/admin/users` | `admin.role.manage` |
| POST | `/api/admin/users/{id}/roles` | `admin.role.manage` |
| DELETE | `/api/admin/users/{id}/roles/{urid}` | `admin.role.manage` |
| GET | `/api/admin/audit` | `admin.audit.view` |

## Reminders — `/api/reminders`

| Method | Path | Permission |
|---|---|---|
| GET / POST | `/api/reminders/milestones` | `admin.reminder.manage` |
| POST | `/api/reminders/milestones/{id}/recipients` | `admin.reminder.manage` |
| GET | `/api/reminders/templates` | `admin.reminder.manage` |
| GET | `/api/reminders/runs` | `admin.reminder.manage` |
| POST | `/api/reminders/run` | `admin.reminder.run` |

## Migration — `/api/migration` (SystemAdmin only)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/migration/xml/stage` | `system.migration.run` |
| POST | `/api/migration/vlookup/merge` | `system.migration.run` |
| GET | `/api/migration/reconcile` | `system.migration.run` |

## Lookups & platform

| Method | Path | Permission | Purpose |
|---|---|---|---|
| GET | `/api/navigation` | signed in | Permission-pruned menu tree |
| GET | `/api/lookup/periods` | signed in | Open certification periods |
| GET | `/api/lookup/entities` | signed in | Active entity master (drives the entity dropdown) |
| GET | `/api/lookup/reference-documents` | signed in | Acknowledgement documents for a period + module |
| GET | `/health` | anonymous | Uptime probe with database check (503 when degraded) |

## Conventions

- **Errors** return `{"error": "<code>", "message": "..."}`. Codes: `authentication_required` (401), `forbidden` (403), `not_found` (404), `invalid_state` (409), `validation_failed` (422), `payload_too_large` (413), `internal_error` (500).
- **Validation failures** on submit return HTTP 422 with a full issue list — each issue carries `field`, `code`, `message`, and `step` so the wizard can jump to the offending step.
- **Correlation** — every request carries `X-Correlation-Id` (echoed on the response, written to logs and to `AuditLog.CorrelationId`).
- **Concurrency** — `Submission.RowVersion` increments on every mutation; Phase 2 sends it back for optimistic concurrency.
