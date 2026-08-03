"""Determinism and conformance gate for traditional algorithms complete V1."""
from __future__ import annotations

import itertools
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"packages/sanji-engine/src"),str(ROOT/"packages/upstream-adapters/src"),str(ROOT/"packages/oracle-adapters/src")]

from sanji_engine import execute, replay
from sanji_engine.canonical import content_hash
from upstream_adapters import BaziUpstreamAdapter,LiuyaoUpstreamAdapter,ZiweiUpstreamAdapter

FIXTURE=ROOT/"tests/fixtures/traditional-algorithms-complete-v1-hashes.json"
OLD_HASHES=[
 "a08cb815b1ba65f16c4873b4c6cfac6653220a7d5630078a654beb36935ea96c",
 "81a43d8a57f12d9b1a5481b6cc34727bd555bceb08291f3c3ec01420d627fabd",
 "250e06cce33d5da5d66570386921ab3dc35df403f0c5c514bbb128f3b1051059",
 "695d404fee8a31d484661ed8617ee3bd96d6ae5d48f77d9be3fc13a93d614772",
 "1ce8007e27a3227bb1357ad2233c64c9c9d196bea1017d8e128cb5854ea985a9",
 "20cba2932d0d800590aa26fd0dd954f5c621d194c909f0a638844dced836b139",
 "97d96f973c611e9ecf91cc45acdb99dcc15a9f0970c4275128e48170f123dbbe",
 "a81019a737762808cb29636b06753cbcf18582d968be107df428287f7463f25b",
 "4d4a3acfdd3c613e4bbc90a341f368ed9a4982e39f057af19bca9a9a18394732",
 "de612316797fad52deb4e2297f4407fab1759557488a3d86f81232bbfaa1fbd5",
 "2ed23f6538b06daa4ed9fc0d67b2cbb812e6853ad150a059484534ced9ffac62",
]


def bazi_cases():
    out=[]; start=date(1984,1,6)
    for i in range(60):
        d=start+timedelta(days=i*223)
        value={"local_date":d.isoformat(),"local_time":f"{(i*5)%24:02d}:{(i*7)%60:02d}:00",
          "traditional_sex":"male" if i%2==0 else "female","yun_sect":1,"cycle_count":3,
          "method_profile":{"profile_id":"bazi-ziping-complete-v1","version":"1.0.0","sect":1,"wall_time_policy":"supplied_local_wall_time"}}
        item=BaziUpstreamAdapter().execute(value)
        result=item["output"]["complete_v1"]
        assert result["strength"]["status"] in {"extremely_weak","weak","balanced","strong","extremely_strong"}
        assert result["pattern"]["candidate"] and result["fortune_cycles"]["cycles"]
        out.append(item)
    return out


def ziwei_cases():
    out=[]
    for month,hour in itertools.product(range(1,13),(0,3,6,9)):
        value={"lunar_year":1990,"lunar_month":month,"lunar_day":min(15,month+2),"hour_index":hour,
          "traditional_sex":"male" if hour%2==0 else "female","target_date":"2026-08-03","target_hour_index":hour,
          "method_profile":{"profile_id":"ziwei-sanhe-complete-v1","version":"1.0.0","leap_month_policy":"iztro_fix_leap_true"}}
        item=ZiweiUpstreamAdapter().execute(value); result=item["output"]["complete_v1"]
        assert len(result["palaces"])==12 and all(len(p["sanhe_palaces"])==3 for p in result["palaces"])
        out.append(item)
    return out


def liuyao_cases():
    out=[]
    for index,lines in enumerate(itertools.product((6,7,8,9),repeat=6)):
        value={"lines":list(lines),"day_stem_index":index%10,"day_branch_index":index%12,"month_branch_index":(index+6)%12,
          "xunkong_branches":[],"question_type":"career",
          "method_profile":{"profile_id":"liuyao-jingfang-najia-v1","version":"1.0.0"}}
        item=LiuyaoUpstreamAdapter().execute(value); result=item["output"]["complete_v1"]
        assert len(result["primary"]["lines"])==6
        assert result["moving_lines"]==[i+1 for i,line in enumerate(lines) if line in (6,9)]
        out.append(item)
    return out


def engine_request(items,run_id="fixture",mode="research_preview"):
    return {"schema_version":"engine-request/1.0.0","engine_api_version":"1.0","run_id":run_id,"run_mode":mode,
      "requested_modules":["traditional-complete"],"input_snapshot":{"operation":"compose_traditional_algorithms_complete_v1","adapter_results":items},
      "ruleset_bundle_id":"sanji-traditional-composite-1.0.0","data_versions":{"tzdb":"2025.2","ephemeris":"astronomy-engine/2.1.19","calendar_dataset":"traditional-v1-upstream-lock/1.0.0"},
      "deterministic_context":{"as_of":"2000-01-01T00:00:00Z","random_method":"none","random_seed":None}}


def main():
    bazi=bazi_cases(); ziwei=ziwei_cases(); liuyao=liuyao_cases()
    composites=[]
    for i in range(12):
        result=execute(engine_request([bazi[i],ziwei[i],liuyao[i*341]],f"composite-{i}"))
        composites.append(result["module_results"]["traditional-complete"]["result"])
    first=execute(engine_request([bazi[0],ziwei[0],liuyao[0]],"original"))
    reordered=execute(engine_request([liuyao[0],bazi[0],ziwei[0]],"reordered"))
    assert first["output_hash"]==reordered["output_hash"]
    replay_request=engine_request([bazi[0],ziwei[0],liuyao[0]],"replay","replay")
    assert replay(first["replay_manifest"],replay_request)["output_hash"]==first["output_hash"]
    searchable=[]
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in {".json",".py",".md",".tsx"} and "work" not in path.parts and path.name != Path(__file__).name:
            searchable.append(path.read_text(encoding="utf-8",errors="ignore"))
    source_text="\n".join(searchable)
    assert all(value in source_text for value in OLD_HASHES),"a required historical hash disappeared"
    actual={"schema_version":"traditional-algorithms-complete-hashes/1.0.0",
      "counts":{"bazi":len(bazi),"ziwei":len(ziwei),"liuyao":len(liuyao),"composite":len(composites)},
      "upstream_lock_hash":content_hash(json.loads((ROOT/"third_party/traditional-v1-upstream-lock.json").read_text(encoding="utf-8"))),
      "bazi_v1_hash":content_hash([x["output"]["complete_v1"] for x in bazi]),
      "ziwei_v1_hash":content_hash([x["output"]["complete_v1"] for x in ziwei]),
      "liuyao_v1_hash":content_hash([x["output"]["complete_v1"] for x in liuyao]),
      "composite_v1_hash":content_hash(composites),"replay_output_hash":first["output_hash"]}
    if not FIXTURE.exists():
        print(json.dumps(actual,ensure_ascii=False,indent=2)); return 2
    expected=json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert actual==expected,f"complete V1 hash drift\nexpected={expected}\nactual={actual}"
    print(json.dumps({"status":"passed",**actual},ensure_ascii=False))
    return 0


if __name__=="__main__": raise SystemExit(main())
