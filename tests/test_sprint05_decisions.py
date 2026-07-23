import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Sprint05DecisionTests(unittest.TestCase):
    def test_all_decisions_are_present_in_status_register(self):
        text = (ROOT / "docs/decision-register.md").read_text(encoding="utf-8")
        self.assertEqual(15, len(re.findall(r"^\| D-\d{3} \|", text, flags=re.MULTILINE)))

    def test_method_dossier_has_ten_decision_dimensions(self):
        text = (ROOT / "docs/decisions/method-selection-dossier.md").read_text(encoding="utf-8")
        for phrase in [
            "待决定的问题",
            "可选方案",
            "传统来源或权威参考",
            "会改变",
            "工程复杂度",
            "权威金样例",
            "目标适配性",
            "推荐默认方案",
            "其他方案能否配置",
            "不能自行认定",
        ]:
            self.assertIn(phrase, text)

    def test_source_register_has_trust_levels(self):
        text = (ROOT / "docs/decisions/source-register.md").read_text(encoding="utf-8")
        for level in ["A1", "A2", "B1", "B2", "C", "X"]:
            self.assertIn(f"**{level}**", text)

    def test_embedding_dimension_is_not_frozen(self):
        sql = (ROOT / "infra/migrations/0001_sprint0_baseline.sql").read_text(encoding="utf-8")
        self.assertNotRegex(sql, r"\bembedding\s+vector\(1024\)")
        self.assertIn("embedding_dimensions", sql)
        self.assertIn("embedding_model_id", sql)

    def test_rules_remain_disabled(self):
        manifest = json.loads((ROOT / "packages/rules/v1.0.0/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("draft", manifest["status"])
        self.assertFalse(manifest["production_activatable"])
        for method in manifest["methods"].values():
            self.assertFalse(method["enabled"])
            self.assertTrue(method["method_id"].endswith(".UNCONFIRMED"))

    def test_no_engine_implementation_files_were_added(self):
        engine = ROOT / "packages/engine"
        implementation_suffixes = {".py", ".ts", ".js", ".rs", ".go"}
        blocked_modules = {"bazi", "ziwei", "yijing", "karma", "bardo", "archetypes", "scoring", "timeline"}
        files = [
            path for path in engine.rglob("*")
            if path.is_file()
            and path.suffix in implementation_suffixes
            and any(part in blocked_modules for part in path.parts)
        ]
        self.assertEqual([], files)


if __name__ == "__main__":
    unittest.main()
