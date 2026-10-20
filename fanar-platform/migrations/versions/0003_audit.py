"""audit_entries — append-only audit log

Revision ID: 0003_audit
Revises: 0002_projections
Create Date: 2026-10-20
"""
from __future__ import annotations

from alembic import op

revision = "0003_audit"
down_revision = "0002_projections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE audit_entries (
            sequence       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            id             uuid        NOT NULL,
            actor          text        NOT NULL,
            action         text        NOT NULL,
            target         text        NOT NULL,
            at             timestamptz NOT NULL DEFAULT now(),
            correlation_id text,
            details        jsonb       NOT NULL DEFAULT '{}'::jsonb
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ux_audit_id ON audit_entries (id)")
    op.execute("CREATE INDEX ix_audit_actor_at ON audit_entries (actor, at)")
    # Append-only — reuse the guard function created in migration 0001.
    op.execute(
        """
        CREATE TRIGGER audit_no_mutate
        BEFORE UPDATE OR DELETE ON audit_entries
        FOR EACH ROW EXECUTE FUNCTION fanar_events_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_no_mutate ON audit_entries")
    op.execute("DROP TABLE IF EXISTS audit_entries")
