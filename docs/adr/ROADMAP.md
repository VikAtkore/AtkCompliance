# ADR Roadmap

## Current State
- Flask application with application factory: `app/__init__.py`.
- Models: normalized schema for `Submission`, `QuestionnaireResponse`, `Attestation`, `Attachment` in `app/models/`.
- Submission lifecycle and validation services: `app/services/submission_service.py`, `app/services/validation_service.py`.
- API-first design with blueprints under `app/*/routes.py` (submissions, reports, migration, auth).
- Bootstrap 5 server-rendered UI, certification wizard (`app/templates/certifications/new.html`).
- SQLite used for local development and tests; Alembic migrations present in `migrations/`.
- Tests with `pytest` under `tests/` covering validation rules, wizard workflow, and templates.

## In Progress
- Wizard UI improvements: draft save/load, cancel with unsaved warning, submission ID display.
- Placeholder UI pages for certifications, reports, and admin.
- ADR documentation generated in `docs/adr/`.

## Next Milestones
- Add attestation editing and response saving in the wizard (client-side wiring to `/api/submissions/<id>/responses` and `/attestations`).
- Implement CI pipelines with tests and linting checks.
- Harden authentication integration for staging and production environments.
- Prepare a SQL Server staging environment and validate migrations.

## Future Milestones
- Complete migration tooling and verification reports for SharePoint data.
- Implement role-based admin UI pages (entity/period management).
- Add E2E tests (Playwright) that run against a deployed test instance.

## Technical Debt
- Minimal front-end test coverage (no E2E yet).
- Some UI is placeholder and needs UX polish and accessibility review.
- External identity integration and production DB configuration are not yet fully automated.

## Production Readiness Checklist
- [ ] Finalize SQL Server connection and run Alembic migrations in staging.
- [ ] Configure secure secrets management (connection strings, Entra credentials).
- [ ] Add CI/CD pipeline that runs tests and applies migrations.
- [ ] Complete migration plan and perform data verification runs.
- [ ] Conduct security review and vulnerability scans.
- [ ] Load test and performance profiling for expected production scale.

