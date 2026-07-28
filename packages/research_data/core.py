from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import re
import shutil
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "research-data" / "manifests"
CACHE_ENV = "SANJI_RESEARCH_DATA_CACHE"
DATE_EXACT = re.compile(r"^\d{2}/\d{2}/\d{4}$")
DATE_MONTH = re.compile(r"^(?:\d{1,2}/\d{4}|\d{4}-\d{2})$")
DATE_YEAR = re.compile(r"^\d{4}$")
STD_TIME = re.compile(
    r"^(?P<hour>\d{2}):(?P<minute>\d{2}) "
    r"(?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{4}) "
    r"(?P<offset>[+-]\d{2}:\d{2})$"
)


def cache_root() -> Path:
    configured = os.getenv(CACHE_ENV)
    return Path(configured).expanduser() if configured else Path.home() / ".cache" / "sanjiguan-research-data"


def load_manifests() -> list[dict]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(MANIFEST_DIR.glob("*.json"))
    ]


def get_manifest(dataset_id: str) -> dict:
    for manifest in load_manifests():
        if manifest["dataset_id"] == dataset_id:
            return manifest
    raise ValueError(f"unknown_dataset:{dataset_id}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_manifest(manifest: dict) -> list[str]:
    required = {
        "schema_version", "dataset_id", "official_provider", "platform",
        "pinned_revision", "downloaded_at", "files", "declared_license",
        "license_file_location", "license_review_status", "record_count",
        "fields", "allowed_uses", "raw_data_committable", "fixture_committable",
        "public_redistribution_allowed", "sensitivity", "provider_credibility",
        "sanji_independent_verification", "shared_source_group", "known_limitations",
        "connector_enabled",
    }
    errors = [f"missing:{field}" for field in sorted(required - manifest.keys())]
    if manifest.get("connector_enabled") and manifest.get("license_review_status") not in {
        "conditional_download_only", "approved",
    }:
        errors.append("enabled_connector_without_license_clearance")
    if manifest.get("dataset_id", "").startswith("DReAMy-lib/") and manifest.get("connector_enabled"):
        errors.append("dreambank_connector_must_remain_disabled_pending_review")
    for file in manifest.get("files", []):
        if not re.fullmatch(r"[a-f0-9]{64}", str(file.get("sha256", ""))):
            errors.append(f"invalid_sha256:{file.get('path')}")
        if manifest.get("pinned_revision") not in str(file.get("url", "")):
            errors.append(f"unpinned_url:{file.get('path')}")
    return errors


def sync_dataset(dataset_id: str, retries: int = 3) -> list[Path]:
    manifest = get_manifest(dataset_id)
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("manifest_invalid:" + ",".join(errors))
    if not manifest["connector_enabled"]:
        raise PermissionError(f"connector_disabled:{manifest['license_review_status']}")
    destination = cache_root() / manifest["cache_key"] / manifest["pinned_revision"]
    destination.mkdir(parents=True, exist_ok=True)
    completed: list[Path] = []
    for entry in manifest["files"]:
        target = destination / entry["path"]
        if target.exists() and sha256_file(target) == entry["sha256"]:
            completed.append(target)
            continue
        partial = target.with_suffix(target.suffix + ".part")
        partial.unlink(missing_ok=True)
        last_error: Exception | None = None
        for attempt in range(retries):
            try:
                request = urllib.request.Request(
                    entry["url"],
                    headers={"User-Agent": "sanjiguan-research-data/1.0"},
                )
                with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
                    shutil.copyfileobj(response, output)
                if sha256_file(partial) != entry["sha256"]:
                    raise ValueError(f"sha256_mismatch:{entry['path']}")
                partial.replace(target)
                completed.append(target)
                break
            except Exception as exc:  # network errors are reported after bounded retries
                last_error = exc
                partial.unlink(missing_ok=True)
                if attempt + 1 < retries:
                    time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"download_failed:{entry['path']}:{last_error}")
    return completed


def date_precision(raw: object) -> str:
    value = str(raw or "").strip()
    if DATE_EXACT.fullmatch(value):
        return "exact_date"
    if DATE_MONTH.fullmatch(value):
        return "month_only"
    if DATE_YEAR.fullmatch(value):
        return "year_only"
    return "unknown"


def _birth_file(manifest: dict) -> Path:
    return cache_root() / manifest["cache_key"] / manifest["pinned_revision"] / "PersonList-15k.csv"


