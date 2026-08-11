from __future__ import annotations

import json
import os
from itertools import product
from pathlib import Path
from jsonschema import Draft202012Validator

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from upstream_adapters import BaziUpstreamAdapter, LiuyaoUpstreamAdapter, ZiweiUpstreamAdapter
from najia import Najia

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "third_party" / "upstream-lock.json"


def _aggregate(values):
    return content_hash(values)


def bazi_cases():
    adapter=BaziUpstreamAdapter(); values=[]
    for year in range(1984,1994):
        for month,day,hour in ((1,1,0),(2,4,23),(3,21,12),(6,21,6),(9,23,18),(12,31,22)):
            values.append(adapter.execute({"local_date":f"{year:04d}-{month:02d}-{day:02d}",
                "local_time":f"{hour:02d}:00:00","traditional_sex":"male" if year%2 else "female",
                "yun_sect":1,"cycle_count":3,
                "method_profile":{"profile_id":"lunar-python-sect1","version":"1.0.0","sect":1,"wall_time_policy":"supplied_local_wall_time"}})["canonical_hash"])
    assert len(values)==60 and len(set(values))==60
    return values


def ziwei_cases():
    adapter=ZiweiUpstreamAdapter(); values=[]
    for year in (1984,1990,2000,2012):
        for month,day,hour in ((1,1,0),(2,8,1),(4,15,3),(6,18,5),(8,22,7),(10,25,9)):
            for sex in ("male","female"):
                values.append(adapter.execute({"lunar_year":year,"lunar_month":month,"lunar_day":day,
                  "hour_index":hour,"traditional_sex":sex,"target_date":"2026-08-03","target_hour_index":hour,
                  "method_profile":{"profile_id":"iztro-lunar-standard","version":"2.5.8","leap_month_policy":"iztro_fix_leap_true"}})["canonical_hash"])
    assert len(values)==48 and len(set(values))==48
    return values


def liuyao_cases():
    adapter=LiuyaoUpstreamAdapter(); values=[]
    for lines in product((6,7,8,9),repeat=6):
        result=adapter.execute({"lines":list(lines),"day_stem_index":0,
          "method_profile":{"profile_id":"yaomancy-liuyao-engine-0.1.0","version":"1.0.0"}})
        values.append(result["canonical_hash"])
    assert len(values)==4096 and len(set(values))==4096
    return values


def liuyao_najia_differential():
    adapter=LiuyaoUpstreamAdapter(); matched=0
    for static_lines in product((7,8),repeat=6):
        upstream=adapter.execute({"lines":list(static_lines),"day_stem_index":5,
          "method_profile":{"profile_id":"yaomancy-liuyao-engine-0.1.0","version":"1.0.0"}})["output"]["primary"]
        oracle=Najia(verbose=0).compile(params=[1 if line==7 else 2 for line in static_lines],
          date="2026-08-03T12:00:00+08:00").data
        assert upstream["bits"]==oracle["mark"] and upstream["name"]==oracle["name"]
        assert upstream["palace"]==oracle["gong"] and upstream["shi_position"]==oracle["shiy"][0]
        assert upstream["ying_position"]==oracle["shiy"][1]
        assert [line["liuqin"] for line in upstream["lines"]]==oracle["qin6"]
        matched+=1
    assert matched==64
    return matched


def composite_case(adapter_results):
    request={"schema_version":"engine-request/1.0.0","engine_api_version":"1.0","run_id":"validation",
      "run_mode":"research_preview","requested_modules":["upstream"],
      "input_snapshot":{"operation":"compose_upstream_traditional_v1","adapter_results":adapter_results},
      "ruleset_bundle_id":"sanji-upstream-composite-1.0.0",
      "data_versions":{"tzdb":"2025.2","ephemeris":"astronomy-engine/2.1.19","calendar_dataset":"upstream-lock/1.0.0"},
      "deterministic_context":{"as_of":"2000-01-01T00:00:00Z","random_method":"none","random_seed":None}}
    result=execute(request)
    reordered=execute({**request,"run_id":"reordered","input_snapshot":{**request["input_snapshot"],"adapter_results":list(reversed(adapter_results))}})
    assert result["output_hash"]==reordered["output_hash"]
    replayed=replay(result["replay_manifest"],{**request,"run_id":"replay","run_mode":"replay"})
    assert replayed["output_hash"]==result["output_hash"]
    domain=result["module_results"]["upstream"]["result"]
    adapter_schema=json.loads((ROOT/"packages"/"sanji-engine"/"src"/"sanji_engine"/"schemas"/"v2"/"upstream-adapter-result.schema.json").read_text(encoding="utf-8"))
    composite_schema=json.loads((ROOT/"packages"/"sanji-engine"/"src"/"sanji_engine"/"schemas"/"v2"/"upstream-composite-result.schema.json").read_text(encoding="utf-8"))
    for item in adapter_results: Draft202012Validator(adapter_schema).validate(item)
    Draft202012Validator(composite_schema).validate(domain)
    assert domain["strength_bp"]==0 and domain["confidence_bp"]==0 and domain["status"]=="insufficient"
    assert domain["deduplication"]["independent_source_count"]==len(adapter_results)
    duplicate=execute({**request,"run_id":"duplicate","input_snapshot":{**request["input_snapshot"],
      "adapter_results":adapter_results+[adapter_results[0]]}})["module_results"]["upstream"]["result"]
    assert duplicate["deduplication"]["independent_source_count"]==len(adapter_results)
    assert duplicate["deduplication"]["exact_duplicate_count"]==1
    return result["output_hash"]


def main():
    lock=json.loads(LOCK.read_text(encoding="utf-8")); assert len(lock["entries"])==4
    bazi=bazi_cases(); ziwei=ziwei_cases(); liuyao=liuyao_cases(); differential=liuyao_najia_differential()
    sample_b=BaziUpstreamAdapter().execute({"local_date":"1990-01-01","local_time":"12:00:00","traditional_sex":"male","yun_sect":1,"cycle_count":3,"method_profile":{"profile_id":"lunar-python-sect1","version":"1.0.0","sect":1,"wall_time_policy":"supplied_local_wall_time"}})
    sample_l=LiuyaoUpstreamAdapter().execute({"lines":[7,8,9,6,7,8],"day_stem_index":0,"method_profile":{"profile_id":"yaomancy-liuyao-engine-0.1.0","version":"1.0.0"}})
    sample_z=ZiweiUpstreamAdapter().execute({"lunar_year":1990,"lunar_month":1,"lunar_day":1,"hour_index":0,"traditional_sex":"male","target_date":"2026-08-03","target_hour_index":0,"method_profile":{"profile_id":"iztro-lunar-standard","version":"2.5.8","leap_month_policy":"iztro_fix_leap_true"}})
    actual={"upstream_lock_hash":content_hash(lock),"bazi_adapter_cases_hash":_aggregate(bazi),
            "ziwei_adapter_cases_hash":_aggregate(ziwei),"liuyao_adapter_cases_hash":_aggregate(liuyao),
            "composite_cases_hash":composite_case([sample_b,sample_z,sample_l])}
    expected=json.loads((ROOT/"tests"/"fixtures"/"upstream-traditional-hashes-v1.json").read_text(encoding="utf-8"))
    assert actual==expected,(actual,expected)
    print(json.dumps({"status":"ok","bazi_cases":60,"ziwei_cases":48,"liuyao_cases":4096,
      "liuyao_najia_independent_matches":differential,**actual},ensure_ascii=False))


if __name__=="__main__": main()
