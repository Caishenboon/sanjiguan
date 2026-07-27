"""Build deterministic BaZi method-profile research assets.

The generated files contain method choices and expected *differences* only.
They deliberately contain no stem/branch or four-pillar calculation.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sanji_engine.calendar import solar_term_instant
from sanji_engine.canonical import content_hash

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "packages/sanji-engine/src/sanji_engine/bazi/assets"

PROFILE_IDS = {
    "civil": "BAZI.PROFILE.CIVIL_MIDNIGHT.CANDIDATE.V1",
    "apparent": "BAZI.PROFILE.APPARENT_ZICHU.CANDIDATE.V1",
    "dual": "BAZI.PROFILE.DUAL_SPLIT_ZI.CANDIDATE.V1",
}


def hashed(value: dict) -> dict:
    base = {key: child for key, child in value.items() if key != "content_hash"}
    return {**base, "content_hash": content_hash(base)}


def policy(
    policy_id: str,
    status: str,
    selected: str | None,
    options: list[str],
    refs: list[str],
    notes: str,
) -> dict:
    return {
        "policy_id": policy_id,
        "decision_status": status,
        "selected_option": selected,
        "options": options,
        "decision_refs": refs,
        "notes": notes,
    }


def profile(
    profile_id: str,
    solar: str,
    day: str,
    hour: str,
    *,
    solar_status: str = "CANDIDATE",
    status: str = "draft",
) -> dict:
    return hashed({
        "schema_version": "bazi-method-profile/1.0.0",
        "profile_id": profile_id,
        "profile_version": "0.1.0",
        "profile_class": "profile_discriminating_candidate",
        "status": status,
        "production_activatable": False,
        "calendar_basis": policy(
            "BAZI.CALENDAR_BASIS",
            "CANDIDATE",
            "PROLEPTIC_GREGORIAN_RESEARCH_WINDOW",
            ["PROLEPTIC_GREGORIAN_RESEARCH_WINDOW", "HISTORICAL_CIVIL_CALENDAR"],
            ["C-ENG-005", "C-GAP-003"],
            "Current code accepts Gregorian input; pre-reform civil-calendar semantics remain unresolved.",
        ),
        "legal_time_policy": policy(
            "BAZI.LEGAL_TIME",
            "FROZEN",
            "IANA_HISTORICAL_LOCAL_TIME_PRESERVE_RAW",
            ["IANA_HISTORICAL_LOCAL_TIME_PRESERVE_RAW"],
            ["C-OWNER-001", "C-ENG-001"],
            "Preserve entered civil time and resolve the named zone without silently rewriting it.",
        ),
        "solar_time_mode": policy(
            "BAZI.SOLAR_TIME",
            solar_status,
            solar,
            [
                "CIVIL_TIME_ONLY",
                "LOCAL_MEAN_SOLAR_TIME",
                "LOCAL_APPARENT_SOLAR_TIME",
                "DUAL_CIVIL_APPARENT_SENSITIVITY",
            ],
            ["C-OWNER-001", "C-ENG-002", "C-ENG-004"],
            "Only the dual policy is owner-frozen; other selections exist solely as discriminating controls.",
        ),
        "year_boundary_policy": policy(
            "BAZI.YEAR_BOUNDARY",
            "UNCONFIRMED",
            "LICHUN_ASTRONOMICAL_INSTANT_CANDIDATE",
            ["LICHUN_ASTRONOMICAL_INSTANT_CANDIDATE", "CIVIL_LUNAR_YEAR_CANDIDATE"],
            ["C-ENG-003", "C-GAP-004"],
            "Astronomical instant is mechanically available but its BaZi use is not owner-frozen.",
        ),
        "month_boundary_policy": policy(
            "BAZI.MONTH_BOUNDARY",
            "UNCONFIRMED",
            "TWELVE_JIE_ASTRONOMICAL_INSTANT_CANDIDATE",
            [
                "TWELVE_JIE_ASTRONOMICAL_INSTANT_CANDIDATE",
                "TWENTY_FOUR_TERMS_CANDIDATE",
                "CIVIL_DAY_CONTAINING_JIE_CANDIDATE",
            ],
            ["C-ENG-003", "C-GAP-004"],
            "Jie versus zhongqi and exact-boundary inclusion require qualified review.",
        ),
        "day_rollover_policy": policy(
            "BAZI.DAY_ROLLOVER",
            "UNCONFIRMED",
            day,
            ["DAY_BOUNDARY_00_CIVIL", "DAY_BOUNDARY_23_ZICHU", "LATE_EARLY_ZI_SPLIT"],
            ["C-GAP-001"],
            "D-002 remains unconfirmed; the selection is a comparison dimension only.",
        ),
        "hour_boundary_policy": policy(
            "BAZI.HOUR_BOUNDARY",
            "UNCONFIRMED",
            hour,
            [
                "CIVIL_TIME_12_DOUBLE_HOURS",
                "APPARENT_SOLAR_12_DOUBLE_HOURS",
                "DUAL_TIME_CANDIDATE_HOURS",
            ],
            ["C-OWNER-001", "C-GAP-001"],
            "No policy determines an hour pillar; this only states which time candidate would be tested.",
        ),
        "boundary_inclusion_policy": policy(
            "BAZI.BOUNDARY_INCLUSION",
            "UNCONFIRMED",
            "START_INCLUSIVE_END_EXCLUSIVE_CANDIDATE",
            [
                "START_INCLUSIVE_END_EXCLUSIVE_CANDIDATE",
                "START_EXCLUSIVE_END_INCLUSIVE_CANDIDATE",
                "EXACT_INSTANT_DUAL_SENSITIVITY",
            ],
            ["C-GAP-004"],
            "Exact equality at a boundary is not frozen.",
        ),
        "historical_calendar_policy": policy(
            "BAZI.HISTORICAL_CALENDAR",
            "UNCONFIRMED",
            "RESEARCH_WINDOW_1900_2099",
            [
                "RESEARCH_WINDOW_1900_2099",
                "PROLEPTIC_GREGORIAN_ALL_SUPPORTED_DATES",
                "HISTORICAL_REFORM_BY_LOCATION",
            ],
            ["C-ENG-001", "C-ENG-005", "C-GAP-003"],
            "The narrow window prevents tzdb and calendar uncertainty being hidden.",
        ),
        "unknown_time_policy": policy(
            "BAZI.UNKNOWN_TIME",
            "FROZEN",
            "ENUMERATE_CANDIDATE_INTERVALS_NO_GUESSED_HOUR",
            ["ENUMERATE_CANDIDATE_INTERVALS_NO_GUESSED_HOUR"],
            ["C-OWNER-001", "C-ENG-004"],
            "Unknown time remains a candidate interval and never becomes a guessed hour.",
        ),
        "location_precision_policy": policy(
            "BAZI.LOCATION_PRECISION",
            "CANDIDATE",
            "EXPLICIT_COORDINATES_AND_PRECISION",
            ["EXPLICIT_COORDINATES_AND_PRECISION", "CITY_CENTROID_WITH_WARNING"],
            ["C-OWNER-001", "C-ENG-002"],
            "Solar correction requires longitude and must preserve its precision provenance.",
        ),
        "source_claim_ids": [
            "C-OWNER-001", "C-ENG-001", "C-ENG-002", "C-ENG-003",
            "C-ENG-004", "C-ENG-005", "C-GAP-001", "C-GAP-003", "C-GAP-004",
        ],
        "review_status": "UNCONFIRMED",
        "reviewer_requirements": [
            "product_owner",
            "qualified_bazi_method_reviewer",
            "calendar_engineering_reviewer",
        ],
        "known_disputes": [
            "D-002 day rollover and early/late Zi handling",
            "D-003 later strength, luck-start and direction rules are outside this profile",
            "year and month boundary use of astronomical instants is not owner-frozen",
            "pre-Gregorian-reform and weak historical-zone evidence",
        ],
        "selection_authority": "CANDIDATE_ONLY_NOT_OWNER_DECISION",
    })


def build_profiles() -> dict[str, dict]:
    return {
        "civil-midnight-candidate-0.1.0.json": profile(
            PROFILE_IDS["civil"],
            "CIVIL_TIME_ONLY",
            "DAY_BOUNDARY_00_CIVIL",
            "CIVIL_TIME_12_DOUBLE_HOURS",
        ),
        "apparent-zichu-candidate-0.1.0.json": profile(
            PROFILE_IDS["apparent"],
            "LOCAL_APPARENT_SOLAR_TIME",
            "DAY_BOUNDARY_23_ZICHU",
            "APPARENT_SOLAR_12_DOUBLE_HOURS",
        ),
        "dual-split-zi-candidate-0.1.0.json": profile(
            PROFILE_IDS["dual"],
            "DUAL_CIVIL_APPARENT_SENSITIVITY",
            "LATE_EARLY_ZI_SPLIT",
            "DUAL_TIME_CANDIDATE_HOURS",
            solar_status="FROZEN",
            status="review_candidate",
        ),
    }


def build_evidence() -> dict:
    locators = [
        {
            "locator_id": "L-OWNER-D001",
            "source_id": "S-OWNER-DECISIONS",
            "source_level": "A1_INTERNAL_OWNER_DECISION",
            "access_class": "repository_internal",
            "location": "docs/decisions/product-owner-confirmation.md#D-001",
            "tradition_tags": ["engineering", "product_governance"],
        },
        {
            "locator_id": "L-IANA-TZDB",
            "source_id": "S-IANA-TZDB",
            "source_level": "A1_PRIMARY_TECHNICAL",
            "access_class": "public",
            "location": "https://data.iana.org/time-zones/tzdb/theory.html",
            "tradition_tags": ["engineering", "timekeeping"],
        },
        {
            "locator_id": "L-USNO-EOT",
            "source_id": "S-USNO-EOT",
            "source_level": "A1_PRIMARY_TECHNICAL",
            "access_class": "public",
            "location": "https://aa.usno.navy.mil/faq/eqtime#apparent-and-mean-solar-time",
            "tradition_tags": ["astronomy", "engineering"],
        },
        {
            "locator_id": "L-HKO-TERMS",
            "source_id": "S-HKO-SOLAR-TERMS",
            "source_level": "A1_PRIMARY_TECHNICAL",
            "access_class": "public",
            "location": "https://www.hko.gov.hk/en/gts/time/24solarterms.htm",
            "tradition_tags": ["astronomy", "calendar"],
        },
        {
            "locator_id": "L-HKO-INSTANTS",
            "source_id": "S-HKO-SOLAR-INSTANTS",
            "source_level": "A1_PRIMARY_TECHNICAL",
            "access_class": "public",
            "location": "https://www.hko.gov.hk/en/gts/astronomy/Solar_Term.htm",
            "tradition_tags": ["astronomy", "calendar"],
        },
        {
            "locator_id": "L-SHLG-JUAN11",
            "source_id": "S-SHILIN-GUANGJI-JUAN11",
            "source_level": "A2_PUBLIC_DOMAIN_PRIMARY_TEXT",
            "access_class": "public_domain",
            "location": "https://zh.wikisource.org/wiki/事林廣記/續集/卷11#凡起大運",
            "tradition_tags": ["bazi", "historical_text"],
        },
        {
            "locator_id": "L-LUOLUZI",
            "source_id": "S-LUOLUZI-SANMING",
            "source_level": "A2_PUBLIC_DOMAIN_PRIMARY_TEXT",
            "access_class": "public_domain",
            "location": "https://zh.wikisource.org/wiki/珞琭子三命消息賦注#男迎女送",
            "tradition_tags": ["bazi", "historical_text"],
        },
        {
            "locator_id": "L-CALENDAR-CODE",
            "source_id": "S-SANJI-CALENDAR-BASELINE",
            "source_level": "A1_INTERNAL_ENGINE_FACT",
            "access_class": "repository_internal",
            "location": "packages/sanji-engine/src/sanji_engine/calendar",
            "tradition_tags": ["engineering", "calendar"],
        },
        {
            "locator_id": "L-D002",
            "source_id": "S-DECISION-REGISTER",
            "source_level": "A1_INTERNAL_OWNER_DECISION",
            "access_class": "repository_internal",
            "location": "docs/decision-register.md#D-002",
            "tradition_tags": ["bazi", "product_governance"],
        },
        {
            "locator_id": "L-D003",
            "source_id": "S-DECISION-REGISTER",
            "source_level": "A1_INTERNAL_OWNER_DECISION",
            "access_class": "repository_internal",
            "location": "docs/decision-register.md#D-003",
            "tradition_tags": ["bazi", "product_governance"],
        },
    ]
    claims = [
        {
            "claim_id": "C-OWNER-001",
            "claim_type": "owner_decision",
            "claim": "Preserve historical civil time, calculate local apparent solar time, and only enter dual sensitivity when a boundary changes; never silently rewrite birth time.",
            "locator_ids": ["L-OWNER-D001"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": [],
            "review_status": "approved_owner_decision",
            "review_candidate_ready": True,
            "missing_evidence": [],
        },
        {
            "claim_id": "C-ENG-001",
            "claim_type": "engineering_fact",
            "claim": "IANA tzdb represents named-zone histories and DST transitions, with known limitations in early historical data.",
            "locator_ids": ["L-IANA-TZDB"],
            "supports_claim_ids": ["C-OWNER-001"],
            "contradicts_claim_ids": [],
            "review_status": "researched",
            "review_candidate_ready": True,
            "missing_evidence": ["jurisdiction-specific pre-1970 corroboration when used"],
        },
        {
            "claim_id": "C-ENG-002",
            "claim_type": "engineering_fact",
            "claim": "Local mean solar time varies by longitude and apparent solar time differs from it by the equation of time.",
            "locator_ids": ["L-USNO-EOT"],
            "supports_claim_ids": ["C-OWNER-001"],
            "contradicts_claim_ids": [],
            "review_status": "researched",
            "review_candidate_ready": True,
            "missing_evidence": [],
        },
        {
            "claim_id": "C-ENG-003",
            "claim_type": "engineering_fact",
            "claim": "The 24 solar terms are defined at 15-degree longitude intervals and comprise alternating major and minor terms.",
            "locator_ids": ["L-HKO-TERMS", "L-HKO-INSTANTS"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": [],
            "review_status": "researched",
            "review_candidate_ready": True,
            "missing_evidence": ["qualified BaZi ruling on which terms switch pillars"],
        },
        {
            "claim_id": "C-TRAD-001",
            "claim_type": "traditional_statement",
            "claim": "One public-domain received text states a three-days-to-one-year luck-start rule and a stem-yin-yang plus sex direction rule.",
            "locator_ids": ["L-SHLG-JUAN11"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": ["C-GAP-002"],
            "review_status": "researched",
            "review_candidate_ready": False,
            "missing_evidence": ["edition review", "qualified school reviewer", "counter-tradition corpus"],
        },
        {
            "claim_id": "C-TRAD-002",
            "claim_type": "traditional_statement",
            "claim": "A received commentary contains a direction statement for yang men and yin women.",
            "locator_ids": ["L-LUOLUZI"],
            "supports_claim_ids": ["C-TRAD-001"],
            "contradicts_claim_ids": ["C-GAP-002"],
            "review_status": "researched",
            "review_candidate_ready": False,
            "missing_evidence": ["edition review", "modern field and ethics decision"],
        },
        {
            "claim_id": "C-ENG-004",
            "claim_type": "engineering_fact",
            "claim": "The migrated Calendar baseline emits civil, local mean and local apparent candidates and boundary sensitivity without selecting a BaZi chart.",
            "locator_ids": ["L-CALENDAR-CODE"],
            "supports_claim_ids": ["C-OWNER-001"],
            "contradicts_claim_ids": [],
            "review_status": "verified_internal",
            "review_candidate_ready": True,
            "missing_evidence": [],
        },
        {
            "claim_id": "C-ENG-005",
            "claim_type": "engineering_fact",
            "claim": "Current date parsing uses Gregorian ISO dates and does not encode location-specific calendar-reform history.",
            "locator_ids": ["L-CALENDAR-CODE"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": ["C-GAP-003"],
            "review_status": "verified_internal",
            "review_candidate_ready": True,
            "missing_evidence": ["owner-approved historical support window"],
        },
        {
            "claim_id": "C-GAP-001",
            "claim_type": "evidence_gap",
            "claim": "No qualified source package currently freezes Zi-hour day rollover, early/late Zi, or correction order.",
            "locator_ids": ["L-D002"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": [],
            "review_status": "UNCONFIRMED",
            "review_candidate_ready": False,
            "missing_evidence": ["qualified reviewer", "located source set", "signed boundary cases"],
        },
        {
            "claim_id": "C-GAP-002",
            "claim_type": "evidence_gap",
            "claim": "D-003 strength, luck-start and direction methods are not frozen; traditional attestations do not themselves create a production method.",
            "locator_ids": ["L-D003", "L-SHLG-JUAN11", "L-LUOLUZI"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": ["C-TRAD-001", "C-TRAD-002"],
            "review_status": "UNCONFIRMED",
            "review_candidate_ready": False,
            "missing_evidence": ["qualified reviewer", "method decision tree", "authoritative cases"],
        },
        {
            "claim_id": "C-GAP-003",
            "claim_type": "evidence_gap",
            "claim": "The project has not frozen pre-Gregorian-reform civil-calendar semantics or a production historical support range.",
            "locator_ids": ["L-CALENDAR-CODE", "L-IANA-TZDB"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": ["C-ENG-005"],
            "review_status": "UNCONFIRMED",
            "review_candidate_ready": False,
            "missing_evidence": ["historical calendar policy", "jurisdictional reform data"],
        },
        {
            "claim_id": "C-GAP-004",
            "claim_type": "evidence_gap",
            "claim": "Astronomical solar-term instants are available, but year/month pillar use and exact-instant inclusion are not owner-frozen.",
            "locator_ids": ["L-HKO-TERMS", "L-HKO-INSTANTS", "L-D003"],
            "supports_claim_ids": [],
            "contradicts_claim_ids": ["C-ENG-003"],
            "review_status": "UNCONFIRMED",
            "review_candidate_ready": False,
            "missing_evidence": ["qualified BaZi reviewer", "source-attested boundary cases"],
        },
    ]
    return hashed({
        "schema_version": "bazi-method-evidence/1.0.0",
        "bundle_id": "bazi-method-evidence-0.1.0",
        "status": "research_only",
        "production_activatable": False,
        "locators": locators,
        "claims": claims,
    })


def case(
    case_id: str,
    category: str,
    classification: str,
    input_value: dict,
    dimensions: list[str],
    expected: dict,
    claims: list[str],
    *,
    review_status: str = "pending_manual_review",
    gate: bool = False,
) -> dict:
    return hashed({
        "case_id": case_id,
        "classification": classification,
        "category": category,
        "input": input_value,
        "profile_ids": list(PROFILE_IDS.values()),
        "expected_difference": {
            "dimensions": dimensions,
            "by_profile": expected,
            "pillar_values": None,
            "assertion_scope": "method_policy_difference_only",
        },
        "source_claim_ids": claims,
        "review_status": review_status,
        "formal_gate_eligible": gate,
    })


def base_input(local_date: str, local_time: str | None, timezone_id: str = "Asia/Shanghai") -> dict:
    return {
        "calendar_type": "gregorian",
        "local_date": local_date,
        "local_time": local_time,
        "timezone_id": timezone_id,
        "place": {
            "name": "Synthetic",
            "latitude": "31.230400",
            "longitude": "121.473700",
            "precision": "exact_test_coordinate",
        },
        "time_precision": "second" if local_time else "unknown",
        "user_confirmed": True,
        "synthetic": True,
    }


def profile_expectation(field: str) -> dict:
    mapping = {
        "solar_time_mode": {
            PROFILE_IDS["civil"]: "CIVIL_TIME_ONLY",
            PROFILE_IDS["apparent"]: "LOCAL_APPARENT_SOLAR_TIME",
            PROFILE_IDS["dual"]: "DUAL_CIVIL_APPARENT_SENSITIVITY",
        },
        "day_rollover_policy": {
            PROFILE_IDS["civil"]: "DAY_BOUNDARY_00_CIVIL",
            PROFILE_IDS["apparent"]: "DAY_BOUNDARY_23_ZICHU",
            PROFILE_IDS["dual"]: "LATE_EARLY_ZI_SPLIT",
        },
        "hour_boundary_policy": {
            PROFILE_IDS["civil"]: "CIVIL_TIME_12_DOUBLE_HOURS",
            PROFILE_IDS["apparent"]: "APPARENT_SOLAR_12_DOUBLE_HOURS",
            PROFILE_IDS["dual"]: "DUAL_TIME_CANDIDATE_HOURS",
        },
        "boundary_inclusion_policy": {
            profile_id: "START_INCLUSIVE_END_EXCLUSIVE_CANDIDATE"
            for profile_id in PROFILE_IDS.values()
        },
        "year_boundary_policy": {
            profile_id: "LICHUN_ASTRONOMICAL_INSTANT_CANDIDATE"
            for profile_id in PROFILE_IDS.values()
        },
        "month_boundary_policy": {
            profile_id: "TWELVE_JIE_ASTRONOMICAL_INSTANT_CANDIDATE"
            for profile_id in PROFILE_IDS.values()
        },
        "historical_calendar_policy": {
            profile_id: "RESEARCH_WINDOW_1900_2099"
            for profile_id in PROFILE_IDS.values()
        },
    }
    return mapping[field]


def solar_instant_2024(longitude: int, month: int, day: int) -> datetime:
    start = datetime(2024, month, day, tzinfo=timezone.utc)
    return solar_term_instant(longitude, start, 25)


def build_cases() -> dict:
    cases: list[dict] = []

    time_specs = [
        ("TIME-MODERN", "1990-01-15", "08:30:00", "Asia/Shanghai", "ordinary modern time"),
        ("TIME-DST-START", "2024-03-10", "02:00:00", "America/New_York", "DST spring gap"),
        ("TIME-DST-END", "2024-11-03", "01:30:00", "America/New_York", "DST fall fold"),
        ("TIME-HISTORICAL-ZONE", "1949-05-28", "00:00:00", "Asia/Shanghai", "historical legal offset"),
        ("TIME-LONGITUDE", "1990-01-15", "08:30:00", "Asia/Shanghai", "longitude from zone meridian"),
        ("TIME-MEAN-CROSS-HOUR", "1990-01-15", "00:30:00", "Asia/Shanghai", "mean-solar crosses hour"),
        ("TIME-APPARENT-CROSS-DAY", "1990-02-11", "00:02:00", "Asia/Shanghai", "apparent-solar crosses date"),
    ]
    for case_id, date_value, time_value, zone, note in time_specs:
        item = base_input(date_value, time_value, zone)
        item["scenario"] = note
        cases.append(case(
            case_id,
            "time_and_timezone",
            "mechanically_verified" if case_id in {"TIME-MODERN", "TIME-DST-START", "TIME-DST-END"} else "profile_discriminating",
            item,
            ["solar_time_mode", "historical_legal_time"],
            profile_expectation("solar_time_mode"),
            ["C-ENG-001", "C-ENG-002", "C-ENG-004"],
            review_status="mechanically_verified" if case_id in {"TIME-MODERN", "TIME-DST-START", "TIME-DST-END"} else "pending_manual_review",
            gate=case_id in {"TIME-MODERN", "TIME-DST-START", "TIME-DST-END"},
        ))
    pre_reform = base_input("1500-02-04", "12:00:00", "Europe/Rome")
    pre_reform["scenario"] = "calendar reform semantics are deliberately unresolved"
    cases.append(case(
        "TIME-PRE-GREGORIAN-REFORM",
        "time_and_timezone",
        "pending_manual_review",
        pre_reform,
        ["historical_calendar_policy"],
        profile_expectation("historical_calendar_policy"),
        ["C-ENG-001", "C-ENG-005", "C-GAP-003"],
        review_status="pending_manual_review",
        gate=False,
    ))

    lichun = solar_instant_2024(315, 2, 1)
    for suffix, delta in (("BEFORE", -1), ("AT", 0), ("AFTER", 1)):
        instant = lichun + timedelta(seconds=delta)
        cases.append(case(
            f"YEAR-LICHUN-{suffix}",
            "year_boundary",
            "profile_discriminating",
            {
                **base_input("2024-02-04", "00:00:00"),
                "reference_instant_utc": lichun.isoformat(),
                "test_instant_utc": instant.isoformat(),
                "offset_seconds": delta,
            },
            ["year_boundary_policy", "boundary_inclusion_policy"],
            {
                profile_id: {
                    "year_boundary_policy": value,
                    "boundary_inclusion_policy": profile_expectation("boundary_inclusion_policy")[profile_id],
                }
                for profile_id, value in profile_expectation("year_boundary_policy").items()
            },
            ["C-ENG-003", "C-GAP-004"],
        ))
    cases.append(case(
        "YEAR-LICHUN-CROSS-TIMEZONE",
        "year_boundary",
        "profile_discriminating",
        {
            **base_input("2024-02-03", "16:30:00", "America/Los_Angeles"),
            "reference_instant_utc": lichun.isoformat(),
            "scenario": "civil date and solar-term instant differ by timezone",
        },
        ["year_boundary_policy", "historical_legal_time"],
        profile_expectation("year_boundary_policy"),
        ["C-ENG-001", "C-ENG-003", "C-GAP-004"],
    ))

    jie = [
        ("LICHUN", 315, 2, 1), ("JINGZHE", 345, 3, 1),
        ("QINGMING", 15, 4, 1), ("LIXIA", 45, 5, 1),
        ("MANGZHONG", 75, 6, 1), ("XIAOSHU", 105, 7, 1),
        ("LIQIU", 135, 8, 1), ("BAILU", 165, 9, 1),
        ("HANLU", 195, 10, 1), ("LIDONG", 225, 11, 1),
        ("DAXUE", 255, 12, 1), ("XIAOHAN", 285, 1, 1),
    ]
    for name, longitude, month, day in jie:
        instant = solar_instant_2024(longitude, month, day)
        for suffix, delta in (("BEFORE", -1), ("AT", 0), ("AFTER", 1)):
            cases.append(case(
                f"MONTH-{name}-{suffix}",
                "month_boundary",
                "profile_discriminating",
                {
                    **base_input(instant.date().isoformat(), instant.time().replace(tzinfo=None).isoformat()),
                    "term_name": name,
                    "target_longitude": longitude,
                    "reference_instant_utc": instant.isoformat(),
                    "test_instant_utc": (instant + timedelta(seconds=delta)).isoformat(),
                    "offset_seconds": delta,
                },
                ["month_boundary_policy", "boundary_inclusion_policy"],
                {
                    profile_id: {
                        "month_boundary_policy": value,
                        "boundary_inclusion_policy": profile_expectation("boundary_inclusion_policy")[profile_id],
                    }
                    for profile_id, value in profile_expectation("month_boundary_policy").items()
                },
                ["C-ENG-003", "C-GAP-004"],
            ))
    for case_id, longitude, label in (
        ("MONTH-ZHONGQI-CONTROL", 330, "YUSHUI"),
        ("MONTH-MIDNIGHT-TERM", 15, "SYNTHETIC_MIDNIGHT_QINGMING"),
    ):
        cases.append(case(
            case_id,
            "month_boundary",
            "profile_discriminating",
            {
                **base_input("2024-04-04", "00:00:00"),
                "target_longitude": longitude,
                "term_name": label,
                "scenario": "control distinguishing jie, zhongqi, and civil midnight",
            },
            ["month_boundary_policy", "boundary_inclusion_policy"],
            profile_expectation("month_boundary_policy"),
            ["C-ENG-003", "C-GAP-004"],
        ))

    for value in ("22:59:00", "23:00:00", "23:59:00", "00:00:00", "00:59:00", "01:00:00"):
        cases.append(case(
            f"DAY-{value.replace(':', '')}",
            "day_boundary",
            "profile_discriminating",
            base_input("2024-02-04", value),
            ["day_rollover_policy"],
            profile_expectation("day_rollover_policy"),
            ["C-GAP-001"],
        ))
    crossing = base_input("2024-02-04", "00:02:00")
    crossing["scenario"] = "local apparent correction crosses a candidate day boundary"
    cases.append(case(
        "DAY-APPARENT-CORRECTION-CROSS",
        "day_boundary",
        "profile_discriminating",
        crossing,
        ["solar_time_mode", "day_rollover_policy"],
        {
            profile_id: {
                "solar_time_mode": profile_expectation("solar_time_mode")[profile_id],
                "day_rollover_policy": profile_expectation("day_rollover_policy")[profile_id],
            }
            for profile_id in PROFILE_IDS.values()
        },
        ["C-ENG-002", "C-ENG-004", "C-GAP-001"],
    ))

    for hour in range(1, 24, 2):
        value = f"{hour:02d}:00:00"
        cases.append(case(
            f"HOUR-BOUNDARY-{hour:02d}00",
            "hour_boundary",
            "profile_discriminating",
            base_input("2024-02-04", value),
            ["hour_boundary_policy", "boundary_inclusion_policy"],
            {
                profile_id: {
                    "hour_boundary_policy": profile_expectation("hour_boundary_policy")[profile_id],
                    "boundary_inclusion_policy": profile_expectation("boundary_inclusion_policy")[profile_id],
                }
                for profile_id in PROFILE_IDS.values()
            },
            ["C-ENG-004", "C-GAP-001"],
        ))
    unknown_specs = [
        ("HOUR-ZI-BEFORE", "22:59:59", "second"),
        ("HOUR-ZI-AFTER", "23:00:00", "second"),
        ("HOUR-IMPRECISE", "10:00:00", "hour"),
        ("HOUR-UNKNOWN", None, "unknown"),
        ("HOUR-MULTI-CANDIDATE", "10:30:00", "two_hour_interval"),
    ]
    for case_id, value, precision in unknown_specs:
        item = base_input("2024-02-04", value)
        item["time_precision"] = precision
        cases.append(case(
            case_id,
            "hour_boundary",
            "profile_discriminating",
            item,
            ["hour_boundary_policy", "unknown_time_policy"],
            profile_expectation("hour_boundary_policy"),
            ["C-ENG-004", "C-GAP-001"],
        ))

    counts = {}
    for item in cases:
        counts[item["category"]] = counts.get(item["category"], 0) + 1
    return hashed({
        "schema_version": "bazi-boundary-cases/1.0.0",
        "asset_id": "bazi-boundary-cases-0.1.0",
        "status": "research_only",
        "production_activatable": False,
        "case_count": len(cases),
        "category_counts": counts,
        "classification_definitions": {
            "mechanically_verified": "repeatable engineering behavior without disputed pillar rules",
            "profile_discriminating": "shows policy differences without selecting a final method",
            "source_attested": "reserved for located source cases with the source method stated",
            "pending_manual_review": "excluded from formal gates pending qualified review",
        },
        "cases": cases,
    })


def write_json(name: str, value: dict) -> None:
    (ASSETS / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    profiles = build_profiles()
    for filename, value in profiles.items():
        write_json(filename, value)
    registry = hashed({
        "schema_version": "bazi-method-profile-registry/1.0.0",
        "status": "research_only",
        "production_activatable": False,
        "profiles": {
            value["profile_id"]: {
                "filename": filename,
                "content_hash": value["content_hash"],
            }
            for filename, value in sorted(profiles.items())
        },
    })
    write_json("profile-registry-1.0.0.json", registry)
    write_json("method-evidence-1.0.0.json", build_evidence())
    write_json("boundary-cases-1.0.0.json", build_cases())
    print(f"wrote {len(profiles)} profiles and {build_cases()['case_count']} cases")


if __name__ == "__main__":
    main()
