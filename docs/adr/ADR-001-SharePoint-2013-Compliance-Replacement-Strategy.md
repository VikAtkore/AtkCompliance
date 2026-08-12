Status: Accepted

Context
-------
This repository implements the Atkore Compliance Certification Portal as a web application to replace legacy SharePoint 2013 InfoPath forms and related processes. Evidence in the codebase includes migration helpers and staging models under app/models/staging.py and the migration routes in app/migration/routes.py, plus the historical-preservation fields on `Submission` (LegacyXmlFileName, LegacyXmlPath, LegacySourceLibrary) in app/models/submission.py. The project contains scripts and references to a migration process in the `migrations/` folder and app/services/migration_service.py.

Decision
--------
Migrate away from SharePoint 2013 by extracting legacy XML submissions, importing their data into a normalized SQL schema hosted in the application database, and preserving references to original XML artifacts. The replacement system is implemented as a Flask application with a migration step that seeds normalized rows into `Submission`, `QuestionnaireResponse`, `Attestation`, and related tables.

Consequences
------------
- Data is normalized into relational tables that support efficient reporting and validation rules implemented in app/services/validation_service.py.
- Legacy traceability is preserved via fields such as `LegacyXmlFileName` on `Submission` and separate staging models for import diagnostics. See app/models/staging.py.
- Migration code and import scripts must be maintained and kept in sync with the application model changes.
- The effort reduces dependency on SharePoint-specific features but requires a careful migration plan (data mapping, attachments, permission mappings).

Alternatives Considered
-----------------------
- Keep running the SharePoint/InfoPath solution unchanged — rejected due to maintenance, security, and modernization concerns.
- Build a SharePoint front-end on top of new SQL data — rejected because the codebase is intentionally API-first and decoupled from SharePoint.
