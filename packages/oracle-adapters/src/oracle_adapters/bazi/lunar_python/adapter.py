from __future__ import annotations

from lunar_python import Solar


def execute(value: dict) -> dict:
    year, month, day = map(int, value["local_date"].split("-"))
    hour, minute, second = map(int, value["local_time"].split(":"))
    eight = Solar.fromYmdHms(year, month, day, hour, minute, second).getLunar().getEightChar()
    return {
        "pillars": {
            "year": eight.getYear(),
            "month": eight.getMonth(),
            "day": eight.getDay(),
            "hour": eight.getTime(),
        },
        "execution_status": "success",
        "unsupported_features": _unsupported(value["profile_id"]),
        "warnings": _warnings(value["profile_id"]),
    }


def _unsupported(profile_id: str) -> list[str]:
    if profile_id.endswith("DUAL_SPLIT_ZI.CANDIDATE.V1"):
        return ["dual_split_zi_tracks"]
    return []


def _warnings(profile_id: str) -> list[str]:
    if "APPARENT_ZICHU" in profile_id:
        return ["adapter_compares_supplied_wall_time; solar correction is engine-owned"]
    return []


def normalize(raw: dict) -> dict:
    return {"pillars": dict(raw["pillars"])}
