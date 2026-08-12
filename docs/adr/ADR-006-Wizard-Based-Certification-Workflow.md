Status: Accepted

Context
-------
The repository includes a multi-step Certification Wizard UI at `app/templates/certifications/new.html` that implements a five-step flow (Select Entity, Certification Info, Attestation Questions, Review, Submit). The wizard interacts with API endpoints such as `POST /api/submissions` and `PATCH /api/submissions/<id>` (implemented in `app/submissions/routes.py`) to create and persist drafts.

Decision
--------
Implement a server-backed, client-side wizard for certification creation. The UI is server-rendered but uses lightweight client-side JavaScript to fetch lookups (`/api/lookup/entities`, `/api/lookup/periods`) and to create/update drafts via the submission APIs.

Consequences
------------
- The wizard leverages existing APIs and keeps complexity on the client minimal.
- Persisting drafts via existing endpoints ensures server-side validation and audit logging (see `SubmissionService.start_draft`, `AuditService`).
- Attestation and question loading uses seeded rows created on draft creation (`SubmissionService._seed_questionnaire`, `_seed_attestations`).

Alternatives Considered
-----------------------
- Fully server-driven multi-page wizard — rejected for poorer UX and extra round trips.
- Single-page SPA wizard — rejected to preserve server-rendered templates and keep the front-end stack minimal for Phase 2.
