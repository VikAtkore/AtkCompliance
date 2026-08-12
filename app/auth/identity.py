"""Current-user resolution and just-in-time provisioning."""
from dataclasses import dataclass
from flask import g, session
from sqlalchemy import select
from ..extensions import db
from ..models import AppUser, Role, UserRole
from ..constants import RoleName
from .permissions import permissions_for
from .provider import AuthenticatedIdentity
from ..models.base import utcnow


@dataclass
class CurrentUser:
    user_id: int
    upn: str
    display_name: str
    email: str | None
    roles: set[str]
    permissions: set[str]
    scope_regions: set[str]
    scope_business_units: set[str]
    scope_entity_ids: set[int]
    unscoped: bool

    def can(self, permission: str) -> bool:
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        return role in self.roles


def provision_user(identity: AuthenticatedIdentity, group_role_map: dict) -> AppUser:
    """Create or refresh the AppUser row on sign-in. Everyone gets Submitter."""
    user = db.session.scalar(
        select(AppUser).where(AppUser.UserPrincipalName == identity.user_principal_name)
    )
    if user is None:
        user = AppUser(
            ObjectId=identity.object_id,
            UserPrincipalName=identity.user_principal_name,
            DisplayName=identity.display_name,
            Email=identity.email,
            JobTitle=identity.job_title,
            Department=identity.department,
        )
        db.session.add(user)
        db.session.flush()
        _grant(user, RoleName.SUBMITTER, granted_by="system:jit-provision")
    else:
        user.ObjectId = identity.object_id or user.ObjectId
        user.DisplayName = identity.display_name or user.DisplayName
        user.Email = identity.email or user.Email

    for group_id in identity.group_ids:
        mapped = group_role_map.get(group_id)
        if mapped:
            _grant(user, mapped, granted_by=f"entra:group:{group_id}")

    user.LastLoginUtc = utcnow()
    db.session.commit()
    return user


def _grant(user: AppUser, role_name: str, granted_by: str) -> None:
    role = db.session.scalar(select(Role).where(Role.RoleName == role_name))
    if role is None:
        return
    existing = any(ra.RoleId == role.RoleId and ra.IsActive for ra in user.role_assignments)
    if not existing:
        db.session.add(UserRole(UserId=user.UserId, RoleId=role.RoleId,
                                GrantedBy=granted_by, IsActive=True))


def load_current_user() -> CurrentUser | None:
    """Populate g.current_user from the session for each request."""
    user_id = session.get("user_id")
    if not user_id:
        return None

    user = db.session.get(AppUser, user_id)
    if user is None or not user.IsActive:
        return None

    roles = user.role_names
    regions, units, entities = set(), set(), set()
    unscoped = False
    for ra in user.role_assignments:
        if not ra.IsActive:
            continue
        if not (ra.ScopeRegion or ra.ScopeBusinessUnit or ra.ScopeEntityId):
            unscoped = True
        if ra.ScopeRegion:
            regions.add(ra.ScopeRegion)
        if ra.ScopeBusinessUnit:
            units.add(ra.ScopeBusinessUnit)
        if ra.ScopeEntityId:
            entities.add(ra.ScopeEntityId)

    current = CurrentUser(
        user_id=user.UserId,
        upn=user.UserPrincipalName,
        display_name=user.DisplayName,
        email=user.Email,
        roles=roles,
        permissions=permissions_for(roles),
        scope_regions=regions,
        scope_business_units=units,
        scope_entity_ids=entities,
        unscoped=unscoped or RoleName.COMPLIANCE_ADMIN in roles or RoleName.SYSTEM_ADMIN in roles,
    )
    g.current_user = current
    return current
