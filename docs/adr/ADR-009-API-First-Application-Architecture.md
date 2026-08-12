Status: Accepted

Context
-------
The project exposes API routes for domain operations (submissions, reports, migration, lookups) under `/api/*` blueprints (see `app/submissions/routes.py`, `app/reports/routes.py`, `app/migration/routes.py`). UI templates consume the same shapes via AJAX (e.g., wizard fetches `/api/lookup/entities` and `/api/lookup/periods`). JSON serializers are implemented in `app/submissions/serializers.py`.

Decision
--------
Adopt an API-first architecture: implement RESTful JSON endpoints for core domain operations and build server-rendered UI pages that consume those APIs. Keep API endpoints authoritative for creation, updates, validation, and listing.

Consequences
------------
- Enables multiple clients (server-rendered pages, potential SPAs, or external integrations) to reuse the same APIs.
- Simplifies testing because services can be exercised through API calls in unit/integration tests.
- Encourages proper separation between presentation and business logic (services and serializers are shared between APIs and templates).

Alternatives Considered
-----------------------
- Tight coupling between UI and server templates with no JSON APIs — rejected to maintain flexibility for future clients and integrations.
