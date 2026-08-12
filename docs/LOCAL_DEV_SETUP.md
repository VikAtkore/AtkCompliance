# Local Development Setup — Windows + VS Code

Runs the portal on `http://localhost:5000` with **no SQL Server, no Entra registration, and no SharePoint access**. Local mode uses a SQLite file and a stub sign-in so you can exercise the API before any tenant configuration exists.

Repository: `github.com/VikAtkore/AtkCompliance`

---

## 1. Prerequisites

| Tool | Check | If missing |
|---|---|---|
| Python 3.11 or 3.12 | `python --version` | python.org installer, or Microsoft Store. Tick **Add python.exe to PATH** |
| Git | `git --version` | git-scm.com |
| VS Code + Python extension | — | Extensions → search "Python" (Microsoft) |

If your laptop blocks installers, Python from the Microsoft Store usually works without admin rights.

---

## 2. Clone and open

```powershell
cd %USERPROFILE%\source\repos
git clone https://github.com/VikAtkore/AtkCompliance.git
cd AtkCompliance
code .
```

If the Flask project sits in a subfolder of the repo, `cd` into that folder — every command below runs from the folder containing `requirements.txt`.

---

## 3. Virtual environment

In the VS Code terminal (**Ctrl + `**):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

That change applies only to the current terminal — it is not a machine-wide policy change, which matters on a managed work laptop.

You should now see `(.venv)` at the start of the prompt. Then point VS Code at it: **Ctrl+Shift+P → Python: Select Interpreter → .venv**.

---

## 4. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Behind the corporate proxy, if pip cannot reach PyPI:

```powershell
pip install -r requirements-dev.txt --proxy http://your.proxy:8080
```

or, if Atkore runs an internal package mirror:

```powershell
pip install -r requirements-dev.txt --index-url https://your-internal-mirror/simple --trusted-host your-internal-mirror
```

`pyodbc` is deliberately **not** in `requirements.txt` — it needs the Microsoft ODBC driver installed and is only required when you point at real SQL Server. See section 9.

---

## 5. Environment file

```powershell
copy .env.development.example .env
```

Defaults are already correct for local work: SQLite, stub auth signing you in as `vpandey@atkore.com`, reminders in dry-run, scheduler off. `.env` is git-ignored — real secrets never reach the repository.

---

## 6. Create the local database

```powershell
$env:FLASK_APP = "run.py"
flask dev-init
```

Expected output:

```
Database: sqlite+pysqlite:///C:\atkore_compliance\instance\atkore_compliance_dev.db
Instance folder: C:\atkore_compliance\instance
Local database ready. Signed-in dev user: vpandey@atkore.com (all four roles).
```

This creates `instance\atkore_compliance_dev.db` and loads: the 4 roles, 2 certification periods (Q1 2026 open, Q4 2025 closed with 404 enabled), 3 entities (one Group 2, two Group 1), a reminder template and milestone, and your dev user holding all four roles so every endpoint is reachable.

**Note:** `dev-init` uses `create_all()`, not `flask db upgrade`. The Alembic migrations target SQL Server (`SYSUTCDATETIME()`, BIGINT IDENTITY) and will not run on SQLite. Use `flask db upgrade` only against real SQL Server — section 9.

To start over: delete `instance\atkore_compliance_dev.db` and re-run `flask dev-init`.

**Do not prefix `ACC_DATABASE_URI` with `instance/`.** Flask-SQLAlchemy already
resolves a relative SQLite filename against the instance folder; adding the
prefix nests it twice (`instance\instance\...`) and fails with
`unable to open database file`.

---

## 7. Run it

**Option A — VS Code debugger (recommended).** Press **F5**, choose *Flask: run local (SQLite + dev auth)*. Breakpoints work in services and routes.

**Option B — terminal.**

```powershell
flask run --port 5000 --debug
```

Then in a browser:

| URL | Expect |
|---|---|
| `http://localhost:5000/health` | `{"status":"ok","database":"ok"}` |
| `http://localhost:5000/auth/login` | Signs you straight in (dev stub), redirects to `/` |
| `http://localhost:5000/auth/me` | Your identity, 4 roles, 30 permissions |
| `http://localhost:5000/api/navigation` | Full menu tree — all five areas |
| `http://localhost:5000/api/lookup/entities` | The 3 seeded entities |

`/` returns `{"error":"not_found"}` — correct for Phase 1. There are no pages yet; that is Phase 2.

---

## 8. Exercise the API

Sign in first so the browser holds a session cookie (`/auth/login`), then use the browser for GETs. For POSTs, PowerShell keeps the session:

```powershell
$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-RestMethod "http://localhost:5000/auth/login" -WebSession $s | Out-Null

# Start a draft against the open Q1 2026 period, Mokena (Group 2)
$body = @{ periodId = 1; entityId = 1; employeeName = "Vikash Pandey"
           preparerRole = "Controller" } | ConvertTo-Json
$draft = Invoke-RestMethod "http://localhost:5000/api/submissions" -Method Post `
         -Body $body -ContentType "application/json" -WebSession $s
$draft.submissionId

# 10 questions + the $450,000 Group 2 threshold question were seeded
$draft.responses | Select questionCode, questionText

# Try to submit with nothing filled in -- expect 422 with the full issue list
Invoke-RestMethod "http://localhost:5000/api/submissions/$($draft.submissionId)/submit" `
  -Method Post -WebSession $s
```

That last call failing with **422** is the system working: it proves the "Yes requires explanation" and acknowledgement rules are enforced server-side, not in the UI.

To test role scoping, sign in as someone else — `http://localhost:5000/auth/login?upn=reviewer@atkore.com` — then grant roles:

```powershell
flask grant-role reviewer@atkore.com Reviewer
```

The new user starts with **Submitter** only (JIT provisioning), so `/api/reports/submissions` returns 403 until you grant Reviewer. That is the permission matrix working end to end.

---

## 9. Optional: run against real SQL Server

Only needed when you want to validate the actual migrations and the production driver.

1. Install **Microsoft ODBC Driver 18 for SQL Server**, and SQL Server Express LocalDB (or point at a dev instance).
2. `pip install -r requirements-sqlserver.txt`
3. In `.env`:

```
ACC_DATABASE_URI=mssql+pyodbc://@(localdb)\MSSQLLocalDB/AtkoreCompliance?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

4. Create the database, then:

```powershell
flask db upgrade      # runs 0001 baseline + 0002 seed
flask seed-roles
```

This is the path that validates the migrations actually apply — worth doing once before Phase 2.

---

## 10. Tests

```powershell
$env:ACC_ENV = "testing"
pytest -v
```

22 tests: validation rules, status transitions, the permission matrix, and legacy XML parsing. They run on in-memory SQLite and need no configuration. In VS Code, the Testing panel picks them up automatically.

---

## 11. Useful commands

| Command | Purpose |
|---|---|
| `flask list-routes` | Print every registered endpoint |
| `flask dev-init` | Create/refresh the local database and sample data |
| `flask grant-role <upn> <role>` | Grant a portal role locally |
| `flask seed-roles` | Insert the four roles (idempotent) |
| `flask run-reminders` | Run the reminder job once (dry-run by default) |
| `flask db upgrade` | Apply migrations — SQL Server only |

---

## 12. Git workflow

```powershell
git checkout -b phase1-foundation
git add .
git commit -m "Phase 1: architecture foundation"
git push -u origin phase1-foundation
```

`.gitignore` already excludes `.venv/`, `.env`, `instance/`, `*.db`, `logs/`, and `__pycache__/`. **Confirm `.env` is not staged before your first push** — `git status` should never list it.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: flask` | venv not active | `.\.venv\Scripts\Activate.ps1`, re-select the interpreter |
| `Could not locate a Flask application` | `FLASK_APP` unset | `$env:FLASK_APP = "run.py"` |
| `Activate.ps1 cannot be loaded` | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `unable to open database file` | `ACC_DATABASE_URI` contains an `instance/` prefix, so the path nests twice | Set it to `sqlite+pysqlite:///atkore_compliance_dev.db` (no folder prefix), delete any stray `instance\instance\` folder, re-run `flask dev-init` |
| `no such table: Role` | Database not initialized | `flask dev-init` |
| 401 on every API call | No session cookie | Visit `/auth/login` first |
| 403 with `missing_permissions` | Role not granted | `flask grant-role <upn> <role>` |
| `SYSUTCDATETIME` error on `flask db upgrade` | Migrations run against SQLite | Use `flask dev-init` locally; migrations are SQL Server only |
| Port 5000 in use | Another process | `flask run --port 5001` |
| pip SSL/proxy errors | Corporate proxy | Use `--proxy` or the internal mirror (section 4) |
