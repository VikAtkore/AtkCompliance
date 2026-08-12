"""SQL-backed identity and role model.

Entra ID authenticates the user; SQL authorizes them. AppUser rows are
provisioned on first successful sign-in (just-in-time) and roles are granted
by a ComplianceAdmin or SystemAdmin, optionally scoped to a region, business
unit, or entity.
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..extensions import db
from .base import TimestampMixin, utcnow


class AppUser(db.Model, TimestampMixin):
    __tablename__ = "AppUser"

    UserId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ObjectId: Mapped[str | None] = mapped_column(String(64), unique=True)  # Entra oid
    UserPrincipalName: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    DisplayName: Mapped[str] = mapped_column(String(255), nullable=False)
    Email: Mapped[str | None] = mapped_column(String(255))
    Department: Mapped[str | None] = mapped_column(String(255))
    JobTitle: Mapped[str | None] = mapped_column(String(255))
    ManagerUpn: Mapped[str | None] = mapped_column(String(255))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    LastLoginUtc: Mapped[datetime | None] = mapped_column(DateTime)

    role_assignments: Mapped[list["UserRole"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def role_names(self) -> set[str]:
        return {ra.role.RoleName for ra in self.role_assignments if ra.IsActive}

    def has_role(self, name: str) -> bool:
        return name in self.role_names


class Role(db.Model):
    __tablename__ = "Role"

    RoleId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RoleName: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    Description: Mapped[str | None] = mapped_column(String(500))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    assignments: Mapped[list["UserRole"]] = relationship(back_populates="role")


class UserRole(db.Model, TimestampMixin):
    """Role grant, optionally scoped. A NULL scope column means 'all values'."""
    __tablename__ = "UserRole"
    __table_args__ = (
        UniqueConstraint("UserId", "RoleId", "ScopeRegion", "ScopeBusinessUnit",
                         "ScopeEntityId", name="UQ_UserRole_Scope"),
        Index("IX_UserRole_User", "UserId", "IsActive"),
    )

    UserRoleId: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    UserId: Mapped[int] = mapped_column(ForeignKey("AppUser.UserId"), nullable=False)
    RoleId: Mapped[int] = mapped_column(ForeignKey("Role.RoleId"), nullable=False)
    ScopeRegion: Mapped[str | None] = mapped_column(String(255))
    ScopeBusinessUnit: Mapped[str | None] = mapped_column(String(255))
    ScopeEntityId: Mapped[int | None] = mapped_column(ForeignKey("EntityMaster.EntityId"))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    GrantedBy: Mapped[str | None] = mapped_column(String(255))
    GrantedUtc: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    user: Mapped[AppUser] = relationship(back_populates="role_assignments")
    role: Mapped[Role] = relationship(back_populates="assignments")
