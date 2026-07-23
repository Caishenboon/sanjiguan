from __future__ import annotations

from typing import Protocol


class Repository(Protocol):
    """Shared storage boundary implemented by memory and PostgreSQL adapters."""

    backend_name: str

    def close(self) -> None: ...


def assert_backend_allowed(app_env: str, backend_name: str) -> None:
    if app_env.lower() in {"production", "prod"} and backend_name == "memory":
        raise RuntimeError("memory_backend_forbidden_in_production")
