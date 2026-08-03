import unittest

from sanji_engine import execute


class BaziTraditionalStructureCrossPlatformTests(unittest.TestCase):
    def test_fixed_output_trace_and_domain_hashes(self):
        request = {
            "schema_version": "engine-request/1.0.0", "engine_api_version": "1.0",
            "run_id": "bazi-structure-test", "run_mode": "research_preview", "requested_modules": ["bazi"],
            "input_snapshot": {
                "operation": "calculate_bazi_traditional_structure",
                "profile_id": "bazi-traditional-structure-research-v1", "profile_version": "1.0.0",
                "hidden_stems_profile_id": "hidden-stems-primary-secondary-residual-candidate-v1",
                "source_four_pillars": {
                    "year": {"stem": "甲", "branch": "子"}, "month": {"stem": "己", "branch": "巳"},
                    "day": {"stem": "甲", "branch": "申"}, "hour": {"stem": "庚", "branch": "辰"},
                },
                "source_candidate_id": "synthetic-candidate-001",
                "source_ruleset_id": "bazi-four-pillars-research-1.0.0",
                "source_method_id": "BAZI.FOUR_PILLARS.MECHANICAL.RESEARCH.V1",
                "source_method_version": "1.0.0",
                "month_context": {"solar_month_index": 4, "boundary_sensitive": False},
            },
            "ruleset_bundle_id": "bazi-traditional-structure-research-1.0.0",
            "data_versions": {
                "tzdb": "2025.2", "ephemeris": "astronomy-engine/2.1.19",
                "calendar_dataset": "calendar-migration-baseline-1.0.0",
                "bazi_method_profiles": "bazi-traditional-structure-profiles/1.0.0",
                "bazi_traditional_structure": "bazi-traditional-structure-assets/1.0.0",
            },
            "deterministic_context": {"as_of": "2000-01-01T00:00:00Z", "random_method": "none", "random_seed": None},
        }
        result = execute(request)
        self.assertEqual("sha256:4d4a3acfdd3c613e4bbc90a341f368ed9a4982e39f057af19bca9a9a18394732", result["output_hash"])
        self.assertEqual("sha256:de612316797fad52deb4e2297f4407fab1759557488a3d86f81232bbfaa1fbd5", result["trace_hash"])
        self.assertEqual("sha256:2ed23f6538b06daa4ed9fc0d67b2cbb812e6853ad150a059484534ced9ffac62", result["module_results"]["bazi"]["result"]["result_hash"])


if __name__ == "__main__":
    unittest.main()
