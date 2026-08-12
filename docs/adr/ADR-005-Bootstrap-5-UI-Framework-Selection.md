Status: Accepted

Context
-------
The repository uses Bootstrap 5 for UI templates: `app/templates/base.html` references the Bootstrap 5 CDN and multiple templates (index, wizard, placeholders) implement Bootstrap classes and responsive grid layout. The tests render templates via Flask test client and assert presence of expected HTML content.

Decision
--------
Use Bootstrap 5 as the CSS framework for server-rendered templates and components. Templates are kept simple and rely on Bootstrap utilities for responsiveness and layout.

Consequences
------------
- Accelerates UI development with a consistent responsive grid and components.
- Keeps front-end complexity low: minimal JS is embedded in templates for the wizard while Bootstrap handles layout and responsiveness.
- Backend-generated templates are straightforward to test with Flask test client.

Alternatives Considered
-----------------------
- Use a JavaScript SPA framework (React/Vue) — rejected to keep the app server-rendered and simple for Phase 2 UI work.
- Use a different CSS framework — Bootstrap was selected for its wide familiarity and built-in responsive utilities.
