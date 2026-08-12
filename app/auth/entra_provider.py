"""Microsoft Entra ID provider using MSAL confidential client flow."""
import logging
import os
import msal
from .provider import AuthProvider, AuthenticatedIdentity, AuthError

log = logging.getLogger(__name__)


class EntraAuthProvider(AuthProvider):
    def __init__(self, tenant_id: str, client_id: str, client_secret: str,
                 authority: str, scopes: list[str]):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.authority = authority or f"https://login.microsoftonline.com/{tenant_id}"
        self.scopes = scopes or ["User.Read"]

    def _client(self) -> msal.ConfidentialClientApplication:
        return msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority,
        )

    def build_login_url(self, state: str, redirect_uri: str) -> str:
        return self._client().get_authorization_request_url(
            scopes=self.scopes, state=state, redirect_uri=redirect_uri,
            prompt="select_account",
        )

    def complete_login(self, request_args: dict, redirect_uri: str) -> AuthenticatedIdentity:
        if "error" in request_args:
            raise AuthError(request_args.get("error_description") or request_args["error"])
        code = request_args.get("code")
        if not code:
            raise AuthError("Authorization code missing from callback.")

        result = self._client().acquire_token_by_authorization_code(
            code=code, scopes=self.scopes, redirect_uri=redirect_uri
        )
        if "error" in result:
            log.error("Token acquisition failed: %s", result.get("error_description"))
            raise AuthError(result.get("error_description") or result["error"])

        claims = result.get("id_token_claims", {}) or {}
        upn = (claims.get("preferred_username") or claims.get("upn")
               or claims.get("email") or "")
        if not upn:
            raise AuthError("Token did not contain a usable user principal name.")

        return AuthenticatedIdentity(
            object_id=claims.get("oid"),
            user_principal_name=upn.lower(),
            display_name=claims.get("name") or upn,
            email=claims.get("email") or upn,
            job_title=None,
            department=None,
            group_ids=claims.get("groups", []) or [],
        )

    def build_logout_url(self, post_logout_uri: str) -> str:
        return (f"{self.authority}/oauth2/v2.0/logout"
                f"?post_logout_redirect_uri={post_logout_uri}")


class DevAuthProvider(AuthProvider):
    """Local/dev/test only. Never enabled when ACC_ENV=production.

    Signs in as ACC_DEV_UPN with no password. Append ?upn=someone@atkore.com to
    /auth/login to impersonate a different account while testing role scoping.
    """

    def __init__(self, upn: str = "dev.user@atkore.com",
                 display_name: str = "Development User"):
        self.upn = upn
        self.display_name = display_name

    def build_login_url(self, state: str, redirect_uri: str) -> str:
        return f"{redirect_uri}?state={state}&code=dev&upn={self.upn}"

    def complete_login(self, request_args: dict, redirect_uri: str) -> AuthenticatedIdentity:
        upn = (request_args.get("upn") or self.upn).lower()
        return AuthenticatedIdentity(
            object_id="00000000-0000-0000-0000-000000000000",
            user_principal_name=upn,
            display_name=self.display_name if upn == self.upn.lower() else upn,
            email=upn,
        )

    def build_logout_url(self, post_logout_uri: str) -> str:
        return post_logout_uri or "/"


def build_provider(config) -> AuthProvider:
    kind = (config.get("AUTH_PROVIDER") or "entra").lower()
    if kind == "dev":
        if os.environ.get("ACC_ENV", "").lower() == "production":
            raise RuntimeError("DevAuthProvider is not permitted in production.")
        return DevAuthProvider(
            upn=config.get("DEV_UPN", "dev.user@atkore.com"),
            display_name=config.get("DEV_DISPLAY_NAME", "Development User"))
    if kind == "entra":
        return EntraAuthProvider(
            tenant_id=config["ENTRA_TENANT_ID"],
            client_id=config["ENTRA_CLIENT_ID"],
            client_secret=config["ENTRA_CLIENT_SECRET"],
            authority=config["ENTRA_AUTHORITY"],
            scopes=config["ENTRA_SIGNIN_SCOPES"],
        )
    raise RuntimeError(f"Unsupported AUTH_PROVIDER '{kind}'. Expected 'entra' or 'dev'.")
