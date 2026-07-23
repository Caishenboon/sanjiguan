import ast
import json
import unittest
from copy import deepcopy
from pathlib import Path

from sanji_engine import execute, inspect_ruleset, replay, validate_request
from sanji_engine.canonical import canonicalize, content_hash
from sanji_engine.errors import EngineError

ROOT = Path(__file__).resolve().parents[1]


def deterministic_request():
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "cross-platform-case",
        "run_mode": "research_preview",
        "requested_modules": ["calendar", "bazi"],
        "input_snapshot": {
            "operation": "normalize_birth_time",
            "birth_record": {
                "calendar_type": "gregorian",
                "local_date": "1990-01-15",
                "local_time": "08:30:00",
                "timezone_id": "Asia/Shanghai",
                "place": {
                    "name": "Synthetic",
                    "latitude": "31.230400",
                    "longitude": "121.473700",
                },
                "time_precision": "minute",
                "user_confirmed": True,
                "captured_at": "2026-07-23T00:00:00+00:00",
            },
            "solar_term_instants_utc": [],
        },
        "ruleset_bundle_id": "core-boundary-0.1.0",
        "data_versions": {
            "tzdb": "2025b",
            "ephemeris": "astronomy-engine-2.1.19",
            "calendar_dataset": "calendar-migration-baseline-1.0.0",
        },
        "deterministic_context": {
            "as_of": "2026-07-23T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


class SanjiEngineCoreTests(unittest.TestCase):
    def test_public_surface_is_exactly_four_entries(self):
        import sanji_engine
        self.assertEqual(
            {"validate_request", "execute", "replay", "inspect_ruleset"},
            set(sanji_engine.__all__),
        )

    def test_jcs_subset_and_binary_float_rejection(self):
        self.assertEqual(b'{"a":2,"z":1}', canonicalize({"z": 1, "a": 2}))
        value = deterministic_request()
        value["input_snapshot"]["score"] = 0.1
        with self.assertRaisesRegex(EngineError, "binary float"):
            validate_request(value)

    def test_disabled_modules_return_no_placeholder_calculation(self):
        result = execute(deterministic_request())
        disabled = result["module_results"]["bazi"]
        self.assertEqual("MODULE_DISABLED", disabled["error"]["code"])
        self.assertIsNone(disabled["result"])
        self.assertIn("bazi", result["disabled_modules"])

    def test_cross_platform_hash_fixture_and_replay(self):
        result = execute(deterministic_request())
        fixture = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/"
            "golden_cases/calendar/cross-platform-1.json").read_text("utf-8"))
        self.assertEqual(
            fixture["expected"]["output_hash"],
            result["output_hash"],
        )
        replayed = replay(result["replay_manifest"], deterministic_request())
        self.assertEqual(result["output_hash"], replayed["output_hash"])

    def test_ruleset_states_and_research_baseline_labels(self):
        bundle = inspect_ruleset("core-boundary-0.1.0")
        for module in ("bazi", "ziwei", "yijing", "past-life", "bardo",
                       "relationship", "life-chart"):
            self.assertFalse(bundle["modules"][module]["enabled"])
            self.assertEqual("UNCONFIRMED", bundle["modules"][module]["review_status"])
        baseline = json.loads((ROOT / "packages/sanji-engine/src/sanji_engine/"
            "research_baselines/signals-inference-sprint2.json").read_text("utf-8"))
        self.assertEqual("research_baseline", baseline["baseline_class"])
        self.assertFalse(baseline["production_approved"])

    def test_core_has_no_framework_database_network_or_llm_import(self):
        forbidden = {
            "fastapi", "next", "psycopg", "sqlalchemy", "requests",
            "httpx", "openai", "deepseek",
        }
        source_root = ROOT / "packages/sanji-engine/src/sanji_engine"
        for path in source_root.rglob("*.py"):
            tree = ast.parse(path.read_text("utf-8"))
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(imported & forbidden, f"{path}: {imported & forbidden}")
        text_assets = list(source_root.rglob("*.py")) + list(source_root.rglob("*.json"))
        self.assertNotIn(
            "DEEPSEEK",
            "\n".join(p.read_text("utf-8") for p in text_assets).upper(),
        )


if __name__ == "__main__":
    unittest.main()
