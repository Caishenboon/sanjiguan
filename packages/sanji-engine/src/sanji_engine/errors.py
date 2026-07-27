from __future__ import annotations


class EngineError(ValueError):
    """Stable, transport-independent engine error."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def as_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


MODULE_DISABLED = "MODULE_DISABLED"
SCHEMA_UNSUPPORTED = "SCHEMA_UNSUPPORTED"
INPUT_INVALID = "INPUT_INVALID"
RULESET_NOT_FOUND = "RULESET_NOT_FOUND"
RULESET_HASH_MISMATCH = "RULESET_HASH_MISMATCH"
NONDETERMINISTIC_CONTEXT = "NONDETERMINISTIC_CONTEXT"
REPLAY_ASSET_MISSING = "REPLAY_ASSET_MISSING"
REPLAY_INPUT_MISMATCH = "REPLAY_INPUT_MISMATCH"
REPLAY_DATA_VERSION_MISMATCH = "REPLAY_DATA_VERSION_MISMATCH"
REPLAY_METHOD_VERSION_MISMATCH = "REPLAY_METHOD_VERSION_MISMATCH"
REPLAY_RESULT_MISMATCH = "REPLAY_RESULT_MISMATCH"
RULESET_REVOKED = "RULESET_REVOKED"
