"""Secrets provider — no secret is ever hardcoded or committed (review finding #2).

The app depends on the `SecretsProvider` port; wiring chooses the implementation:
  * `EnvSecretsProvider`   — reads process env (dev only).
  * `VaultSecretsProvider` — HashiCorp Vault (prod); stub here, same interface.
"""
from __future__ import annotations

import os
from typing import Protocol


class SecretNotFound(KeyError):
    pass


class SecretsProvider(Protocol):
    def get(self, name: str) -> str: ...


class EnvSecretsProvider:
    """Dev provider. Reads FANAR_SECRET_<NAME>. Never log the returned values."""

    def __init__(self, environ: dict[str, str] | None = None) -> None:
        self._env = environ if environ is not None else os.environ

    def get(self, name: str) -> str:
        key = f"FANAR_SECRET_{name.upper()}"
        if key not in self._env:
            raise SecretNotFound(name)
        return self._env[key]


class VaultSecretsProvider:
    """Production provider (HashiCorp Vault). Stub: wire hvac in Phase 0 proper."""

    def __init__(self, addr: str, mount: str = "secret", path_prefix: str = "fanar") -> None:
        self.addr = addr
        self.mount = mount
        self.path_prefix = path_prefix

    def get(self, name: str) -> str:  # pragma: no cover - needs a live Vault
        raise NotImplementedError("wire hvac against Vault; read secret/fanar/<name>")


def build_provider(backend: str, *, vault_addr: str = "") -> SecretsProvider:
    if backend == "vault":
        return VaultSecretsProvider(vault_addr)
    return EnvSecretsProvider()
