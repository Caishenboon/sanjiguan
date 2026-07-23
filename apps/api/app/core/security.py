"""Token hashing and constant-time comparison helpers."""
from __future__ import annotations

import hashlib
import hmac
import secrets


def new_token(bytes_of_entropy: int = 32) -> str:
    return secrets.token_urlsafe(bytes_of_entropy)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def matches_token(token: str, expected_hash: str) -> bool:
    return hmac.compare_digest(token_hash(token), expected_hash)
