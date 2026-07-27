import itertools
import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from sanji_engine import execute, inspect_ruleset, replay
from sanji_engine.canonical import content_hash
from sanji_engine.errors import EngineError
from sanji_engine.yijing.assets import load_hexagrams

ROOT = Path(__file__).resolve().parents[1]


def request_for(
    values=(6, 7, 8, 9, 6, 7),
    bundle_id="yijing-three-coin-mechanical-0.1.0",
    mode="research_preview",
):
    coins = {6: [2, 2, 2], 7: [3, 2, 2], 8: [3, 3, 2], 9: [3, 3, 3]}
    return {
        "schema_version": "engine-request/1.0.0",
        "engine_api_version": "1.0",
        "run_id": "synthetic-yijing-test",
        "run_mode": mode,
        "requested_modules": ["yijing"],
        "input_snapshot": {
            "operation": "cast_physical_three_coin",
            "method_id": "YIJING.THREE_COIN.PHYSICAL.MECHANICAL.V1",
            "method_version": "1.0.0",
            "input_order": "bottom_to_top",
            "tosses": [
                {"line_position": index, "coin_values": coins[value]}
                for index, value in enumerate(values, 1)
            ],
        },
        "ruleset_bundle_id": bundle_id,
        "data_versions": {
            "tzdb": "not_used",
            "ephemeris": "not_used",
            "calendar_dataset": "not_used",
            "yijing_hexagram_mapping": "king-wen-hexagrams/1.0.0",
        },
        "deterministic_context": {
            "as_of": "2000-01-01T00:00:00Z",
            "random_method": "none",
            "random_seed": None,
        },
    }


