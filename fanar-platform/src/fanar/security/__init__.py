"""Security baseline — closes the review findings by construction (docs/03 §3).

  * `secrets`  — no secret in source/FS; Vault-backed in prod (finding #2).
  * `auth`     — Keycloak bearer-JWT validation + RBAC; SPA/BFF does auth-code+PKCE and keeps
                 tokens out of localStorage (findings #1, #4, #5).
"""
