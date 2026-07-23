"""Fail-closed merge for prose-only LLM fixture output. No provider calls."""

from copy import deepcopy

TOP_LEVEL_ALLOWLIST = {"image_text", "plain_interpretation"}
JUDGEMENT_ALLOWLIST = {"benefit", "risk", "instruction"}


def merge_llm_prose(verdict: dict, llm_fragment: dict) -> dict:
    unknown = set(llm_fragment) - TOP_LEVEL_ALLOWLIST - {"judgement"}
    if unknown:
        raise ValueError(f"llm_attempted_locked_or_unknown_fields:{sorted(unknown)}")
    result = deepcopy(verdict)
    for field in TOP_LEVEL_ALLOWLIST:
        if field in llm_fragment:
            result[field] = llm_fragment[field]
    if "judgement" in llm_fragment:
        if not isinstance(llm_fragment["judgement"], dict):
            raise ValueError("llm_judgement_must_be_object")
        forbidden = set(llm_fragment["judgement"]) - JUDGEMENT_ALLOWLIST
        if forbidden:
            raise ValueError(f"llm_attempted_locked_judgement_fields:{sorted(forbidden)}")
        for field in JUDGEMENT_ALLOWLIST:
            if field in llm_fragment["judgement"]:
                result["judgement"][field] = llm_fragment["judgement"][field]
    return result
