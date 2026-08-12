Status: Accepted

Context
-------
Draft creation and persistence are implemented by `SubmissionService.start_draft` (`app/services/submission_service.py`) which seeds questionnaire responses and attestations, and by the submissions blueprint (`app/submissions/routes.py`) exposing `POST /api/submissions` and `PATCH /api/submissions/<id>` for header updates. The wizard uses these endpoints to create and update drafts.

Decision
--------
Persist drafts as full `Submission` rows with seeded `QuestionnaireResponse` and `Attestation` children. Use `Status = 'Draft'` to indicate editable submissions. Drafts are created server-side (POST) and updated via PATCH to `update_header` which enforces editable state and audit trails.

Consequences
------------
- Drafts are first-class domain objects and can be listed (`GET /api/submissions`) and reloaded by the UI.
- Server-side seeding of questions/attestations ensures consistent validation rules and reduces client complexity.
- The design supports audit logging via `AuditService.record` and enforces transitions using `SubmissionService._assert_editable`.

Alternatives Considered
-----------------------
- Store temporary client-side drafts until final submit — rejected because server-side drafts support collaboration, autosave, and consistent validation.
- Use a separate drafts table — rejected to reduce schema duplication and to reuse existing state transitions and auditing.
