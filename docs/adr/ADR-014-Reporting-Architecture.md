Status: Proposed

Context
-------
The project contains a `reports` blueprint (`app/reports/routes.py`) and a `reporting_service.py` under `app/services/`. Current templates include placeholder report pages under `app/templates/reports/`.

Decision
--------
Adopt a hybrid reporting architecture that supports:

- Operational reports served via the primary application (fast, cached SQL queries exposed through `/reports` and `/api/reports`).
- Analytical or cross-system reports produced by scheduled ETL jobs that populate a read-optimized reporting schema or data warehouse.

Implementation Recommendations
--------------------------
- Keep the canonical domain in the normalized OLTP schema. Implement report queries as service methods under `app/services/reporting_service.py` and expose lightweight JSON endpoints for UI consumption.
- Use parameterized SQLAlchemy Core queries or raw SQL for complex groupings to preserve performance and index usage.
- Add a reporting schema (e.g., `reporting_*` tables or a separate database) populated by background jobs that run nightly/weekly; store pre-aggregated metrics and time-series for dashboards.
- Implement caching for frequently requested dashboard data (Redis or in-process caching for low-scale deployments).
- Provide CSV/Excel exports for auditors and stakeholders; implement streaming responses for large resultsets.

Consequences
------------
- Online reports remain responsive for day-to-day usage while heavy analytical queries run asynchronously.
- Maintenance of ETL jobs and a reporting schema increases operational work but provides predictable performance for analytics.

Alternatives Considered
-----------------------
- Ad-hoc reporting directly against OLTP with no ETL — acceptable for small datasets but risks performance problems as volume grows.
