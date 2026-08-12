Status: Proposed

Context
-------
Development uses SQLite for convenience (`docs/adr/ADR-003...`), but production targets SQL Server (see `requirements-sqlserver.txt` and `docs/adr/ADR-004-Future-SQL-Server-Production-Database-Strategy.md`). Alembic migrations live under `migrations/`.

Decision
--------
Deploy production data to Microsoft SQL Server with SQLAlchemy via `pyodbc` or a supported ODBC driver and manage schema changes with Alembic migration scripts.

Implementation Recommendations
--------------------------
- Use a SQL Server compatible connection string in `config.py` and a tested driver such as `pyodbc` with ODBC Driver 17/18 for SQL Server.
- Configure SQLAlchemy `engine` with appropriate connection pool settings and `fast_executemany=True` for bulk operations when using `pyodbc`.
- Validate all Alembic migrations against a staging SQL Server instance; add a CI job that runs migrations and smoke tests against a transient SQL Server container or ephemeral instance.
- Leverage SQL Server features for production needs: use transactional DDL controls, consider Temporal Tables for auditing (see ADR-020), and tune indexes for reporting queries.
- Secure database connectivity via managed identities or secret stores; avoid embedding credentials in repo or config files.

Consequences
------------
- SQL dialect differences require testing (e.g., boolean handling, limit/offset behavior) and occasional migration script customizations.
- Operational requirements include backups, disaster recovery, and performance monitoring.

Alternatives Considered
-----------------------
- Continue using SQLite in production — not viable for scale or concurrency; rejected.
