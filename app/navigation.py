"""Navigation model.

Declared server-side so the menu is a function of the signed-in user's
permissions, not of template logic. Phase 2 templates render this structure;
Phase 1 exposes it at GET /api/navigation so the shape can be reviewed now.
"""
from .auth.permissions import P

NAVIGATION = [
    {"key": "home", "label": "Home", "icon": "house", "route": "/",
     "permission": None},
    {"key": "my-certifications", "label": "My Certifications", "icon": "file-check",
     "route": "/certifications", "permission": P.SUBMISSION_VIEW_OWN,
     "children": [
         {"key": "start", "label": "Start Certification", "route": "/certifications/new",
          "permission": P.SUBMISSION_CREATE},
         {"key": "drafts", "label": "Drafts", "route": "/certifications?status=Draft",
          "permission": P.SUBMISSION_VIEW_OWN},
         {"key": "submitted", "label": "Submitted",
          "route": "/certifications?status=Submitted", "permission": P.SUBMISSION_VIEW_OWN},
     ]},
    {"key": "review", "label": "Review Center", "icon": "clipboard-check",
     "route": "/review", "permission": P.REPORT_VIEW,
     "children": [
         {"key": "queue", "label": "Submission Queue", "route": "/review/queue",
          "permission": P.REPORT_VIEW},
         {"key": "exceptions", "label": "Exceptions", "route": "/review/exceptions",
          "permission": P.REPORT_VIEW},
         {"key": "missing", "label": "Missing Submissions", "route": "/review/missing",
          "permission": P.REPORT_VIEW_MISSING},
         {"key": "export", "label": "Export", "route": "/review/export",
          "permission": P.REPORT_EXPORT},
     ]},
    {"key": "admin", "label": "Admin Center", "icon": "gear", "route": "/admin",
     "permission": P.PERIOD_MANAGE,
     "children": [
         {"key": "periods", "label": "Certification Periods", "route": "/admin/periods",
          "permission": P.PERIOD_MANAGE},
         {"key": "entities", "label": "Entity Master", "route": "/admin/entities",
          "permission": P.ENTITY_MANAGE},
         {"key": "refdocs", "label": "Reference Documents", "route": "/admin/documents",
          "permission": P.REFDOC_MANAGE},
         {"key": "reminders", "label": "Reminders", "route": "/admin/reminders",
          "permission": P.REMINDER_MANAGE},
         {"key": "roles", "label": "Users & Roles", "route": "/admin/roles",
          "permission": P.ROLE_MANAGE},
         {"key": "audit", "label": "Audit Log", "route": "/admin/audit",
          "permission": P.AUDIT_VIEW},
     ]},
    {"key": "system", "label": "System", "icon": "server", "route": "/system",
     "permission": P.CONFIG_VIEW,
     "children": [
         {"key": "migration", "label": "Legacy Migration", "route": "/system/migration",
          "permission": P.MIGRATION_RUN},
         {"key": "jobs", "label": "Background Jobs", "route": "/system/jobs",
          "permission": P.JOB_MANAGE},
         {"key": "health", "label": "Health", "route": "/system/health",
          "permission": P.HEALTH_DETAIL},
     ]},
]


def visible_navigation(current_user) -> list[dict]:
    """Prune the tree to what this user may actually reach."""
    def allowed(node) -> bool:
        permission = node.get("permission")
        return permission is None or (current_user and current_user.can(permission))

    result = []
    for node in NAVIGATION:
        if not allowed(node):
            continue
        item = {k: v for k, v in node.items() if k != "children"}
        children = [c for c in node.get("children", []) if allowed(c)]
        if children:
            item["children"] = children
        result.append(item)
    return result