class ThreeCoinEngineTests(unittest.TestCase):
    def result(self, values=(6, 7, 8, 9, 6, 7)):
        return execute(request_for(values))["module_results"]["yijing"]["result"]

    def assert_code(self, code, request):
        with self.assertRaises(EngineError) as raised:
            execute(request)
        self.assertEqual(code, raised.exception.code)

    def test_all_eight_raw_coin_arrangements(self):
        seen = {}
        for arrangement in itertools.product((2, 3), repeat=3):
            request = request_for((7,) * 6)
            request["input_snapshot"]["tosses"][0]["coin_values"] = list(arrangement)
            line = execute(request)["module_results"]["yijing"]["result"]["lines"][0]
            total = sum(arrangement)
            self.assertEqual(total, line["sum"])
            self.assertEqual(list(arrangement), line["coin_values"])
            seen.setdefault(total, set()).add(
                (line["line_state"], line["base_polarity"], line["moving"],
                 line["transformed_polarity"])
            )
        self.assertEqual({6, 7, 8, 9}, set(seen))
        self.assertTrue(all(len(states) == 1 for states in seen.values()))

    def test_exhaustive_4096_six_line_states(self):
        base_keys = set()
        transformed_keys = set()
        hashes = set()
        for values in itertools.product((6, 7, 8, 9), repeat=6):
            result = execute(request_for(values))
            domain = result["module_results"]["yijing"]["result"]
            expected_base = "".join("0" if value in {6, 8} else "1" for value in values)
            expected_changed = "".join(
                "1" if value in {6, 7} else "0" for value in values
            )
            self.assertEqual(expected_base, domain["base_hexagram"]["key"])
            self.assertEqual(expected_changed, domain["transformed_hexagram"]["key"])
            self.assertEqual(
                [index for index, value in enumerate(values, 1) if value in {6, 9}],
                domain["moving_lines"],
            )
            self.assertEqual(expected_base[:3], domain["lower_trigram"]["key"])
            self.assertEqual(expected_base[3:], domain["upper_trigram"]["key"])
            self.assertIn(domain["base_hexagram"]["sequence"], range(1, 65))
            self.assertIn(domain["transformed_hexagram"]["sequence"], range(1, 65))
            base_keys.add(expected_base)
            transformed_keys.add(expected_changed)
            hashes.add(result["output_hash"])
        self.assertEqual(64, len(base_keys))
        self.assertEqual(64, len(transformed_keys))
        self.assertEqual(4096, len(hashes))

    def test_mapping_asset_integrity(self):
        mapping, metadata = load_hexagrams()
        self.assertEqual(64, len(mapping))
        self.assertEqual(set(range(1, 65)), {item["sequence"] for item in mapping.values()})
        self.assertEqual("乾", mapping["111111"]["name"])
        self.assertEqual("坤", mapping["000000"]["name"])
        self.assertEqual("既济", mapping["101010"]["name"])
        self.assertEqual("未济", mapping["010101"]["name"])
        self.assertEqual(
            "sha256:596c8dd8afe597b8530b008343f0d68ea81889c90d8b4a208e6b28531e6a1113",
            metadata["content_hash"],
        )

    def test_result_schema_and_missing_asset(self):
        result = execute(request_for())["module_results"]["yijing"]["result"]
        schema = json.loads(
            (
                ROOT
                / "packages/shared-types/schemas/yijing-three-coin-engine-result.schema.json"
            ).read_text("utf-8")
        )
        self.assertEqual("yijing", result["module"])
        self.assertTrue(set(schema["required"]) <= set(result))
        with patch(
            "sanji_engine.public.cast_physical_three_coin",
            side_effect=EngineError("REPLAY_ASSET_MISSING", "fixture unavailable"),
        ):
            self.assert_code("REPLAY_ASSET_MISSING", request_for())

    def test_special_cases_and_no_interpretation(self):
        static = self.result((7,) * 6)
        self.assertEqual([], static["moving_lines"])
        self.assertFalse(static["has_transformed_hexagram"])
        self.assertEqual(static["base_hexagram"], static["transformed_hexagram"])
        all_moving = self.result((6, 9, 6, 9, 6, 9))
        self.assertEqual([1, 2, 3, 4, 5, 6], all_moving["moving_lines"])
        first = self.result((6, 7, 7, 7, 7, 7))
        top = self.result((7, 7, 7, 7, 7, 9))
        self.assertEqual([1], first["moving_lines"])
        self.assertEqual([6], top["moving_lines"])
        all_yin = self.result((8,) * 6)
        all_yang = self.result((7,) * 6)
        self.assertEqual(2, all_yin["base_hexagram"]["sequence"])
        self.assertEqual(1, all_yang["base_hexagram"]["sequence"])
        for result in (static, all_moving, first, top, all_yin, all_yang):
            self.assertIsNone(result["interpretation"])
            self.assertIsNone(result["auspiciousness"])
            self.assertIsNone(result["manifestation_period"])

    def test_invalid_inputs_are_not_guessed(self):
        requests = []
        for count in (5, 7):
            request = request_for()
            request["input_snapshot"]["tosses"] = request["input_snapshot"]["tosses"][:count]
            if count == 7:
                request["input_snapshot"]["tosses"].append(
                    {"line_position": 7, "coin_values": [2, 2, 2]}
                )
            requests.append(request)
        for coins in ([2, 2], [2, 2, 2, 2], [2, 2, 4], ["2", 2, 2], [2.0, 2, 2], None):
            request = request_for()
            request["input_snapshot"]["tosses"][0]["coin_values"] = coins
            requests.append(request)
        missing_order = request_for()
        missing_order["input_snapshot"].pop("input_order")
        requests.append(missing_order)
        reverse_order = request_for()
        reverse_order["input_snapshot"]["input_order"] = "top_to_bottom"
        requests.append(reverse_order)
        wrong_method = request_for()
        wrong_method["input_snapshot"]["method_version"] = "missing"
        requests.append(wrong_method)
        wrong_mapping = request_for()
        wrong_mapping["data_versions"]["yijing_hexagram_mapping"] = "missing"
        requests.append(wrong_mapping)
        duplicate_position = request_for()
        duplicate_position["input_snapshot"]["tosses"][1]["line_position"] = 1
        requests.append(duplicate_position)
        for request in requests:
            with self.subTest(request=request):
                self.assert_code(
                    "REPLAY_DATA_VERSION_MISMATCH"
                    if request is wrong_mapping else "INPUT_INVALID",
                    request,
                )

    def test_trace_replay_tamper_and_revocation(self):
        request = request_for()
        result = execute(request)
        self.assertEqual(7, len(result["trace"]))
        self.assertEqual(
            list(range(1, 7)),
            [step["parameters"]["line_position"] for step in result["trace"][:6]],
        )
        replayed = replay(result["replay_manifest"], request)
        self.assertEqual(result["output_hash"], replayed["output_hash"])

        changed = request_for()
        changed["input_snapshot"]["tosses"][0]["coin_values"] = [3, 3, 3]
        with self.assertRaises(EngineError) as raised:
            replay(result["replay_manifest"], changed)
        self.assertEqual("REPLAY_INPUT_MISMATCH", raised.exception.code)

        tampered = deepcopy(result["replay_manifest"])
        tampered["domain_result_hashes"]["yijing_domain_hash"] = "sha256:" + "0" * 64
        tampered["content_hash"] = content_hash(
            {key: value for key, value in tampered.items() if key != "content_hash"}
        )
        with self.assertRaises(EngineError) as raised:
            replay(tampered, request)
        self.assertEqual("REPLAY_RESULT_MISMATCH", raised.exception.code)

        revoked = "yijing-three-coin-mechanical-0.1.0-revoked-fixture"
        self.assert_code("RULESET_REVOKED", request_for(bundle_id=revoked))
        historical = execute(request_for(bundle_id=revoked, mode="replay"))
        self.assertEqual(
            historical["output_hash"],
            replay(
                historical["replay_manifest"],
                request_for(bundle_id=revoked),
            )["output_hash"],
        )

    def test_ruleset_is_mechanical_research_only(self):
        bundle = inspect_ruleset("yijing-three-coin-mechanical-0.1.0")
        self.assertEqual("research_active", bundle["status"])
        self.assertEqual("traditional_mechanical", bundle["system_class"])
        self.assertFalse(bundle["production_activatable"])
        yijing = bundle["modules"]["yijing"]
        self.assertTrue(yijing["enabled"])
        self.assertFalse(yijing["production_activatable"])
        self.assertFalse(yijing["interpretation_enabled"])
        for module in ("bazi", "ziwei", "past-life", "bardo", "relationship", "life-chart"):
            self.assertFalse(bundle["modules"][module]["enabled"])

    def test_cross_platform_golden_fixture(self):
        fixture = json.loads(
            (
                ROOT
                / "packages/sanji-engine/src/sanji_engine/golden_cases/yijing/"
                "physical-three-coin-cross-platform-1.json"
            ).read_text("utf-8")
        )
        result = execute(request_for(tuple(fixture["input_line_values_bottom_to_top"])))
        expected = fixture["expected"]
        domain = result["module_results"]["yijing"]["result"]
        self.assertEqual(expected["output_hash"], result["output_hash"])
        self.assertEqual(expected["trace_hash"], result["trace_hash"])
        self.assertEqual(
            expected["yijing_domain_hash"],
            result["replay_manifest"]["domain_result_hashes"]["yijing_domain_hash"],
        )
        self.assertEqual(expected["base_hexagram"], domain["base_hexagram"])
        self.assertEqual(expected["transformed_hexagram"], domain["transformed_hexagram"])
        self.assertEqual(expected["moving_lines"], domain["moving_lines"])


if __name__ == "__main__":
    unittest.main()
