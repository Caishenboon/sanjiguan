from __future__ import annotations

from .canonical import content_hash


def disabled_result(module_id: str, definition: dict) -> dict:
    result = {
        "module_id": module_id,
        "module_version": "0.1.0",
        "method_id": definition["method_id"],
        "method_status": "disabled",
        "error": {
            "code": "MODULE_DISABLED",
            "message": "method is not frozen and no temporary calculation is permitted",
        },
        "result": None,
        "blocked_by": ["METHOD_UNCONFIRMED", "AUTHORITATIVE_GOLDEN_CASES_REQUIRED"],
        "trace_step_ids": [],
        "rule_refs": [],
        "source_refs": [],
        "uncertainties": ["UNCONFIRMED"],
        "sensitivity_flags": [],
    }
    return {**result, "content_hash": content_hash(result)}
