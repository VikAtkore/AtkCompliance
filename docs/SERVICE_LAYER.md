# Service Layer Design

Routes stay thin. All compliance logic lives in services so that the Phase 2 UI, the REST API, and the migration importer enforce **identical** behaviour — this is the specific failure mode of the InfoPath original, where rules lived inside `view1.xsl` and `manifest.xsf` and could not be reused.

| Service | Responsibility | Key operations |
|---|---|---|
| `SubmissionService` | Lifecycle owner. Creation, header edits, status transitions, row-level scoping. | `start_draft`, `update_header`, `submit`, `reopen`, `return_to_submitter`, `accept`, `archive`, `scoped_query` |
| `ValidationService` | Stateless rule engine — the 6 legacy rules. Pure functions over a loaded Submission. | `validate_for_submit`, `validate_for_draft`, `apply_no_exception_defaults` |
| `AttestationService` | Which modules apply this quarter, selection, acknowledgement, reference documents. | `available_types`, `set_selection`, `acknowledge`, `reference_documents` |
| `AttachmentService` | SharePoint Online I/O via Graph. Bytes out of SQL entirely. | `upload`, `download_url`, `soft_delete`, `validate_file` |
| `ReminderService` | Milestone evaluation, missing-submission gap analysis, notification, run logging. | `due_milestones`, `missing_submissions`, `run` |
| `ReportingService` | Reviewer queries and the audit-ready Excel export. | `search`, `status_summary`, `export_xlsx` |
| `MigrationService` | Legacy XML/Vlookup parsing, InfoPath base64 decoding, reconciliation. | `stage_xml`, `parse_staged`, `decode_infopath_attachment`, `merge_vlookup`, `reconcile` |
| `EntityService` / `PeriodService` | Master data CRUD with before/after auditing. | `create`, `update`, `list_active`, `open_periods` |
| `AuditService` | Single write path for the immutable trail. | `record`, `snapshot` |
| `GraphClient` | Thin Graph transport: token caching, retries, error normalization. | `request`, `get_json`, `resolve_site_id` |

## The six validation rules

| # | Rule | Legacy origin |
|---|---|---|
| 1 | Required header fields: quarter, employee name, business segment, preparer role | XSF required-field rule set |
| 2 | At least one certification module selected | Form could not submit with no section chosen |
| 3 | Every selected module requires its acknowledgement checkbox | Per-section acknowledgement in `view1.xsl` |
| 4 | Group 1 / Group 2 classification must be answered | Entity group question |
| 5 | **Yes ⇒ explanation required** — on all 10 questions and both threshold questions | The core compliance rule |
| 6 | Threshold questions must be answered for the applicable group ($250k / $450k) | Group-conditional sections |

Legacy behaviour preserved: `apply_no_exception_defaults()` writes **"None noted"** into empty explanations where the answer was No, matching what the InfoPath rule sets did — so migrated and new records read identically in an audit export.

Each `ValidationIssue` carries `field`, `code`, `message`, and **`step`**, letting the Phase 2 wizard route the user straight to the offending step from the validation summary.

## Status machine

```
Draft ──submit──▶ Submitted ──▶ UnderReview ──▶ Accepted ──▶ Archived
  ▲                   │              │
  └───── reopen ──────┴── return ────┘  (→ Returned → Draft)
```

Transitions are declared once in `ALLOWED_STATUS_TRANSITIONS` and enforced centrally in `_transition()`. An illegal move raises `TransitionError` → HTTP 409. Only `Draft` and `Returned` are editable; a `Submitted` record is immutable to its author, which is what makes it an audit artifact.

## Audit discipline

Everything mutating routes through `AuditService.record()` — create, edit, submit, reopen, return, accept, archive, attachment upload/delete, export, admin change, role change, reminder send, migration import, and login. Admin changes carry full `BeforeJson` / `AfterJson` snapshots, and secrets are redacted before serialization. `AuditLog` has no update or delete path anywhere in the codebase.

## Transaction boundaries

Services own commits; routes never call `db.session.commit()` directly. `_transition()` writes its audit row with `commit=False` so the status change and its audit entry land in a single transaction — a state change can never be recorded without its audit trail, or vice versa.
