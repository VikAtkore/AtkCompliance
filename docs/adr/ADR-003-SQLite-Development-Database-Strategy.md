Status: Accepted

Context
-------
The repository configures Flask-SQLAlchemy via `app/extensions.py` and contains logic to ensure local SQLite files exist in `_ensure_local_folders` in `app/__init__.py`. Tests use an in-memory or local SQLite DB created during test setup in `tests/conftest.py` via `_db.create_all()`.

Decision
--------
Use SQLite for local development and testing to minimize setup friction. The application includes defensive code to create the `instance/` folder and directories needed for relative sqlite paths.

Consequences
------------
- Lightweight developer setup: no external database required to run tests or local dev via `dev-init` CLI.
- Some SQL behaviors differ from production (e.g., types, concurrency). The code uses SQLAlchemy variants (`BigIntPK` in `app/models/base.py`) to handle SQLite differences where needed.

Alternatives Considered
-----------------------
- Use SQL Server for all environments — rejected because it increases local setup complexity.
- Use Dockerized SQL Server for dev — viable, but would add setup steps; kept as a future option.
