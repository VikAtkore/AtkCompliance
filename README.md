# Atkore Compliance Certification Portal — Phase 1

Replacement for the SharePoint 2013 / InfoPath quarterly compliance certification form.
**Phase 1 = architecture foundation. No UI pages — API, data model, and services only.**

## Architecture decisions applied

- **Authentication:** Microsoft Entra ID via MSAL; SQL-backed role model (Submitter, Reviewer, ComplianceAdmin, SystemAdmin)
- **Attachments:** SharePoint Online via Microsoft Graph; SQL stores metadata and pointers only
- **Data:** SQL Server via SQLAlchemy 2.0 + Flask-Migrate
- **Hosting:** IIS (wfastcgi)

## Layout

```
atkore_compliance/
├── app/
│   ├── __init__.py          application factory, lookups, /health, CLI
│   ├── config-driven modules: constants.py, extensions.py, navigation.py, jobs.py
│   ├── models/              10 operational + 4 staging tables
│   ├── auth/                MSAL provider, identity, permissions, decorators
│   ├── services/            10 services — all business logic
│   ├── submissions/         submission + attachment API
│   ├── admin/               periods, entities, documents, roles, audit
│   ├── reports/             reviewer queue, summary, missing, Excel export
│   ├── reminders/           milestones, recipients, templates, run logs
│   ├── migration/           legacy XML / Vlookup import
│   └── templates/, static/  (empty — Phase 2)
├── migrations/versions/     0001 baseline schema, 0002 roles + question catalogue
├── tests/                   validation, transitions, permissions, XML parsing
├── docs/                    ERD, API inventory, permission matrix, auth, services, config, navigation
├── .vscode/                launch + settings for F5 debugging
├── config.py, run.py, web.config, requirements*.txt, .env*.example
```

## Run locally (Windows + VS Code)

No SQL Server, no Entra registration, no SharePoint needed.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.development.example .env
$env:FLASK_APP = "run.py"
flask dev-init                  # SQLite schema + sample data
flask run --port 5000 --debug
```

Then open `http://localhost:5000/health`, then `/auth/login`, then `/auth/me`.
Full walkthrough incl. proxy, LocalDB and troubleshooting: **`docs/LOCAL_DEV_SETUP.md`**

## Production setup

```powershell
pip install -r requirements.txt -r requirements-sqlserver.txt
copy .env.example .env          # then populate secrets
$env:ACC_ENV = "production"
flask db upgrade                # 0001 baseline + 0002 seed
```

## Verify

```powershell
$env:ACC_ENV = "testing"; pytest
flask list-routes
```

## Documentation

| Document | Contents |
|---|---|
| `docs/ERD.md` | Entity relationship diagrams + cardinality rules |
| `docs/API_INVENTORY.md` | All 46 endpoints with permissions |
| `docs/PERMISSION_MATRIX.md` | Role × permission grid, scoping rules |
| `docs/AUTHENTICATION.md` | Entra flow, app registration, token model |
| `docs/SERVICE_LAYER.md` | Service responsibilities, validation rules, status machine |
| `docs/CONFIGURATION.md` | Every environment variable |
| `docs/NAVIGATION.md` | Menu tree and Phase 2 route map |
| `docs/LOCAL_DEV_SETUP.md` | Windows + VS Code local run, troubleshooting, git workflow |

## Not in Phase 1

Bootstrap templates and the 6-step wizard, the reviewer dashboard UI, the IIS deployment runbook, and the bulk XML extraction script that pulls files out of SharePoint 2013.
