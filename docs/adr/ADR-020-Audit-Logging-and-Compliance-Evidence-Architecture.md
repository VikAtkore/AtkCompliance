Status: Proposed

Context
-------
The codebase contains `app/models/audit.py` and services that touch domain entities. Tests and regulatory requirements imply the need for an auditable trail of changes and exports for compliance evidence.

Decision
--------
Adopt an append-only audit logging model for domain changes plus structured application logging to capture operational events. Store audit events in the primary database and provide exports for compliance review.

Implementation Recommendations
--------------------------
- Implement an `AuditEvent` table capturing: event id, timestamp (UTC), actor (user id), target object type and id, operation (`create`, `update`, `delete`, `submit`), before/after payloads (JSON), and correlation id.
- Use SQL Server Temporal Tables or an append-only audit table with triggers where DB-level enforcement is required.
- Integrate application logs (structured) via `structlog` or Python `logging` with JSON format and forward to a log aggregation/SIEM (e.g., Azure Monitor, Splunk) for operational auditing.
- Hash and store file attachment checksums (SHA-256) at upload time and include hash references in audit records to ensure tamper-evidence for attachments.
- Provide admin/export endpoints that produce signed/verified evidence packages for compliance (include data snapshot, attachments, and a manifest with hashes and timestamps).
- Retention policies, access controls on audit exports, and legal hold procedures should be defined and automated where possible.

Consequences
------------
- Produces reliable evidence for compliance requests and investigations.
- Requires storage planning and maintenance for audit data volume and secure access controls.

Alternatives Considered
-----------------------
- Rely solely on application logs — insufficient for compliance-grade evidence because logs are transient and often trimmed; rejected.
