# Permission Matrix

Four roles, 30 distinct permissions, strictly increasing: `Submitter (7) ⊂ Reviewer (14) ⊂ ComplianceAdmin (26) ⊂ SystemAdmin (30)`. This containment is asserted by an automated test.

Legend: ● granted · ○ not granted

| Permission | Submitter | Reviewer | ComplianceAdmin | SystemAdmin |
|---|:--:|:--:|:--:|:--:|
| **Submissions** ||||
| `submission.create` | ● | ● | ● | ● |
| `submission.view.own` | ● | ● | ● | ● |
| `submission.edit.own` | ● | ● | ● | ● |
| `submission.submit` | ● | ● | ● | ● |
| `submission.delete.draft` | ● | ● | ● | ● |
| `submission.view.scoped` | ○ | ● | ● | ● |
| `submission.view.all` | ○ | ○ | ● | ● |
| `submission.edit.any` | ○ | ○ | ● | ● |
| `submission.return` | ○ | ● | ● | ● |
| `submission.accept` | ○ | ● | ● | ● |
| `submission.reopen` | ○ | ○ | ● | ● |
| `submission.archive` | ○ | ○ | ● | ● |
| **Attachments** ||||
| `attachment.upload` | ● | ● | ● | ● |
| `attachment.view.own` | ● | ● | ● | ● |
| `attachment.view.scoped` | ○ | ● | ● | ● |
| `attachment.delete` | ○ | ○ | ● | ● |
| **Reporting** ||||
| `report.view` | ○ | ● | ● | ● |
| `report.export` | ○ | ● | ● | ● |
| `report.view.missing` | ○ | ● | ● | ● |
| **Administration** ||||
| `admin.period.manage` | ○ | ○ | ● | ● |
| `admin.entity.manage` | ○ | ○ | ● | ● |
| `admin.refdoc.manage` | ○ | ○ | ● | ● |
| `admin.reminder.manage` | ○ | ○ | ● | ● |
| `admin.reminder.run` | ○ | ○ | ● | ● |
| `admin.role.manage` | ○ | ○ | ● | ● |
| `admin.audit.view` | ○ | ○ | ● | ● |
| **System** ||||
| `system.migration.run` | ○ | ○ | ○ | ● |
| `system.config.view` | ○ | ○ | ○ | ● |
| `system.job.manage` | ○ | ○ | ○ | ● |
| `system.health.detail` | ○ | ○ | ○ | ● |

## Two deliberate separations of duty

1. **ComplianceAdmin cannot run migration.** Legacy import rewrites system-of-record data; that stays with SystemAdmin so the business owner of the process cannot silently alter imported history.
2. **SystemAdmin inherits business permissions but is expected not to use them.** Every action is attributed in `AuditLog` with the actor's role set, so administrative use of a submitter permission is visible in the audit export rather than invisible.

## Row-level scoping (applies on top of the matrix)

`UserRole` carries three optional scope columns — `ScopeRegion`, `ScopeBusinessUnit`, `ScopeEntityId`.

| Grant | Effective visibility |
|---|---|
| Reviewer, all scope columns NULL | Every submission (unscoped reviewer) |
| Reviewer, `ScopeRegion = 'North America'` | Own submissions + all North America submissions |
| Reviewer, `ScopeBusinessUnit = 'Conduit'` | Own submissions + all Conduit submissions |
| Reviewer, `ScopeEntityId = 42` | Own submissions + entity 42 |
| Multiple grants | Union of all scopes |
| Submitter (any scope) | Own submissions only — scope columns are ignored |

Scoping is enforced in `SubmissionService.scoped_query()`, which every list, report, and export path funnels through. There is no query path to submission data that bypasses it.

## Object-level checks

Permissions alone do not authorize a specific record. `_may_read()` / `_may_write()` in the submissions blueprint additionally verify ownership or scope membership, so a Reviewer scoped to Conduit receives 403 — not an empty result — when requesting an Electrical submission by ID.
