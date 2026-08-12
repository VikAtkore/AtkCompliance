# Authentication & Authorization Design

**Decision applied:** Microsoft Entra ID via MSAL, with a SQL-backed role model.

## Split of responsibility

| Concern | Owner |
|---|---|
| *Who is this person?* | Entra ID (MSAL authorization-code flow, confidential client) |
| *What may they do?* | SQL — `AppUser` / `Role` / `UserRole` |
| *Which rows may they see?* | SQL — `UserRole` scope columns, applied in `scoped_query()` |

Entra never carries authorization data. This is deliberate: quarter-to-quarter reviewer reassignment is a Compliance Admin action inside the portal, not an IT ticket to change group membership.

## Sign-in sequence

```
Browser → GET /auth/login
          ↳ generate CSRF state, store in session
          ↳ 302 to https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
Entra   → user authenticates (MFA/conditional access enforced by tenant policy)
        → 302 back to /auth/callback?code=...&state=...
App     → verify state matches session  (mismatch ⇒ 400 invalid_state)
        → acquire_token_by_authorization_code()
        → read id_token_claims: oid, preferred_username, name, groups
        → provision_user(): upsert AppUser, grant Submitter on first sign-in
        → session["user_id"] = <AppUser.UserId>;  audit Login
        → 302 to originally requested page
```

Every subsequent request runs `load_current_user()` in a `before_request` hook, which materializes a `CurrentUser` carrying roles, the resolved permission set, and the data scope.

## App registration requirements

| Setting | Value |
|---|---|
| Platform | Web |
| Redirect URI | `https://compliance.atkore.com/auth/callback` |
| Front-channel logout | `https://compliance.atkore.com/` |
| Delegated (sign-in) | `User.Read` |
| Application (app-only, admin consent) | `Sites.Selected` (preferred) or `Files.ReadWrite.All`, plus `Mail.Send` |
| Credential | Client secret in the app pool environment, or certificate — **never in source** |

`Sites.Selected` is the recommended choice: it grants the app write access to the single compliance SharePoint site rather than to every site in the tenant.

## Just-in-time provisioning

First successful sign-in creates the `AppUser` row and grants **Submitter**. Reviewer, ComplianceAdmin, and SystemAdmin are granted explicitly through Admin Center → Users & Roles, and every grant or revoke writes a `RoleChange` audit row with the full before/after payload.

Optional: `ENTRA_GROUP_ROLE_MAP` maps Entra security-group object IDs to portal roles for tenants that prefer group-driven administration. It is empty by default — grants are explicit until you decide otherwise.

## Session security

| Control | Setting |
|---|---|
| Cookie name | `acc_session` |
| Flags | `HttpOnly`, `Secure`, `SameSite=Lax` |
| Lifetime | 480 minutes (configurable) |
| Session fixation | `session.clear()` immediately before establishing the authenticated session |
| CSRF | State parameter on the OAuth flow; Flask-WTF tokens on Phase 2 form posts |

## Provider abstraction

`AuthProvider` (`build_login_url` / `complete_login` / `build_logout_url`) has three implementations: `EntraAuthProvider` (production), `DevAuthProvider` (local and test only — it raises if `ACC_ENV=production`), and a documented seam for a future Windows Integrated Authentication provider. No business logic imports MSAL; only `entra_provider.py` does.

## Graph token model

Two separate token flows, intentionally:

- **User token** (delegated, `User.Read`) — sign-in only. Discarded after the identity claims are read.
- **App token** (client credentials, `.default`) — all SharePoint file operations and reminder mail.

Consequence: attachment access control is enforced by the portal's permission model, not by SharePoint's per-user ACLs. A user who is not authorized in the portal cannot obtain a download URL, even if they could reach the SPO library directly. Document this in the security review — it is a decision, not an oversight.
