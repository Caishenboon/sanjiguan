"""Create, reset, or delete the fully synthetic V1 demonstration archive."""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import urllib.error
import urllib.request
import uuid


parser = argparse.ArgumentParser()
parser.add_argument("action", choices=["create", "reset", "delete"])
parser.add_argument("--base-url", default="http://127.0.0.1:3000")
args = parser.parse_args()

jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def request(path: str, method: str = "GET", payload=None, headers=None):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    session = os.getenv("SANJI_DEMO_SESSION", "")
    merged = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        **({"Cookie": f"__Host-session={session}"} if session else {}),
        **(headers or {}),
    }
    if method not in {"GET", "HEAD"}:
        merged["Idempotency-Key"] = str(uuid.uuid4())
    req = urllib.request.Request(args.base_url + path, data=body, headers=merged, method=method)
    try:
        with client.open(req) as response:
            data = response.read()
            return json.loads(data) if data else None
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {path} failed ({exc.code}): {detail}") from exc


existing_profile = os.getenv("SANJI_DEMO_PROFILE_ID", "")
if args.action in {"reset", "delete"}:
    if not existing_profile or not os.getenv("SANJI_DEMO_SESSION"):
        raise SystemExit("SANJI_DEMO_PROFILE_ID and SANJI_DEMO_SESSION are required")
    request(f"/api/v1/profiles/{existing_profile}", "DELETE")
    if args.action == "delete":
        print(json.dumps({"status": "deleted", "profile_id": existing_profile, "synthetic": True}))
        raise SystemExit(0)

if not os.getenv("SANJI_DEMO_SESSION"):
    bootstrap = os.getenv("OWNER_BOOTSTRAP_TOKEN", "")
    if not bootstrap:
        raise SystemExit("OWNER_BOOTSTRAP_TOKEN is required; it is never printed")
    try:
        request(
            "/api/v1/auth/bootstrap-owner",
            "POST",
            {"bootstrap_token": bootstrap, "email": "demo-owner@invalid.example"},
        )
    except RuntimeError as exc:
        if "(409)" in str(exc):
            raise SystemExit(
                "An owner already exists. Supply SANJI_DEMO_SESSION from a disposable local session."
            ) from exc
        raise

profile = request(
    "/api/v1/profiles",
    "POST",
    {
        "display_name": "虚构演示者·清和",
        "consent_version": "profile-consent/1.0",
        "birth": {
            "calendar_type": "gregorian",
            "local_date": "1992-04-18",
            "local_time": "09:30:00",
            "timezone_id": "Asia/Shanghai",
            "timezone_database": "IANA",
            "timezone_database_version": "2025b",
            "time_precision": "minute",
            "place": {
                "label": "虚构城市·云汀",
                "latitude": 31.2,
                "longitude": 121.4,
                "coordinate_source": "synthetic_fixture",
            },
            "user_confirmed": True,
            "captured_at": "2026-01-01T00:00:00Z",
        },
    },
)
profile_id = profile["id"]

records = [
    ("vow_action", "持续完成一项虚构手艺计划", ["steadiness", "craft"]),
    ("dream", "梦见虚构庭院中的纸灯", ["paper_lantern", "courtyard"]),
    ("practice", "连续三周记录并复盘虚构作品", ["repeat_action"]),
    ("life_event", "完成虚构作品《云汀小记》", ["completion"]),
    ("relationship", "与虚构伙伴讨论协作边界", ["consent_checked"]),
    ("life_event", "从虚构旧居迁往云汀", ["transition", "migration"]),
]
record_ids = []
for index, (kind, text, tags) in enumerate(records, 1):
    item = request(
        f"/api/v1/profiles/{profile_id}/journal",
        "POST",
        {
            "entry_date": f"2026-01-{index + 1:02d}",
            "entry_type": kind,
            "fields": {
                "state": "observed",
                "date_precision": "exact_date",
                "synthetic": True,
            },
            "free_text": text,
            "tags": tags,
            "evidence_ids": [],
            "candidate_evidence": True,
        },
    )
    record_ids.append(item["id"])

tosses = [
    {"line_no": line, "coin_faces": ["heads", "tails", "tails"], "was_retossed": False}
    for line in range(1, 7)
]
divination = request(
    f"/api/v1/profiles/{profile_id}/divinations/three-coin",
    "POST",
    {
        "question": "如何完成虚构作品？",
        "purpose": "V1虚构演示",
        "divination_at": "2026-01-08T08:00:00Z",
        "timezone": "Asia/Shanghai",
        "location_precision": "none",
        "method_id": "YIJING.THREE_COIN.PHYSICAL.V1",
        "method_version": "1.0.0",
        "coin_face_mapping_id": "COIN_FACES.HEADS_3_TAILS_2.V1",
        "coin_face_mapping_version": "1.0.0",
        "tosses": tosses,
    },
)

liuxiang = request(
    f"/api/v1/profiles/{profile_id}/liuxiang/executions",
    "POST",
    {"as_of": "2026-07-30T00:00:00Z", "excluded_record_ids": []},
)
liuxiang_replay = request(
    f"/api/v1/liuxiang/executions/{liuxiang['id']}/replay",
    "POST",
)
liuxiang_reanalysis = request(
    f"/api/v1/liuxiang/executions/{liuxiang['id']}/reanalyze",
    "POST",
    {"as_of": "2026-07-30T00:00:00Z"},
)

topics = {}
for topic in ("sushe", "zhongyin_life", "yuanqi"):
    topics[topic] = request(
        f"/api/v1/profiles/{profile_id}/topics/{topic}/executions",
        "POST",
        {"as_of": "2026-07-30T00:00:00Z", "excluded_record_ids": []},
    )

life_trend = request(
    f"/api/v1/profiles/{profile_id}/life-trend/executions",
    "POST",
    {
        "as_of": "2026-07-30T00:00:00Z",
        "start_date": "2025-01-01",
        "end_date": "2028-12-31",
        "granularity": "year",
        "future_bucket_count": 2,
    },
)
report = request(
    f"/api/v1/life-trend-executions/{life_trend['id']}/narrative",
    "POST",
    {"external_model_confirmed": False},
)
life_replay = request(
    f"/api/v1/life-trend-executions/{life_trend['id']}/replay",
    "POST",
)
life_reanalysis = request(
    f"/api/v1/life-trend-executions/{life_trend['id']}/reanalyze",
    "POST",
    {"as_of": "2026-07-30T00:00:00Z", "granularity": "year"},
)

summary = {
    "status": "created",
    "synthetic": True,
    "profile_id": profile_id,
    "record_ids": record_ids,
    "divination_id": divination["id"],
    "liuxiang_execution_id": liuxiang["id"],
    "liuxiang_replay_matched": liuxiang_replay["matched"],
    "liuxiang_reanalysis_id": liuxiang_reanalysis["id"],
    "topic_execution_ids": {name: item["id"] for name, item in topics.items()},
    "life_trend_execution_id": life_trend["id"],
    "life_trend_replay_matched": life_replay["matched"],
    "life_trend_reanalysis_id": life_reanalysis["id"],
    "core_output_hash": life_trend["core_output_hash"],
    "deterministic_report_hash": life_trend["deterministic_report_hash"],
    "narrative_source": report["source"],
}
print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
