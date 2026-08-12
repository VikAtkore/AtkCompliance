Status: Accepted

Context
-------
The codebase uses the Flask application factory pattern in `app/__init__.py` (`create_app`), registers blueprints, initializes extensions (`app/extensions.py`), and wires CLI commands in `_register_cli`. Blueprints exist for submissions, admin, reports, migration, reminders, auth, and the new certifications UI. The app separates services under `app/services/` and models under `app/models/`.

Decision
--------
Adopt Flask with an application factory, modular blueprints, and an explicit services layer. Database access is via Flask-SQLAlchemy with a `db` singleton in `app/extensions.py`. Business logic lives in service classes (e.g., `SubmissionService`, `ValidationService`, `ReportingService`) under `app/services/` and is invoked by blueprints in `app/*/routes.py`.

Consequences
------------
- Clear separation of concerns: routes (blueprints) handle HTTP and auth, services contain business rules, models define persistence.
- Testability: `create_app` and fixtures in `tests/conftest.py` create test apps and databases for unit tests.
- Extension initialization and CLI commands are centralized.
- Requires developers to follow the pattern when adding new features (blueprint + service + tests).

Alternatives Considered
-----------------------
- Monolithic single-module Flask app — rejected due to scaling and maintainability concerns.
- Use another Python web framework (Django/FastAPI) — rejected because Flask provides sufficient flexibility and the codebase is already implemented in Flask.
