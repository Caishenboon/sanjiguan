from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse


PRODUCTION_ENVS = {"production", "prod"}
WEAK_VALUES = {"", "change-me", "changeme", "password", "secret", "default"}


@dataclass(frozen=True)
class RuntimeConfig:
    app_env: str
    database_url: str
    public_origin: str
    cookie_secure: bool
    key_provider: str
    field_encryption_key_hex: str
    field_encryption_key_id: str
    owner_bootstrap_token: str | None
    version: str

    @property
    def production(self) -> bool:
        return self.app_env in PRODUCTION_ENVS


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"missing_required_config:{name}")
    return value


def load_runtime_config() -> RuntimeConfig:
    app_env = os.environ.get("APP_ENV", "").strip().lower()
    if app_env not in {"test", "development", "production", "prod"}:
        raise RuntimeError("APP_ENV_must_be_explicit")
    database_url = _required("DATABASE_URL")
    public_origin = os.environ.get("PUBLIC_ORIGIN", "http://127.0.0.1:3000").rstrip("/")
    parsed = urlparse(public_origin)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("PUBLIC_ORIGIN_invalid")
    key_provider = os.environ.get("KEY_PROVIDER", "").strip()
    key_hex = os.environ.get(
        "FIELD_ENCRYPTION_KEY_HEX", os.environ.get("TEST_ENCRYPTION_KEY_HEX", "")
    ).strip()
    key_id = os.environ.get("FIELD_ENCRYPTION_KEY_ID", "").strip()
    bootstrap = os.environ.get("OWNER_BOOTSTRAP_TOKEN", "").strip() or None
    cookie_secure = os.environ.get(
        "SESSION_COOKIE_SECURE", "true" if app_env in PRODUCTION_ENVS else "false"
    ).lower() == "true"
    if app_env in PRODUCTION_ENVS:
        if key_provider != "env-aesgcm":
            raise RuntimeError("production_key_provider_must_be_env_aesgcm")
        if len(key_hex) != 64:
            raise RuntimeError("production_field_encryption_key_invalid")
        if key_id.lower() in WEAK_VALUES:
            raise RuntimeError("production_field_encryption_key_id_invalid")
        if parsed.scheme != "https":
            raise RuntimeError("production_PUBLIC_ORIGIN_must_use_https")
        if not cookie_secure:
            raise RuntimeError("production_secure_cookie_required")
        if bootstrap and (len(bootstrap) < 32 or bootstrap.lower() in WEAK_VALUES):
            raise RuntimeError("production_owner_bootstrap_token_weak")
    return RuntimeConfig(
        app_env=app_env,
        database_url=database_url,
        public_origin=public_origin,
        cookie_secure=cookie_secure,
        key_provider=key_provider,
        field_encryption_key_hex=key_hex,
        field_encryption_key_id=key_id,
        owner_bootstrap_token=bootstrap,
        version=os.environ.get("SANJI_VERSION", "v1-candidate"),
    )
