from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from lunar_python import Lunar, Solar
from oracle_adapters.ziwei.iztro.adapter import execute as execute_iztro
from oracle_adapters.ziwei.iztro.adapter import normalize as normalize_iztro

from .contract import dataclass_dict, result_envelope
from .complete import bazi_complete, liuyao_complete, ziwei_complete

BAZI = {"name": "6tail/lunar-python", "version": "1.4.8", "commit": "000c8a3d74eed098d6256a28fdd51b869324c559", "license": "MIT"}
ZIWEI = {"name": "SylarLong/iztro", "version": "2.5.8", "commit": "9d39f1743bf31c2b3c635c9b9556215d9c90ee2c", "license": "MIT"}
LIUYAO = {"name": "yaomancy/liuyao-engine", "version": "0.1.0", "commit": "562b902eb3ec47d4dadb326b6dc98e8ee09b4295", "license": "Apache-2.0"}
_VENDORED_HEXAGRAM = None


def _legacy_text(value):
    """Normalize the upstream snapshot's legacy GBK literal encoding."""
    if not isinstance(value, str):
        return value
    try:
        return value.encode("latin1").decode("gbk")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def _profile(value: dict, expected_id: str, expected_version: str) -> dict:
    profile=value.get("method_profile")
    if not isinstance(profile,dict) or profile.get("profile_id")!=expected_id or profile.get("version")!=expected_version:
        raise ValueError(f"explicit supported method profile required: {expected_id}@{expected_version}")
    return profile


class BaziUpstreamAdapter:
    adapter_version = "bazi-upstream-adapter/1.0.0"

    def execute(self, value: dict) -> dict:
        profile=value.get("method_profile", {})
        if profile.get("profile_id") not in {"lunar-python-sect1", "bazi-ziping-complete-v1"}:
            _profile(value,"lunar-python-sect1","1.0.0")
        if profile.get("profile_id") == "bazi-ziping-complete-v1" and profile.get("version") != "1.0.0":
            raise ValueError("bazi-ziping-complete-v1@1.0.0 is required")
        if profile.get("sect") != 1 or profile.get("wall_time_policy") != "supplied_local_wall_time":
            raise ValueError("BaZi upstream profile must explicitly freeze sect=1 and supplied wall time")
        time = value["local_time"]
        hh, mm, ss = map(int, time.split(":"))
        if profile.get("profile_id") == "bazi-ziping-complete-v1" and value.get("calendar_type") == "lunar":
            y,m,d=int(value["lunar_year"]),int(value["lunar_month"]),int(value["lunar_day"])
            lunar=Lunar.fromYmdHms(y,m,d,hh,mm,ss); date=f"{y:04d}-{m:02d}-{d:02d}"; input_calendar="lunar"
        else:
            date=value["local_date"]; y,m,d=map(int,date.split("-")); lunar=Solar.fromYmdHms(y,m,d,hh,mm,ss).getLunar(); input_calendar="solar"
        eight = lunar.getEightChar()
        eight.setSect(profile["sect"])
        pillars = {key: getattr(eight, f"get{key.title()}")() for key in ("year", "month", "day", "time")}
        detail = {}
        for key in ("year", "month", "day", "time"):
            cap = key.title()
            detail[key] = {
                "ganzhi": pillars[key],
                "stem": getattr(eight, f"get{cap}Gan")(),
                "branch": getattr(eight, f"get{cap}Zhi")(),
                "hidden_stems": list(getattr(eight, f"get{cap}HideGan")()),
                "ten_god_stem": getattr(eight, f"get{cap}ShiShenGan")(),
                "ten_gods_hidden": list(getattr(eight, f"get{cap}ShiShenZhi")()),
                "five_elements": getattr(eight, f"get{cap}WuXing")(),
                "nayin": getattr(eight, f"get{cap}NaYin")(),
            }
        output = {"pillars": pillars, "structure": detail, "day_master": eight.getDayGan(),
                  "not_admitted": ["strength", "pattern", "useful_god", "fortune_interpretation"]}
        if profile.get("profile_id") == "bazi-ziping-complete-v1":
            output.update({"input_calendar":input_calendar,
              "time_basis":{"timezone_id":value.get("timezone_id"),"longitude":value.get("longitude"),
                "time_candidate_id":value.get("time_candidate_id"),"correction_minutes":value.get("correction_minutes"),
                "wall_time_policy":profile.get("wall_time_policy")},
              "not_admitted":["unversioned_interpretation","unbounded_exact_event_prediction"]})
        if value.get("traditional_sex") in {"male", "female"}:
            yun = eight.getYun(1 if value["traditional_sex"] == "male" else 0, int(value.get("yun_sect", 1)))
            def annual_entry(year):
                entry = {"year": year.getYear(), "age": year.getAge(), "ganzhi": year.getGanZhi()}
                if profile.get("profile_id") == "bazi-ziping-complete-v1":
                    entry["monthly"] = [
                        {"month": month.getMonthInChinese(), "ganzhi": month.getGanZhi()}
                        for month in year.getLiuYue()
                    ]
                return entry
            output["fortune_cycles"] = {
                "forward": bool(yun.isForward()),
                "start_offset": {"years": yun.getStartYear(), "months": yun.getStartMonth(),
                                 "days": yun.getStartDay(), "hours": yun.getStartHour()},
                "cycles": [{"ganzhi": item.getGanZhi(), "start_year": item.getStartYear(),
                            "end_year": item.getEndYear(), "start_age": item.getStartAge(),
                            "end_age": item.getEndAge(),
                            "annual": [annual_entry(year) for year in item.getLiuNian()]}
                           for item in yun.getDaYun(int(value.get("cycle_count", 10)))]}
        if profile.get("profile_id") == "bazi-ziping-complete-v1":
            output["complete_v1"] = bazi_complete(detail, eight.getDayGan(), output.get("fortune_cycles"))
        trace = [{"step": "lunar_python.Solar.fromYmdHms", "input": {"local_date": date, "local_time": time}},
                 {"step": "Lunar.getEightChar", "sect": eight.getSect()},
                 {"step": "EightChar mechanical accessors", "fields": sorted(output)}]
        return result_envelope(definition=BAZI, adapter_version=self.adapter_version,
            method_profile=value["method_profile"], canonical_input=value, output=output,
            warnings=["Upstream mechanical structure is not a complete BaZi interpretation."],
            disputes=[{"field": "day_boundary", "status": "profile_required"}], trace=trace, raw=output,
            ruleset_version="bazi-ziping-complete-1.0.0" if "complete_v1" in output else None,
            supporting_evidence=output.get("complete_v1", {}).get("strength", {}).get("supporting_evidence", []),
            counter_evidence=output.get("complete_v1", {}).get("strength", {}).get("counter_evidence", []))


