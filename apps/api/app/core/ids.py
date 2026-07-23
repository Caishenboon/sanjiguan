"""Application-generated UUIDv7 identifiers (RFC 9562 layout)."""
from __future__ import annotations

import secrets
import time
import uuid


def uuid7(now_ms: int | None = None) -> uuid.UUID:
    timestamp = int(time.time_ns() // 1_000_000 if now_ms is None else now_ms)
    if not 0 <= timestamp < 1 << 48:
        raise ValueError("UUIDv7 timestamp must fit in 48 bits")
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    value = timestamp << 80
    value |= 0x7 << 76
    value |= rand_a << 64
    value |= 0b10 << 62
    value |= rand_b
    return uuid.UUID(int=value)
