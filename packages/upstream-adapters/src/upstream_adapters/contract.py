from __future__ import annotations

from copy import deepcopy
from typing import Any

from sanji_engine.canonical import content_hash

ADAPTER_CONTRACT_VERSION = "sanji-upstream-adapter/1.0.0"


def result_envelope(*, definition: dict, adapter_version: str, method_profile: dict,
                    canonical_input: dict, output: dict, warnings: list[str],
                    disputes: list[dict], trace: list[dict], raw: dict,
                    ruleset_version: str | None = None,
                    supporting_evidence: list | None = None,
                    counter_evidence: list | None = None) -> dict:
    core = {
        "schema_version": ADAPTER_CONTRACT_VERSION,
        "upstream_name": definition["name"],
        "upstream_version": definition["version"],
        "upstream_commit": definition["commit"],
        "license": definition["license"],
        "adapter_version": adapter_version,
        "method_profile": deepcopy(method_profile),
        "canonical_input": deepcopy(canonical_input),
        "output": deepcopy(output),
        "warnings": list(warnings),
        "disputes": deepcopy(disputes),
        "trace": deepcopy(trace),
        "raw_hash": content_hash(raw),
    }
    if ruleset_version is not None:
        core["ruleset_version"] = ruleset_version
        core["supporting_evidence"] = deepcopy(supporting_evidence or [])
        core["counter_evidence"] = deepcopy(counter_evidence or [])
    return {**core, "canonical_hash": content_hash(core)}


def dataclass_dict(value: Any) -> dict:
    return {name: getattr(value, name) for name in value.__dataclass_fields__}