def _marriage_file(manifest: dict) -> Path:
    return cache_root() / manifest["cache_key"] / manifest["pinned_revision"] / "MarriageInfoDataset.csv"


def normalize_births(path: Path, manifest: dict) -> tuple[list[dict], dict]:
    people: list[dict] = []
    invalid = 0
    precision = Counter()
    ratings = Counter()
    ids = Counter()
    names = Counter()
    missing_place = missing_timezone = 0
    with path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            try:
                raw_birth = json.loads(row["BirthTime"])
                match = STD_TIME.fullmatch(raw_birth.get("StdTime", ""))
                if not match:
                    raise ValueError("birth_time_format")
                location = raw_birth.get("Location") or {}
                note = ast.literal_eval(row["Notes"]) if row.get("Notes") else {}
                original_id = row["RowKey"]
                ids[original_id] += 1
                names[row["Name"].strip().casefold()] += 1
                precision["exact_time"] += 1
                ratings[str(note.get("rodden", "missing"))] += 1
                if not location.get("Name"):
                    missing_place += 1
                # The provider supplies a numeric UTC offset, not an IANA zone
                # or an independently auditable DST flag.
                missing_timezone += 1
                person = {
                    "person_id": f"vedastro:{original_id}",
                    "source_person_id": original_id,
                    "original_person_identifier": original_id,
                    "normalized_name": row["Name"].strip(),
                    "aliases": [],
                    "birth_date": f"{match['year']}-{match['month']}-{match['day']}",
                    "birth_time": f"{match['hour']}:{match['minute']}:00",
                    "time_precision": "exact_time",
                    "birth_place_raw": location.get("Name"),
                    "normalized_place": location.get("Name"),
                    "latitude": str(location.get("Latitude")),
                    "longitude": str(location.get("Longitude")),
                    "timezone_id": None,
                    "utc_offset": match["offset"],
                    "dst_status": "unknown",
                    "provider_rating": str(note.get("rodden", "missing")),
                    "sanji_verification_status": "unverified_provider_claim",
                    "source_revision": manifest["pinned_revision"],
                    "provenance": {
                        "dataset_id": manifest["dataset_id"],
                        "source_row_key": original_id,
                    },
                    "shared_source_group": manifest["shared_source_group"],
                }
                people.append(person)
            except (ValueError, KeyError, SyntaxError, json.JSONDecodeError):
                invalid += 1
    report = {
        "raw_rows": len(people) + invalid,
        "normalized_rows": len(people),
        "invalid_rows": invalid,
        "duplicate_source_ids": sum(value - 1 for value in ids.values() if value > 1),
        "duplicate_normalized_names": sum(value - 1 for value in names.values() if value > 1),
        "birth_time_precision": dict(sorted(precision.items())),
        "provider_rating": dict(sorted(ratings.items())),
        "missing_place": missing_place,
        "missing_iana_timezone": missing_timezone,
        "complete_four_pillars_eligible_by_time_precision": len(people),
        "ziwei_time_eligible_by_time_precision": len(people),
        "eligibility_warning": "Eligibility is precision-only; missing IANA/DST provenance still requires review.",
    }
    return people, report


def _outcome(raw: object) -> str:
    value = str(raw or "").strip().casefold()
    if value in {"dissolution", "divorce", "separation", "separated", "breakup"}:
        return "divorce"
    if "death" in value or "murder" in value or "traged" in value:
        return "spouse_death_or_other_end"
    if value in {"happiness", "ongoing", "long-term partnership", "long-term relationship"}:
        return "relationship_ongoing"
    return "unknown_outcome"


