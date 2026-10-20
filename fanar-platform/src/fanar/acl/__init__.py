"""Anti-corruption layer (ACL) — the ONLY component that speaks Manar (docs/02 §3, docs/05 §3).

`guard` is the stdlib, unit-tested read-only enforcement. `manar_client` is the httpx adapter that
applies it. When a domain is fully migrated off Manar, its ACL path is deleted — that's how
strangler progress is measured.
"""
