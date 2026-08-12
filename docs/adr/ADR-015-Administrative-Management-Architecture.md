Status: Proposed

Context
-------
The repository contains an admin blueprint (`app/admin/routes.py`) and permission checks in `app/auth/permissions.py`. Admin UI placeholders exist under `app/templates/admin/`.

Decision
--------
Provide a role-and-permission driven administrative surface that centralizes management of core reference data: Entities, Periods, Question Catalog, Users/Roles, and Lookups.

Implementation Recommendations
--------------------------
- Implement CRUD admin endpoints under `/admin` and `/api/admin/*` guarded by `require_permission('admin.*')` decorators.
- Add an `AdminService` layer in `app/services/admin_service.py` for encapsulating domain logic and validations.
- Protect UI and API routes with granular permissions; surface audit trails for administrative changes (see ADR-020).
- Use server-rendered pages for simple admin tasks and progressively enhance with client-side behavior for bulk-edit and search.
- Provide import/export capabilities (CSV) for bulk reference updates and administrative workflows.

Consequences
------------
- Centralized admin improves maintainability and reduces duplication of reference data logic.
- Requires careful permission design and comprehensive tests for role boundaries.

Alternatives Considered
-----------------------
- Delegating admin tasks to direct DB access — faster short-term but risky and not auditable; rejected.
