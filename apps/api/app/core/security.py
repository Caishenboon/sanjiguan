"""Token hashing and constant-time comparison helpers."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


def new_token(bytes_of_entropy: int = 32) -> str:
    return secrets.token_urlsafe(bytes_of_entropy)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def matches_token(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(token_hash(token), expected_hash)


def normalized_request_id(candidate: str | None) -> str:
    """Keep correlation IDs log-safe without accepting arbitrary header content."""
    if candidate and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return secrets.token_hex(16)
