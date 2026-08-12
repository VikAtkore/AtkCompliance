"""Seed the four fixed roles and a reference copy of the 302 question catalogue.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

ROLES = [
    ("Submitter", "Completes and submits certifications."),
    ("Reviewer", "Reviews submissions and exports reporting within assigned scope."),
    ("ComplianceAdmin", "Manages periods, entities, documents, reminders and roles."),
    ("SystemAdmin", "Manages configuration, migration and operations."),
]

QUESTIONS = [
    ("ORG_CHANGE", "Organizational Changes", 10),
    ("PROCESS_CHANGE", "Significant business process changes", 20),
    ("KEY_PERSONNEL_CHANGE", "Key personnel changes", 30),
    ("SYSTEM_CHANGE", "System changes", 40),
    ("EXTERNAL_AUDIT_FINDING", "External audit findings", 50),
    ("INTERNAL_AUDIT_FINDING", "Internal audit findings", 60),
    ("ACCOUNTING_ADJUSTMENTS", "Accounting adjustments", 70),
    ("FRAUD_INDICATORS", "Fraud indicators", 80),
    ("CONTROL_REMEDIATION", "Control remediation", 90),
    ("CONTROL_DEFICIENCIES", "Identification of control deficiencies", 100),
]


def upgrade():
    role_table = sa.table("Role",
                          sa.column("RoleName", sa.String),
                          sa.column("Description", sa.String),
                          sa.column("IsActive", sa.Boolean))
    op.bulk_insert(role_table, [{"RoleName": n, "Description": d, "IsActive": True}
                                for n, d in ROLES])

    # Question catalogue -- authoritative list of the 10 legacy 302 questions.
    op.create_table(
        "QuestionCatalog",
        sa.Column("QuestionCode", sa.String(100), primary_key=True),
        sa.Column("QuestionText", sa.String(500), nullable=False),
        sa.Column("DisplayOrder", sa.Integer, nullable=False),
        sa.Column("RequiresExplanationWhenYes", sa.Boolean, nullable=False,
                  server_default=sa.text("1")),
        sa.Column("IsActive", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )
    catalog = sa.table("QuestionCatalog",
                       sa.column("QuestionCode", sa.String),
                       sa.column("QuestionText", sa.String),
                       sa.column("DisplayOrder", sa.Integer),
                       sa.column("RequiresExplanationWhenYes", sa.Boolean),
                       sa.column("IsActive", sa.Boolean))
    op.bulk_insert(catalog, [{"QuestionCode": c, "QuestionText": t, "DisplayOrder": o,
                              "RequiresExplanationWhenYes": True, "IsActive": True}
                             for c, t, o in QUESTIONS])


def downgrade():
    op.drop_table("QuestionCatalog")
    op.execute("DELETE FROM Role WHERE RoleName IN "
               "('Submitter','Reviewer','ComplianceAdmin','SystemAdmin')")
