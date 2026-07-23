"""RFC 8785 JCS-compatible canonical JSON subset used by engine hash v1.

Hash payloads allow only null, booleans, strings, safe integers, arrays and
objects with string keys. Domain decimals are represented as explicitly scaled
strings before hashing. Binary floats are rejected.
"""
from __future__ import annotations

import hashlib
import json

from .errors import EngineError, INPUT_INVALID

CANONICALIZATION_VERSION = "jcs-rfc8785-subset/1.0.0"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _validate_string(value: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise EngineError(INPUT_INVALID, "unpaired Unicode surrogate is not valid I-JSON")


def _string(value: str) -> str:
    _validate_string(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _key(value: str) -> bytes:
    _validate_string(value)
    return value.encode("utf-16be")


def canonicalize(value) -> bytes:
    def encode(item) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, int):
            if abs(item) > MAX_SAFE_INTEGER:
                raise EngineError(INPUT_INVALID, "integer exceeds the JCS safe-integer profile")
            return str(item)
        if isinstance(item, float):
            raise EngineError(
                INPUT_INVALID,
                "binary floats are forbidden in engine hash payloads; use a scaled decimal string",
            )
        if isinstance(item, str):
            return _string(item)
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(child) for child in item) + "]"
        if isinstance(item, dict):
            if any(not isinstance(key, str) for key in item):
                raise EngineError(INPUT_INVALID, "canonical JSON object keys must be strings")
            parts = [
                _string(key) + ":" + encode(item[key])
                for key in sorted(item, key=_key)
            ]
            return "{" + ",".join(parts) + "}"
        raise EngineError(INPUT_INVALID, f"unsupported canonical JSON type: {type(item).__name__}")

    return encode(value).encode("utf-8")


def content_hash(value) -> str:
    return "sha256:" + hashlib.sha256(canonicalize(value)).hexdigest()
