"""Select an AuditLog implementation from settings (lazy imports keep the core dep-free)."""
from __future__ import annotations

from fanar.audit.log import AuditLog
from fanar.config import Settings


def build_audit_log(settings: Settings) -> AuditLog:
    if settings.env == "test" or not settings.db_dsn:
        from fanar.audit.log import InMemoryAuditLog
        return InMemoryAuditLog()
    from sqlalchemy import create_engine

    from fanar.audit.pg_audit_log import SqlAlchemyAuditLog
    engine = create_engine(settings.db_dsn, future=True, pool_pre_ping=True)
    return SqlAlchemyAuditLog(engine)
