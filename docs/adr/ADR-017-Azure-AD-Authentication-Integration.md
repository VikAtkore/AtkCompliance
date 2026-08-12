Status: Proposed

Context
-------
The project already contains an Entra provider integration (`app/auth/entra_provider.py`) and local identity plumbing (`app/auth/identity.py`). Production authentication is targeted at Azure AD (Entra).

Decision
--------
Fully integrate Azure AD for production authentication and authorization using MSAL/OAuth2 flows and keep local `AppUser` records for role and permission mappings.

Implementation Recommendations
--------------------------
- Use Microsoft Authentication Library (MSAL) for Python to implement server-side OAuth2 authorization code flow for web sign-in and token acquisition.
- Configure an Azure AD App Registration with appropriate redirect URIs and configured application permissions for Graph if the app will call Graph APIs.
- Validate incoming tokens and implement session management: avoid storing raw tokens in sessions for long-term; store minimal claims and refresh tokens securely if required.
- For API-to-API calls, use client credentials flow with application identity.
- Document required configuration (tenant ID, client ID, client secret, scopes) in `config.py` and secrets management for production.

Consequences
------------
- Centralizes identity and enables enterprise SSO and conditional access policies.
- Requires secure secret management and periodic secret rotation; tests must simulate authentication when needed.

Alternatives Considered
-----------------------
- Use a custom OAuth provider or local username/password — rejected due to enterprise SSO requirement.
