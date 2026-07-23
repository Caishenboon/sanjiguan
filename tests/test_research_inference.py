import json,unittest
from pathlib import Path
from packages.research_inference.engine import run_inference
from packages.research_inference.providers import DeepSeekProvider,EmbeddingProvider,FakeProvider,merge_prose

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"knowledge/research/scoring-config.json").read_text("utf-8"))
ARCHETYPES=json.loads((ROOT/"knowledge/research/inference-archetypes.json").read_text("utf-8"))
CASES=json.loads((ROOT/"tests/fixtures/sprint2-evaluation-cases.json").read_text("utf-8"))


def case_payload(spec,duplicate=False,oppose=False):
    tags=[spec["tag"]]+([spec["second_tag"]] if spec.get("second_tag") else [])
    signals=[]
    domains=["karma","vow","dream"]
    for i,tag in enumerate(tags):
        for j,domain in enumerate(domains):
            signals.append({"id":f"{spec['id']}-{i}-{j}","domain":domain,"tag":tag,
              "direction":"oppose" if oppose else "support","strength":.8,"source_reliability":.8,
              "relevance":.8,"independence_group":f"{spec['id']}-{i}-{j}",
              "ordinary_explanation_present":spec.get("ordinary",False)})
    if duplicate:signals.append({**signals[0],"id":signals[0]["id"]+"-duplicate"})
    return {"mode":"research_preview","synthetic_or_research":True,"random_seed":42,
            "completeness":spec.get("completeness",.9),"claim_snapshot":[],"signals":signals}


class ResearchInferenceTests(unittest.TestCase):
    def test_thirty_fully_synthetic_cases(self):
        self.assertEqual(30,len(CASES))
        self.assertEqual({"clear":10,"contested":8,"insufficient":6,"ordinary":6},
          {g:sum(c["group"]==g for c in CASES) for g in ("clear","contested","insufficient","ordinary")})
        for spec in CASES:
            result=run_inference(case_payload(spec),ARCHETYPES,CONFIG)
            self.assertEqual("research_preview",result["locked_verdict"]["status"])
            self.assertEqual(5,len(result["locked_verdict"]["ranked_hypotheses"]))
            self.assertTrue(any(h["category"]=="ordinary_livelihood"
              for h in result["locked_verdict"]["ranked_hypotheses"]))
            self.assertNotIn("probability",json.dumps(result))
            if spec["group"]=="insufficient":self.assertEqual("insufficient",result["locked_verdict"]["verdict"])

    def test_determinism_and_duplicate_resistance(self):
        payload=case_payload(CASES[3])
        first=run_inference(payload,ARCHETYPES,CONFIG)
        second=run_inference(payload,ARCHETYPES,CONFIG)
        duplicated=run_inference(case_payload(CASES[3],duplicate=True),ARCHETYPES,CONFIG)
        self.assertEqual(first["locked_hash"],second["locked_hash"])
        self.assertEqual(first["locked_verdict"]["ranked_hypotheses"],duplicated["locked_verdict"]["ranked_hypotheses"])

    def test_counterevidence_really_reduces_score(self):
        positive=run_inference(case_payload(CASES[1]),ARCHETYPES,CONFIG)
        negative=run_inference(case_payload(CASES[1],oppose=True),ARCHETYPES,CONFIG)
        self.assertLess(negative["locked_verdict"]["ranked_hypotheses"][0]["raw_score"],
                        positive["locked_verdict"]["ranked_hypotheses"][0]["raw_score"])

    def test_mode_and_profile_boundary(self):
        payload=case_payload(CASES[0]);payload["mode"]="production"
        with self.assertRaisesRegex(ValueError,"research_preview"):run_inference(payload,ARCHETYPES,CONFIG)

    def test_fake_provider_and_locked_field_integrity(self):
        prose=FakeProvider().generate({})
        merged=merge_prose({"verdict":"provisional","rank":1},prose)
        self.assertEqual("provisional",merged["verdict"])
        with self.assertRaisesRegex(ValueError,"locked"):merge_prose({},{"verdict":"decisive"})

    def test_providers_default_safe(self):
        self.assertFalse(DeepSeekProvider().configured)
        with self.assertRaisesRegex(RuntimeError,"embedding_disabled"):EmbeddingProvider().embed(["x"])
