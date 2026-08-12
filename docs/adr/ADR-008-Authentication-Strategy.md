Status: Accepted

Context
-------
Authentication and authorization are implemented via an Entra provider integration in `app/auth/entra_provider.py` and local identity provisioning in `app/auth/identity.py`. The `create_app` bootstrapping registers `load_current_user` to populate `g.current_user` on each request. Permissions map to route guards (`app/auth/decorators.py`) and the permissions catalogue is in `app/auth/permissions.py`.

Decision
--------
Use Entra (Azure AD) for authentication in production with just-in-time user provisioning into the `AppUser` table for authorization and role/grant assignment. For local development and tests, the code uses session-based `user_id` population (see `tests/conftest.py` which sets `session['user_id']` for test requests).

Consequences
------------
- Real environment uses external identity provider while the app retains a local AppUser record for role and scope management.
- Tests and local development can simulate authenticated users by writing `user_id` to the Flask session.
- Authorization checks rely on `CurrentUser.can(...)` and decorators like `require_permission` that return JSON 401/403 for API routes.

Alternatives Considered
-----------------------
- Manage authentication entirely in-app — rejected to leverage enterprise SSO and central identity management.
- Use mock authentication in production — rejected for security and audit concerns.
