"""IBOR — the Investment Book of Record: append-only event log + projections.

The ledger (`event_store`) is the single source of truth; positions, cash and NAV are derived by
folding events (`projections`). This is the spine the whole platform hangs off (docs/03 §1).
"""
