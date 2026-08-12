"""Auth blueprint: login, callback, logout, whoami."""
import secrets
from urllib.parse import urljoin
from flask import (Blueprint, current_app, g, jsonify, redirect, request,
                   session, url_for)
from .entra_provider import build_provider
from .provider import AuthError
from .identity import provision_user
from .decorators import login_required
from ..services.audit_service import AuditService
from ..constants import AuditAction

bp = Blueprint("auth", __name__, url_prefix="/auth")


def _redirect_uri() -> str:
    return urljoin(request.host_url, current_app.config["ENTRA_REDIRECT_PATH"].lstrip("/"))


@bp.get("/login")
def login():
    provider = build_provider(current_app.config)
    state = secrets.token_urlsafe(24)
    session["auth_state"] = state
    session["post_login_next"] = request.args.get("next") or "/"
    return redirect(provider.build_login_url(state, _redirect_uri()))


@bp.route("/callback", methods=["GET", "POST"])
def callback():
    provider = build_provider(current_app.config)
    args = request.values.to_dict()

    expected = session.pop("auth_state", None)
    if not expected or args.get("state") != expected:
        return jsonify(error="invalid_state"), 400

    try:
        identity = provider.complete_login(args, _redirect_uri())
    except AuthError as exc:
        current_app.logger.warning("Sign-in failed: %s", exc)
        return jsonify(error="authentication_failed"), 401

    user = provision_user(identity, current_app.config.get("ENTRA_GROUP_ROLE_MAP", {}))
    session.clear()
    session["user_id"] = user.UserId
    session.permanent = True

    AuditService.record(entity_name="AppUser", entity_key=str(user.UserId),
                        action=AuditAction.LOGIN, actor=user.UserPrincipalName)
    return redirect(session.pop("post_login_next", "/") or "/")


@bp.get("/logout")
def logout():
    provider = build_provider(current_app.config)
    session.clear()
    return redirect(provider.build_logout_url(
        current_app.config.get("ENTRA_POST_LOGOUT_URI") or request.host_url))


@bp.get("/me")
@login_required
def me():
    u = g.current_user
    return jsonify(
        userId=u.user_id, userPrincipalName=u.upn, displayName=u.display_name,
        email=u.email, roles=sorted(u.roles), permissions=sorted(u.permissions),
        scope={"regions": sorted(u.scope_regions),
               "businessUnits": sorted(u.scope_business_units),
               "entityIds": sorted(u.scope_entity_ids),
               "unscoped": u.unscoped},
    )
