Status: Proposed

Context
-------
Migration code and staging models exist in `app/models/staging.py` and `app/migration/routes.py`. The `migrations/` folder (Alembic) and `app/services/migration_service.py` contain helpers for moving legacy data into the normalized schema but a full production migration plan is not present in code.

Decision
--------
Propose a staged migration approach: export legacy InfoPath XML and attachments, load into staging tables for validation and transformation, then map into normalized tables (`Submission`, `QuestionnaireResponse`, `Attestation`, `Attachment`). Preserve legacy references (LegacyXmlFileName) and implement verification reports to ensure parity.

Consequences
------------
- Requires an operational migration pipeline and verification tooling; staging tables and scripts in the repo are a starting point.
- Attachment migration must handle SharePoint item paths and Graph-based storage references; this may be complex and require auxiliary tooling.

Alternatives Considered
-----------------------
- Big-bang direct migration without staging — rejected due to high risk and lack of rollback/validation.
- Keep SharePoint data live and run the new app in parallel — possible as an interim strategy but not a long-term solution.
