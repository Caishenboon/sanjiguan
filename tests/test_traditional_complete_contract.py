import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class TraditionalCompleteContractTests(unittest.TestCase):
 def test_private_persistence_forces_rls(self):
    sql=(ROOT/"infra/migrations/0021_traditional_algorithms_complete_v1.sql").read_text(encoding="utf-8")
    self.assertIn("FORCE ROW LEVEL SECURITY",sql)
    self.assertIn("owner_id=app_current_user_id()",sql)
    self.assertIn("production_activatable boolean NOT NULL DEFAULT false CHECK (NOT production_activatable)",sql)

 def test_all_new_rulesets_are_research_only(self):
    directory=ROOT/"packages/sanji-engine/src/sanji_engine/rulesets"
    for name in ("bazi-ziping-complete-1.0.0.json","ziwei-sanhe-complete-1.0.0.json","liuyao-jingfang-najia-1.0.0.json","sanji-traditional-composite-1.0.0.json"):
        value=json.loads((directory/name).read_text(encoding="utf-8"))
        self.assertEqual(value["status"],"research_active")
        self.assertEqual(value["review_status"],"UNCONFIRMED")
        self.assertFalse(value["production_activatable"])

 def test_core_and_adapters_have_no_llm_dependency(self):
    text="\n".join((ROOT/path).read_text(encoding="utf-8") for path in (
      "packages/upstream-adapters/src/upstream_adapters/complete.py",
      "packages/sanji-engine/src/sanji_engine/traditional_complete/v1.py"))
    for forbidden in ("DEEPSEEK_API_KEY","openai","anthropic","requests.post","httpx"):
        self.assertNotIn(forbidden,text)

 def test_openapi_has_lifecycle_endpoints(self):
    api=json.loads((ROOT/"docs/api/traditional-algorithms-complete.openapi.json").read_text(encoding="utf-8"))
    paths=api["paths"]
    self.assertIn("/api/v1/admin/research/traditional-complete/execute",paths)
    self.assertIn("/api/v1/admin/research/traditional-complete/{run_id}/replay",paths)
    self.assertIn("/api/v1/admin/research/traditional-complete/{run_id}/reanalyze",paths)
    self.assertIn("/api/v1/admin/research/traditional-complete/{left_run_id}/compare/{right_run_id}",paths)
    self.assertIn("/api/v1/traditional-complete/execute",paths)
    self.assertIn("/api/v1/traditional-complete/{run_id}/replay",paths)
    self.assertIn("/api/v1/traditional-complete/{run_id}/reanalyze",paths)
    self.assertIn("/api/v1/traditional-complete/{left_run_id}/compare/{right_run_id}",paths)


if __name__=="__main__": unittest.main()
