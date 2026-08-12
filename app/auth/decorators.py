"""Route guards. Always check a permission, not a role name."""
from functools import wraps
from flask import g, jsonify, redirect, request, url_for


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if getattr(g, "current_user", None) is None:
            if request.accept_mimetypes.best == "application/json" or request.path.startswith("/api/"):
                return jsonify(error="authentication_required"), 401
            return redirect(url_for("auth.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapper


def require_permission(*permissions: str):
    """Requires ALL listed permissions."""
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            user = g.current_user
            missing = [p for p in permissions if not user.can(p)]
            if missing:
                return jsonify(error="forbidden", missing_permissions=missing), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if not any(g.current_user.can(p) for p in permissions):
                return jsonify(error="forbidden", required_any=list(permissions)), 403
            return view(*args, **kwargs)
        return wrapper
    return decorator
