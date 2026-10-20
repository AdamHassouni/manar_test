"""create events table — the append-only IBOR ledger

Revision ID: 0001_create_events
Revises:
Create Date: 2026-10-20
"""
from __future__ import annotations

from alembic import op

revision = "0001_create_events"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE events (
            sequence        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            event_id        uuid        NOT NULL,
            type            text        NOT NULL,
            aggregate_id    text        NOT NULL,
            tenant          text        NOT NULL,
            effective_date  date        NOT NULL,     -- valid time
            recorded_at     timestamptz NOT NULL DEFAULT now(),  -- knowledge time
            actor           text,
            correlation_id  text,
            idempotency_key text,
            payload         jsonb       NOT NULL
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX ux_events_event_id ON events (event_id)")
    op.execute(
        "CREATE UNIQUE INDEX ux_events_idempotency ON events (idempotency_key) "
        "WHERE idempotency_key IS NOT NULL"
    )
    op.execute("CREATE INDEX ix_events_aggregate ON events (aggregate_id, sequence)")
    op.execute("CREATE INDEX ix_events_tenant_effective ON events (tenant, effective_date)")

    # Append-only: block UPDATE/DELETE at the database, not just by convention.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fanar_events_append_only() RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'events is append-only (% blocked)', TG_OP;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER events_no_mutate
        BEFORE UPDATE OR DELETE ON events
        FOR EACH ROW EXECUTE FUNCTION fanar_events_append_only()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS events_no_mutate ON events")
    op.execute("DROP FUNCTION IF EXISTS fanar_events_append_only()")
    op.execute("DROP TABLE IF EXISTS events")
