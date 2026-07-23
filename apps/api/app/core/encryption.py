from __future__ import annotations

import os
from typing import Protocol

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class KeyProvider(Protocol):
    production_safe: bool
    def encrypt(self, plaintext: bytes, aad: bytes = b"") -> bytes: ...
    def decrypt(self, ciphertext: bytes, aad: bytes = b"") -> bytes: ...


class TestKeyProvider:
    """AES-GCM provider for tests only; never represents KMS-backed production security."""

    production_safe = False

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("test_key_must_be_32_bytes")
        self._cipher = AESGCM(key)

    def encrypt(self, plaintext: bytes, aad: bytes = b"") -> bytes:
        nonce = os.urandom(12)
        return nonce + self._cipher.encrypt(nonce, plaintext, aad)

    def decrypt(self, ciphertext: bytes, aad: bytes = b"") -> bytes:
        return self._cipher.decrypt(ciphertext[:12], ciphertext[12:], aad)


def assert_key_provider_allowed(app_env: str, provider: KeyProvider) -> None:
    if app_env.lower() in {"production", "prod"} and not provider.production_safe:
        raise RuntimeError("test_key_provider_forbidden_in_production")