class ZiweiUpstreamAdapter:
    adapter_version = "ziwei-upstream-adapter/1.0.0"

    def execute(self, value: dict) -> dict:
        profile=value.get("method_profile", {})
        if profile.get("profile_id") not in {"iztro-lunar-standard", "ziwei-sanhe-complete-v1"}:
            _profile(value,"iztro-lunar-standard","2.5.8")
        if profile.get("profile_id") == "ziwei-sanhe-complete-v1" and profile.get("version") != "1.0.0":
            raise ValueError("ziwei-sanhe-complete-v1@1.0.0 is required")
        if profile.get("leap_month_policy") != "iztro_fix_leap_true":
            raise ValueError("Ziwei upstream leap-month policy must be explicit")
        runner_input = {
            "lunar_year": value["lunar_year"], "lunar_month": value["lunar_month"],
            "lunar_day": value["lunar_day"], "hour_index": value["hour_index"],
            "traditional_sex": value["traditional_sex"], "profile_id": value["method_profile"]["profile_id"],
        }
        if value.get("target_date"):
            runner_input["target_date"] = value["target_date"]
            runner_input["target_hour_index"] = int(value.get("target_hour_index", 0))
        raw = execute_iztro(runner_input)
        output = {**normalize_iztro(raw),
                  "soul_ruler": raw.get("soul_ruler"), "body_ruler": raw.get("body_ruler"),
                  "solar_date": raw.get("solar_date"), "lunar_date": raw.get("lunar_date"),
                  "palaces": raw.get("palaces", []), "horoscope": raw.get("horoscope")}
        if profile.get("profile_id") == "ziwei-sanhe-complete-v1":
            output["complete_v1"] = ziwei_complete(output)
        return result_envelope(definition=ZIWEI, adapter_version=self.adapter_version,
            method_profile=value["method_profile"], canonical_input=value, output=output,
            warnings=["Pinned iztro structural chart; modern interpretation text is excluded."],
            disputes=[{"field": "leap_month_policy", "status": "profile_required"},
                      {"field": "transformation_school", "status": "profile_required"}],
            trace=[{"step": "iztro.astro.byLunar", "runtime": "local_node", "network": False}], raw=raw,
            ruleset_version="ziwei-sanhe-complete-1.0.0" if "complete_v1" in output else None,
            supporting_evidence=[e for p in output.get("complete_v1", {}).get("palaces", []) for e in p["supporting_evidence"]],
            counter_evidence=[e for p in output.get("complete_v1", {}).get("palaces", []) for e in p["counter_evidence"]])


