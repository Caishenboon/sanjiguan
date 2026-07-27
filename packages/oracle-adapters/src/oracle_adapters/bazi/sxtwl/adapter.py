from __future__ import annotations

import sxtwl

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def _name(gz) -> str:
    return STEMS[gz.tg] + BRANCHES[gz.dz]


def execute(value: dict) -> dict:
    year, month, day = map(int, value["local_date"].split("-"))
    hour = int(value["local_time"].split(":")[0])
    solar_day = sxtwl.fromSolar(year, month, day)
    return {
        "pillars": {
            "year": _name(solar_day.getYearGZ(True)),
            "month": _name(solar_day.getMonthGZ()),
            "day": _name(solar_day.getDayGZ()),
            "hour": _name(solar_day.getHourGZ(hour)),
        },
        "execution_status": "success",
        "unsupported_features": (
            ["dual_split_zi_tracks"]
            if value["profile_id"].endswith("DUAL_SPLIT_ZI.CANDIDATE.V1")
            else []
        ),
        "warnings": ["sxtwl hour API accepts integer civil hour"],
    }


def normalize(raw: dict) -> dict:
    return {"pillars": dict(raw["pillars"])}
