"""projection read models + the outbox NOTIFY trigger

Revision ID: 0002_projections
Revises: 0001_create_events
Create Date: 2026-10-20
"""
from __future__ import annotations

from alembic import op

revision = "0002_projections"
down_revision = "0001_create_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE positions (
            fund             text    NOT NULL,
            instrument       text    NOT NULL,
            quantity         numeric NOT NULL DEFAULT 0,
            updated_sequence bigint  NOT NULL,
            PRIMARY KEY (fund, instrument)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE projection_checkpoints (
            projector     text   PRIMARY KEY,
            last_sequence bigint NOT NULL DEFAULT 0
        )
        """
    )

    # Outbox fan-out: NOTIFY on commit of an event insert, so LISTENers wake immediately.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fanar_events_notify() RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify('fanar_events', NEW.sequence::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute(
        """
        CREATE TRIGGER events_notify
        AFTER INSERT ON events
        FOR EACH ROW EXECUTE FUNCTION fanar_events_notify()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS events_notify ON events")
    op.execute("DROP FUNCTION IF EXISTS fanar_events_notify()")
    op.execute("DROP TABLE IF EXISTS projection_checkpoints")
    op.execute("DROP TABLE IF EXISTS positions")
