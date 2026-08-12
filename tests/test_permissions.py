"""Role -> permission matrix."""
from app.auth.permissions import P, permissions_for, ROLE_PERMISSIONS
from app.constants import RoleName


def test_submitter_cannot_reach_admin_functions():
    granted = permissions_for({RoleName.SUBMITTER})
    for permission in (P.PERIOD_MANAGE, P.ENTITY_MANAGE, P.ROLE_MANAGE,
                       P.AUDIT_VIEW, P.REPORT_EXPORT, P.MIGRATION_RUN):
        assert permission not in granted


def test_reviewer_can_export_but_not_administer():
    granted = permissions_for({RoleName.REVIEWER})
    assert P.REPORT_EXPORT in granted
    assert P.SUBMISSION_VIEW_SCOPED in granted
    assert P.PERIOD_MANAGE not in granted
    assert P.SUBMISSION_VIEW_ALL not in granted


def test_compliance_admin_cannot_run_migration():
    granted = permissions_for({RoleName.COMPLIANCE_ADMIN})
    assert P.AUDIT_VIEW in granted
    assert P.MIGRATION_RUN not in granted


def test_system_admin_is_a_superset_of_every_role():
    system = permissions_for({RoleName.SYSTEM_ADMIN})
    for role in RoleName:
        assert permissions_for({role}) <= system


def test_role_hierarchy_is_strictly_increasing():
    order = [RoleName.SUBMITTER, RoleName.REVIEWER, RoleName.COMPLIANCE_ADMIN,
             RoleName.SYSTEM_ADMIN]
    for lower, higher in zip(order, order[1:]):
        assert ROLE_PERMISSIONS[lower] < ROLE_PERMISSIONS[higher]
