"""Microsoft Graph client (app-only, client credentials).

Used for SharePoint Online file operations and reminder mail. Tokens are
cached in-process by MSAL and refreshed automatically.
"""
import logging
import msal
import requests

log = logging.getLogger(__name__)


class GraphError(Exception):
    pass


class GraphClient:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str,
                 base_url: str = "https://graph.microsoft.com/v1.0",
                 timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._app = msal.ConfidentialClientApplication(
            client_id=client_id, client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )
        self._scope = ["https://graph.microsoft.com/.default"]

    def _token(self) -> str:
        result = self._app.acquire_token_silent(self._scope, account=None)
        if not result:
            result = self._app.acquire_token_for_client(scopes=self._scope)
        if "access_token" not in result:
            raise GraphError(result.get("error_description", "Token acquisition failed."))
        return result["access_token"]

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token()}"
        response = requests.request(method, url, headers=headers,
                                    timeout=self.timeout, **kwargs)
        if response.status_code >= 400:
            log.error("Graph %s %s -> %s: %s", method, url, response.status_code,
                      response.text[:500])
            raise GraphError(f"Graph {method} {path} failed with {response.status_code}")
        return response

    def get_json(self, path: str, **kwargs) -> dict:
        return self.request("GET", path, **kwargs).json()

    # ---- Site / drive resolution ----
    def resolve_site_id(self, hostname: str, site_path: str) -> str:
        data = self.get_json(f"/sites/{hostname}:{site_path}")
        return data["id"]

    def resolve_default_drive_id(self, site_id: str) -> str:
        return self.get_json(f"/sites/{site_id}/drive")["id"]