def normalize_marriages(path: Path, manifest: dict) -> tuple[list[dict], dict]:
    events: list[dict] = []
    invalid_rows = 0
    person_ids = Counter()
    marriage_precision = Counter()
    divorce_precision = Counter()
    with path.open(encoding="utf-8-sig", newline="") as source:
        for row_number, row in enumerate(csv.DictReader(source), 1):
            try:
                person = row["PartitionKey"]
                decoded = json.loads(row["Info"])
                if "marriages" not in decoded or not isinstance(decoded["marriages"], list):
                    raise ValueError("marriages_shape_changed")
                marriages = decoded["marriages"]
                person_ids[person] += 1
                for index, marriage in enumerate(marriages):
                    marriage_raw = marriage.get("marriageDate")
                    divorce_raw = marriage.get("divorceDate")
                    mp = date_precision(marriage_raw)
                    dp = date_precision(divorce_raw)
                    marriage_precision[mp] += 1
                    divorce_precision[dp] += 1
                    events.append({
                        "event_id": f"vedastro:{person}:marriage:{index + 1}",
                        "person_id": f"vedastro:{person}",
                        "event_type": "marriage",
                        "start_date_raw": marriage_raw,
                        "end_date_raw": divorce_raw,
                        "start_date": marriage_raw if mp == "exact_date" else None,
                        "end_date": divorce_raw if dp == "exact_date" else None,
                        "date_precision": mp,
                        "end_date_precision": dp,
                        "related_person_raw": marriage.get("spouse"),
                        "relationship_type_raw": marriage.get("type"),
                        "outcome": _outcome(marriage.get("outcome")),
                        "outcome_raw": marriage.get("outcome"),
                        "provider_credibility": marriage.get("dataCredibility"),
                        "sanji_verification_status": "unverified_provider_claim",
                        "source": manifest["dataset_id"],
                        "source_revision": manifest["pinned_revision"],
                        "provenance": {"source_row": row_number, "event_index": index},
                        "shared_source_group": manifest["shared_source_group"],
                    })
            except (ValueError, KeyError, json.JSONDecodeError):
                invalid_rows += 1
    report = {
        "raw_rows": sum(person_ids.values()) + invalid_rows,
        "normalized_person_rows": sum(person_ids.values()),
        "normalized_event_rows": len(events),
        "invalid_rows": invalid_rows,
        "duplicate_source_ids": sum(value - 1 for value in person_ids.values() if value > 1),
        "marriage_date_precision": dict(sorted(marriage_precision.items())),
        "divorce_date_precision": dict(sorted(divorce_precision.items())),
    }
    return events, report


def link_people(people: list[dict], events: list[dict]) -> tuple[list[dict], dict]:
    exact = {person["person_id"]: person for person in people}
    matches: list[dict] = []
    counters = Counter()
    matched_people: set[str] = set()
    for event in events:
        person_id = event["person_id"]
        if person_id in exact:
            method, confidence, review = "stable_source_person_id", 10_000, False
            counters["exact_matches"] += 1
            matched_people.add(person_id)
        else:
            method, confidence, review = "unmatched", 0, True
            counters["unmatched"] += 1
        matches.append({
            "event_id": event["event_id"],
            "person_id": person_id if confidence else None,
            "match_method": method,
            "match_confidence_bp": confidence,
            "conflicting_fields": [],
            "manual_review_required": review,
            "provenance": {"shared_source_group": "vedastro_org"},
        })
    return matches, {
        "exact_match_events": counters["exact_matches"],
        "exact_match_people": len(matched_people),
        "unmatched_events": counters["unmatched"],
        "conflicts": 0,
        "fuzzy_candidates": 0,
        "rejected_false_matches": 0,
        "match_rate_bp": (
            (counters["exact_matches"] * 10_000) // len(events) if events else 0
        ),
        "independence_warning": "Both datasets share provider group vedastro_org.",
    }


def normalize_all(write_records: bool = True) -> dict:
    birth_manifest = get_manifest("vedastro-org/15000-Famous-People-Birth-Date-Location")
    marriage_manifest = get_manifest("vedastro-org/15000-Famous-People-Marriage-Divorce-Info")
    people, birth_report = normalize_births(_birth_file(birth_manifest), birth_manifest)
    events, marriage_report = normalize_marriages(_marriage_file(marriage_manifest), marriage_manifest)
    matches, match_report = link_people(people, events)
    output = cache_root() / "normalized"
    if write_records:
        output.mkdir(parents=True, exist_ok=True)
        for name, values in (("people.jsonl", people), ("life-events.jsonl", events), ("matches.jsonl", matches)):
            with (output / name).open("w", encoding="utf-8") as target:
                for value in values:
                    target.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {
        "schema_version": "research-data-quality/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "asset_class": "external_research_unverified",
        "birth": birth_report,
        "marriage": marriage_report,
        "matching": match_report,
        "claims": {
            "reality_validation": False,
            "predictive_power_established": False,
            "ruleset_mutation_allowed": False,
        },
    }


def clear_cache() -> None:
    target = cache_root().resolve()
    if target.name != "sanjiguan-research-data":
        raise ValueError("refusing_to_clear_nonstandard_cache_root")
    if target.exists():
        shutil.rmtree(target)
