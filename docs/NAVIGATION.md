# Navigation Design

The menu is declared server-side in `app/navigation.py` and pruned per user by `visible_navigation()`. A user never sees a menu item they cannot reach — and the same permission that hides the link also guards the endpoint, so hiding is cosmetic rather than load-bearing.

Exposed now at `GET /api/navigation` so the structure can be reviewed before any template exists.

```
Home                                          all signed-in users
My Certifications                             submission.view.own
  ├── Start Certification                     submission.create
  ├── Drafts                                  submission.view.own
  └── Submitted                               submission.view.own
Review Center                                 report.view            (Reviewer+)
  ├── Submission Queue                        report.view
  ├── Exceptions                              report.view
  ├── Missing Submissions                     report.view.missing
  └── Export                                  report.export
Admin Center                                  admin.period.manage    (ComplianceAdmin+)
  ├── Certification Periods                   admin.period.manage
  ├── Entity Master                           admin.entity.manage
  ├── Reference Documents                     admin.refdoc.manage
  ├── Reminders                               admin.reminder.manage
  ├── Users & Roles                           admin.role.manage
  └── Audit Log                               admin.audit.view
System                                        system.config.view     (SystemAdmin only)
  ├── Legacy Migration                        system.migration.run
  ├── Background Jobs                         system.job.manage
  └── Health                                  system.health.detail
```

## What each role actually sees

| Role | Visible top-level areas |
|---|---|
| Submitter | Home, My Certifications |
| Reviewer | Home, My Certifications, Review Center |
| ComplianceAdmin | Home, My Certifications, Review Center, Admin Center |
| SystemAdmin | All five, including System |

This maps 1:1 to the information architecture in the UI/UX specification — Home Dashboard, Start Certification, Certification Sections, Exception Reporting, Review Center, Admin Center. "Start Certification" and the section/exception steps sit inside the Phase 2 wizard rather than the global menu, because they are steps in a flow, not destinations.

## Phase 2 route map (not built yet)

| Nav route | Wizard step / page |
|---|---|
| `/certifications/new` | Step 1 — quarter, name, business unit, location, preparer role |
| `/certifications/{id}/modules` | Step 2 — select certification types |
| `/certifications/{id}/exceptions` | Step 3 — Group 1 / Group 2 threshold sections |
| `/certifications/{id}/questionnaire` | Step 4 — 302 questionnaire (shown only when selected) |
| `/certifications/{id}/acknowledgements` | Step 5 — acknowledgement panels + document links |
| `/certifications/{id}/review` | Step 6 — validation summary, submit |

Each wizard step is backed by an endpoint that already exists in Phase 1 — the UI adds no new business behaviour.
