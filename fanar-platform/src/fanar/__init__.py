"""Fanar — owned Investment Book of Record & operations platform (Phase 0 scaffold).

Layering (keep the dependency arrows pointing inward):
    domain/      pure entities + events          (stdlib only)
    ibor/        append-only event store + projections   (stdlib only)
    acl/guard    read-only guard                 (stdlib only)
    reference/   reference-data service core      (stdlib only)
    security/secrets                               (stdlib only)
    ---- adapters (third-party deps) ----
    acl/manar_client   httpx → Manar (strangler)
    security/auth      pyjwt → Keycloak
    api/               FastAPI web layer

The core is dependency-free so it runs and is unit-tested without any infra. See SKELETON.md.
"""
__version__ = "0.0.1"
