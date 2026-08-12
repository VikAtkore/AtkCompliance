Status: Proposed

Context
-------
The models include SQL Server-friendly types and indexing assumptions (e.g., `BigIntPK` in `app/models/base.py` which maps BIGINT to INTEGER for sqlite). The project also contains `requirements-sqlserver.txt`, indicating support for a SQL Server production target. Migration tooling uses Alembic in the `migrations/` folder.

Decision
--------
Target Microsoft SQL Server for production while keeping SQLite for development. Production deployments will use a managed SQL Server instance and Alembic-based migrations (files in `migrations/`). This ADR is proposed until production deployment and configuration are finalized.

Consequences
------------
- Requires production DB configuration, secure connection strings, and migration/backup procedures.
- Developers must validate database-specific behaviors (collations, locking, numeric precisions) against a SQL Server environment prior to production release.

Alternatives Considered
-----------------------
- Postgres or MySQL for production — not selected because existing enterprise environment prefers SQL Server (implied by repository artifacts and `requirements-sqlserver.txt`).
- Keep SQLite in production — rejected for scale, concurrency, and enterprise support reasons.
