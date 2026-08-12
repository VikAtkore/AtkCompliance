from flask import Blueprint

bp = Blueprint("certifications", __name__, url_prefix="/certifications")

from . import routes  # noqa: E402,F401
