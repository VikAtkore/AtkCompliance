Status: Accepted

Context
-------
The repository includes a test suite under `tests/` with `pytest` fixtures in `tests/conftest.py`. Tests exercise services, templates, and API routes (see `tests/test_validation_rules.py`, `tests/test_certification_workflow.py`, `tests/test_home.py`). The test setup uses the `create_app('testing')` configuration and creates/tears down an SQLite test database via the `db` fixture.

Decision
--------
Adopt `pytest` for unit and integration tests, use Flask's test client for route/template tests, and create fixtures that provision a test database and sample domain data. Tests aim to verify services (validation, submission flow), API contracts, and UI templates rendering.

Consequences
------------
- Tests are runnable locally with minimal setup (SQLite) and are integrated into CI pipelines.
- The consistent fixture pattern makes it straightforward to add tests for new services and blueprints.
- Some production-specific behaviors (SQL Server-specific semantics, Entra integration) are validated through higher-level integration tests or staging environments.

Alternatives Considered
-----------------------
- Use a different test runner or full browser-based E2E tests only — the project combines unit/integration tests and may add E2E tests later (Playwright/Selenium) as needed.
