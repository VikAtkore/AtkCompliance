from flask import render_template, current_app, request, jsonify
from . import bp


@bp.get("/new")
def new_certification():
    # The template and client-side JS will load entities and periods via API
    return render_template("certifications/new.html")


@bp.get("")
def list_certifications():
    return render_template("certifications/index.html")
