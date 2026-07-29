from __future__ import annotations

import csv
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from packages.research_data.core import (
    date_precision, link_people, load_manifests, normalize_births,
    normalize_marriages, sync_dataset, validate_manifest,
)
from packages.research_data.evaluation import evaluate_binary_protocol


class ResearchDataPipelineTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "dataset_id": "synthetic/test",
            "pinned_revision": "0" * 40,
            "shared_source_group": "synthetic_provider",
        }

    def test_manifests_are_pinned_and_dreambank_is_blocked(self):
        manifests = load_manifests()
        self.assertEqual(3, len(manifests))
        for manifest in manifests:
            self.assertEqual([], validate_manifest(manifest))
        dreambank = next(value for value in manifests if value["dataset_id"].startswith("DReAMy"))
        self.assertFalse(dreambank["connector_enabled"])
        self.assertEqual("license_review_required", dreambank["license_review_status"])
        self.assertFalse(dreambank["raw_data_committable"])

    def test_year_only_is_never_fabricated_as_a_date(self):
        self.assertEqual("year_only", date_precision("2016"))
        self.assertEqual("unknown", date_precision("Not Applicable"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "marriages.csv"
            with path.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=["PartitionKey", "RowKey", "Info"])
                writer.writeheader()
                writer.writerow({
                    "PartitionKey": "Synthetic1988",
                    "RowKey": "",
                    "Info": json.dumps({"marriages": [{
                        "type": "Synthetic", "spouse": "Other", "marriageDate": "2016",
                        "divorceDate": "", "outcome": "Unknown",
                        "dataCredibility": "synthetic",
                    }]}),
                })
            events, report = normalize_marriages(path, self.manifest)
        self.assertIsNone(events[0]["start_date"])
        self.assertEqual("year_only", events[0]["date_precision"])
        self.assertEqual(1, report["marriage_date_precision"]["year_only"])

    def test_stable_id_matching_only(self):
        people = [{"person_id": "vedastro:Exact"}]
        events = [
            {"event_id": "e1", "person_id": "vedastro:Exact"},
            {"event_id": "e2", "person_id": "vedastro:SimilarName"},
        ]
        matches, report = link_people(people, events)
        self.assertEqual(1, report["exact_match_events"])
        self.assertEqual(1, report["unmatched_events"])
        self.assertTrue(matches[1]["manual_review_required"])
        self.assertEqual(0, report["fuzzy_candidates"])

    def test_birth_parser_preserves_offset_without_claiming_iana_or_dst(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "births.csv"
            with path.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=["RowKey", "BirthTime", "Gender", "Name", "Notes"])
                writer.writeheader()
                writer.writerow({
                    "RowKey": "Synthetic1988",
                    "BirthTime": json.dumps({
                        "StdTime": "08:15 14/03/1988 +08:00",
                        "Location": {"Name": "Fictional", "Longitude": 120, "Latitude": 30},
                    }),
                    "Gender": "Unspecified", "Name": "Fictional Person",
                    "Notes": "{'rodden': 'SYNTHETIC'}",
                })
            people, report = normalize_births(path, self.manifest)
        self.assertEqual("+08:00", people[0]["utc_offset"])
        self.assertIsNone(people[0]["timezone_id"])
        self.assertEqual("unknown", people[0]["dst_status"])
        self.assertEqual(1, report["missing_iana_timezone"])

    def test_permutation_protocol_is_reproducible(self):
        records = [{
            "record_id": f"r{index:03d}",
            "prediction": index % 2,
            "outcome": (index // 3) % 2,
            "stratum": str(index // 20),
        } for index in range(100)]
        first = evaluate_binary_protocol(records, seed=20260728)
        second = evaluate_binary_protocol(list(reversed(records)), seed=20260728)
        self.assertEqual(first, second)
        self.assertFalse(first["claims"]["predictive_power_established"])

    def test_interrupted_download_never_promotes_partial_file(self):
        revision = "a" * 40
        manifest = {
            "schema_version": "research-dataset-manifest/1.0.0",
            "dataset_id": "synthetic/network", "official_provider": "synthetic",
            "platform": "test", "pinned_revision": revision, "downloaded_at": None,
            "cache_key": "network-test",
            "files": [{
                "path": "data.csv",
                "url": f"https://example.invalid/resolve/{revision}/data.csv",
                "sha256": "b" * 64,
            }],
            "declared_license": "synthetic", "license_file_location": "fixture",
            "license_review_status": "approved", "record_count": 0, "fields": [],
            "allowed_uses": ["test"], "raw_data_committable": False,
            "fixture_committable": True, "public_redistribution_allowed": False,
            "sensitivity": "none", "provider_credibility": "synthetic",
            "sanji_independent_verification": "not_applicable",
            "shared_source_group": "synthetic", "known_limitations": [],
            "connector_enabled": True,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "network-test" / revision / "data.csv.part"
            target.parent.mkdir(parents=True)
            target.write_text("partial", encoding="utf-8")
            with (
                patch("packages.research_data.core.get_manifest", return_value=manifest),
                patch("packages.research_data.core.cache_root", return_value=root),
                patch(
                    "packages.research_data.core.urllib.request.urlopen",
                    side_effect=urllib.error.URLError("offline"),
                ),
            ):
                with self.assertRaises(RuntimeError):
                    sync_dataset("synthetic/network", retries=1)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix("").exists())

    def test_manifest_license_gap_and_nested_json_change_are_rejected(self):
        manifest = next(
            value for value in load_manifests()
            if value["dataset_id"].startswith("vedastro-org/")
        )
        broken = dict(manifest)
        broken["license_review_status"] = "license_review_required"
        self.assertIn(
            "enabled_connector_without_license_clearance",
            validate_manifest(broken),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "changed.csv"
            with path.open("w", encoding="utf-8", newline="") as target:
                writer = csv.DictWriter(target, fieldnames=["PartitionKey", "RowKey", "Info"])
                writer.writeheader()
                writer.writerow({"PartitionKey": "P", "RowKey": "", "Info": "{\"unexpected\": true}"})
            events, report = normalize_marriages(path, self.manifest)
        self.assertEqual([], events)
        self.assertEqual(0, report["normalized_person_rows"])
        self.assertEqual(1, report["invalid_rows"])


if __name__ == "__main__":
    unittest.main()
