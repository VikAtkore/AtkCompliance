"""AuthProvider abstraction.

Entra ID via MSAL is the chosen standard. The interface is kept so that a
Windows Integrated Authentication provider can be dropped in without touching
business logic, and so tests can run under a deterministic stub.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AuthenticatedIdentity:
    object_id: str | None
    user_principal_name: str
    display_name: str
    email: str | None = None
    job_title: str | None = None
    department: str | None = None
    group_ids: list[str] = field(default_factory=list)


class AuthProvider(ABC):
    @abstractmethod
    def build_login_url(self, state: str, redirect_uri: str) -> str: ...

    @abstractmethod
    def complete_login(self, request_args: dict, redirect_uri: str) -> AuthenticatedIdentity: ...

    @abstractmethod
    def build_logout_url(self, post_logout_uri: str) -> str: ...


class AuthError(Exception):
    pass