def _load_vendored_hexagram():
    global _VENDORED_HEXAGRAM
    if _VENDORED_HEXAGRAM is not None:
        return _VENDORED_HEXAGRAM
    path = Path(__file__).parent / "vendor" / "liuyao_engine_0_1_0" / "hexagram.py"
    spec = importlib.util.spec_from_file_location("sanji_vendored_liuyao_hexagram_0_1_0", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("vendored liuyao hexagram module unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _VENDORED_HEXAGRAM = module
    return module


class LiuyaoUpstreamAdapter:
    adapter_version = "liuyao-upstream-adapter/1.0.0"

    def execute(self, value: dict) -> dict:
        profile=value.get("method_profile", {})
        if profile.get("profile_id") not in {"yaomancy-liuyao-engine-0.1.0", "liuyao-jingfang-najia-v1"}:
            _profile(value,"yaomancy-liuyao-engine-0.1.0","1.0.0")
        if profile.get("profile_id") == "liuyao-jingfang-najia-v1" and profile.get("version") != "1.0.0":
            raise ValueError("liuyao-jingfang-najia-v1@1.0.0 is required")
        lines = value["lines"]
        if len(lines) != 6 or any(line not in (6, 7, 8, 9) for line in lines):
            raise ValueError("lines must contain six bottom-to-top values in 6/7/8/9")
        bits = "".join("1" if line in (7, 9) else "0" for line in lines)
        moving = [index + 1 for index, line in enumerate(lines) if line in (6, 9)]
        changed_bits = "".join(str(1 - int(bit)) if index + 1 in moving else bit for index, bit in enumerate(bits))
        module = _load_vendored_hexagram()
        primary = module.cast_chart(bits, value["day_stem_index"])
        changed = module.cast_chart(changed_bits, value["day_stem_index"]) if moving else None
        norm = _legacy_text if profile.get("profile_id") == "liuyao-jingfang-najia-v1" else (lambda item: item)
        def chart(item):
            if item is None: return None
            return {"bits": item.bits, "name": norm(item.name), "palace": norm(item.palace),
                    "palace_five_element": norm(item.palace_wuxing), "gua_type": norm(item.gua_type),
                    "shi_position": item.shi_pos, "ying_position": item.ying_pos,
                    "lines": [{key:norm(value) for key,value in dataclass_dict(line).items()} | {"najia": norm(line.najia)} for line in item.yaos]}
        output = {"primary": chart(primary), "moving_lines": moving, "changed": chart(changed),
                  "not_admitted": ["final_fortune", "event_timing", "automatic_yongshen"]}
        if profile.get("profile_id") == "liuyao-jingfang-najia-v1":
            output["complete_v1"] = liuyao_complete(output, value)
            target = output["complete_v1"]["question"].get("liuqin")
            if target and not output["complete_v1"]["question"]["candidates"]:
                hidden = module.find_fushen(primary, target, value["day_stem_index"])
                if hidden is not None:
                    hidden_data = {key: norm(item) for key, item in dataclass_dict(hidden).items()}
                    hidden_data["najia"] = norm(hidden.najia)
                    flying = output["primary"]["lines"][hidden.position - 1]
                    output["complete_v1"]["question"].update({
                        "fushen": hidden_data,
                        "feishen": {"position": flying["position"], "najia": flying["najia"],
                                    "liuqin": flying["liuqin"]},
                        "status": "provisional",
                    })
        return result_envelope(definition=LIUYAO, adapter_version=self.adapter_version,
            method_profile=value["method_profile"], canonical_input=value, output=output,
            warnings=["Vendored exact upstream hexagram module avoids the unportable sxtwl runtime dependency."],
            disputes=[{"field": "yongshen", "status": "not_admitted_without_explicit_question_profile"}],
            trace=[{"step": "canonical_6_7_8_9_to_bits", "order": "bottom_to_top"},
                   {"step": "liuyao_engine.hexagram.cast_chart", "vendored_sha256": "e01071302ece21d825bb6020a7924e15807a9d587d47a79fb2bfca3e87e4d3b0"}], raw=output,
            ruleset_version="liuyao-jingfang-najia-1.0.0" if "complete_v1" in output else None,
            supporting_evidence=output.get("complete_v1", {}).get("supporting_evidence", []),
            counter_evidence=output.get("complete_v1", {}).get("counter_evidence", []))
