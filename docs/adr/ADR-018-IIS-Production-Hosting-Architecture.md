Status: Proposed

Context
-------
The application is a Flask Python app intended to run in a Windows environment. The repository includes `web.config` at the project root which suggests IIS hosting scenarios.

Decision
--------
Host the Flask application in production on Windows using a robust WSGI server (Waitress) behind IIS configured as a reverse proxy or using FastCGI (`wfastcgi`) depending on operational preferences.

Implementation Recommendations
--------------------------
- Preferred: Run the Flask app via `waitress` as a Windows service or process and use IIS Application Request Routing (ARR) as a reverse proxy. This separates concerns and allows the WSGI server to manage Python app processes while IIS handles TLS termination and request routing.
- Alternate: Use `wfastcgi` to host the Flask app directly under IIS (supported via the `wfastcgi` adapter) for a tightly integrated setup.
- Configure IIS for TLS, request size limits, and request timeout tuning. Ensure sticky sessions are not relied upon if multiple app processes are used; use server-side session storage (database) or secure cookie sessions.
- Ensure process management (service/supervisor) for the WSGI server and automated restarts on failure.

Consequences
------------
- Using `waitress` + IIS ARR provides a flexible and tested hosting model for Python on Windows with easier operational control.
- `wfastcgi` simplifies deployment but may be harder to scale and debug in complex scenarios.

Alternatives Considered
-----------------------
- Containerize the app and host in Linux-based container hosting (preferred for cross-platform parity) — requires container infrastructure and organizational buy-in.
