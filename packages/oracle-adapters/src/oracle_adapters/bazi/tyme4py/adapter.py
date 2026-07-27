from __future__ import annotations

from tyme4py.solar import SolarTime


def execute(value: dict) -> dict:
    year, month, day = map(int, value["local_date"].split("-"))
    hour, minute, second = map(int, value["local_time"].split(":"))
    lunar_hour = SolarTime.from_ymd_hms(
        year, month, day, hour, minute, second
    ).get_lunar_hour()
    eight = lunar_hour.get_eight_char()
    names = str(eight).split()
    if len(names) != 4:
        raise ValueError("tyme4py returned an unexpected EightChar representation")
    return {
        "pillars": dict(zip(("year", "month", "day", "hour"), names)),
        "execution_status": "success",
        "unsupported_features": (
            ["dual_split_zi_tracks"]
            if value["profile_id"].endswith("DUAL_SPLIT_ZI.CANDIDATE.V1")
            else []
        ),
        "warnings": (
            ["adapter_compares_supplied_wall_time; solar correction is engine-owned"]
            if "APPARENT_ZICHU" in value["profile_id"]
            else []
        ),
    }


def normalize(raw: dict) -> dict:
    return {"pillars": dict(raw["pillars"])}
