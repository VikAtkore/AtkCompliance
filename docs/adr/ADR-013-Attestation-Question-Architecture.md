Status: Proposed

Context
-------
The application models `Attestation` and seeds attestation rows during draft creation (see `app/services/submission_service.py` and `app/models/attestation.py`). The certification wizard includes a placeholder attestation step in `app/templates/certifications/new.html` but the UI wiring for full attestation editing and persistence is incomplete.

Decision
--------
Design the attestation/question architecture as a set of normalized domain objects persisted in the main relational schema:

- `Question` (catalog) — static definitions for questionnaire items, grouped by `Section` and `Category`.
- `Attestation` — a template row describing an attestation requirement (linked to `Question` where appropriate).
- `QuestionResponse` or `AttestationResponse` — per-submission answer rows capturing the selected value, free-text comment, and optional metadata (who edited, edit timestamp).

Implementation Recommendations
--------------------------
- Keep `Question` catalog immutable in regular operation; publish new versions via migrations or controlled admin UI.
- Seed attestations at draft start (`submission_service.start_draft`) but store responses separately so drafts may be re-seeded without losing user answers.
- Use SQLAlchemy relationships with eager loading for UI endpoints that render the wizard pages to avoid DetachedInstanceError in tests.
- Provide API endpoints under `/api/submissions/<id>/responses` to `GET` and `PATCH` responses; implement bulk save to reduce round-trips from the wizard UI.
- Validate responses server-side via `validation_service` and return structured error details for client-side display.

Consequences
------------
- Allows fine-grained auditing of attestation answers and per-submission history.
- Enables partial saves (drafts) and reconciling catalog changes over time.

Alternatives Considered
-----------------------
- Storing attestation responses as a JSON blob on `Submission` — simpler but harder to query, validate, and audit; rejected.
