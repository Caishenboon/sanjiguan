import unittest
from packages.knowledge_governance.policy import archetype_errors, validate_claim, validate_research_rule


class KnowledgeGovernanceTests(unittest.TestCase):
    def test_locator_and_layer_guards(self):
        base = {"access_class":"citation_only","confidence":"verified","locator":{},
                "claim_type":"traditional_statement","source_excerpt":None,
                "allowed_uses":{"rag":False,"rule_authoring":False}}
        self.assertIn("verified_claim_requires_precise_locator",
                      validate_claim(base, {"knowledge_layer":"canonical_text"}))
        self.assertIn("system_interpretation_cannot_be_traditional_statement",
                      validate_claim({**base,"confidence":"uncertain"},
                                     {"knowledge_layer":"system_interpretation"}))

    def test_restricted_content_is_deny_by_default(self):
        claim={"access_class":"sealed","confidence":"uncertain","locator":{},
               "claim_type":"scholarly_interpretation","source_excerpt":"forbidden",
               "allowed_uses":{"rag":True,"rule_authoring":False}}
        errors=validate_claim(claim,{"knowledge_layer":"modern_scholarship"})
        self.assertIn("restricted_content_must_not_store_excerpt",errors)
        self.assertIn("restricted_or_unknown_not_allowed_for_rag_or_rules",errors)

    def test_rules_remain_research_only_and_need_counterevidence(self):
        rule={"status":"reviewed","counter_conditions":[],"missing_data_behavior":"block",
              "method_id":"UNCONFIRMED","production_activatable":False}
        errors=validate_research_rule(rule,[{"review_status":"approved"}])
        self.assertIn("reviewed_rule_requires_counterevidence",errors)

    def test_archetype_ordinary_ratio(self):
        base={"positive_evidence":["x"],"counterevidence":["x"],"ordinary_explanations":["x"],
              "misjudgment_risks":["x"]}
        records=[{**base,"name":str(i),"category":"ordinary_livelihood" if i<1 else "craft_art"} for i in range(5)]
        self.assertIn("ordinary_livelihood_below_one_quarter",archetype_errors(records))
