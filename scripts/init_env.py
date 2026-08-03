"""Generate local-only secrets without printing them."""
from __future__ import annotations

import secrets
from pathlib import Path


target = Path(__file__).resolve().parents[1] / ".env"
if target.exists():
    raise SystemExit(".env already exists; refusing to overwrite")

values = {
    "APP_ENV": "development",
    "SANJI_VERSION": "v1-candidate-local",
    "PUBLIC_ORIGIN": "http://127.0.0.1:3000",
    "SESSION_COOKIE_SECURE": "false",
    "POSTGRES_DB": "sanjiguan",
    "POSTGRES_MIGRATION_PASSWORD": secrets.token_urlsafe(32),
    "POSTGRES_APP_PASSWORD": secrets.token_urlsafe(32),
    "KEY_PROVIDER": "env-aesgcm",
    "FIELD_ENCRYPTION_KEY_ID": "local-v1-key",
    "FIELD_ENCRYPTION_KEY_HEX": secrets.token_hex(32),
    "OWNER_BOOTSTRAP_TOKEN": secrets.token_urlsafe(32),
    "DEEPSEEK_API_KEY": "",
    "DEEPSEEK_MODEL": "deepseek-chat",
    "DOMAIN": "localhost",
}
target.write_text(
    "# Generated locally. Never commit this file.\n"
    + "\n".join(f"{key}={value}" for key, value in values.items())
    + "\n",
    encoding="utf-8",
)
print("created ignored .env with generated local secrets")
