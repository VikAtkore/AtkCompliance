Status: Proposed

Context
-------
The codebase includes `app/reminders/routes.py`, `app/services/reminder_service.py`, and `app/jobs.py` which indicate scheduled/async work for reminders. There is no explicit external queue or scheduler configuration currently checked in.

Decision
--------
Implement a robust reminder/notification architecture with a scheduler, durable queue, and pluggable delivery providers (email, Graph notifications, webhook).

Implementation Recommendations
--------------------------
- Use a background worker architecture: pick either Celery with Redis/RabbitMQ or APScheduler + a small durable queue depending on operational constraints. For Windows-first environments, `APScheduler` or a hosted Azure Function timer + queue is a practical choice.
- Keep a `Notification` entity in the schema that records intended sends, status (pending/sent/failed), retries, and last error.
- Implement `ReminderService` responsible for calculating due reminders and enqueuing `Notification` jobs.
- Workers will process notification jobs, call delivery providers (SMTP, Microsoft Graph mail/send, or Teams webhook), and update `Notification` status and `logs` for auditability.
- Implement exponential backoff and dead-letter handling for failed deliveries.

Consequences
------------
- Durable queuing ensures no reminders are lost and makes retrying reliable.
- Operational complexity increases (queue, worker processes), but reliability and observability improve.

Alternatives Considered
-----------------------
- Fire-and-forget reminders from the web process — simplest but fragile under load and restarts; rejected.
