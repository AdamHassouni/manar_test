"""Audit log — append-only record of who did what, when. Separate from the IBOR business ledger.

`log` is the stdlib core (entry + in-memory log, unit-tested); `pg_audit_log`/`schema` are the
Postgres adapter; `factory` selects between them.
"""
