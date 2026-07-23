import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, RefResolver

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "packages/shared-types/schemas"
schema = json.loads((SCHEMAS / "verdict.schema.json").read_text(encoding="utf-8"))
store = {
    json.loads(path.read_text(encoding="utf-8"))["$id"]: json.loads(path.read_text(encoding="utf-8"))
    for path in SCHEMAS.glob("*.schema.json")
}
resolver = RefResolver.from_schema(schema, store=store)
validator = Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())


class VerdictSchemaTests(unittest.TestCase):
    def setUp(self):
        self.item = json.loads((ROOT / "tests/fixtures/demo-verdict.json").read_text(encoding="utf-8"))

    def invalid(self, mutate):
        item = copy.deepcopy(self.item)
        mutate(item)
        self.assertTrue(list(validator.iter_errors(item)))

    def test_complete_fixture_passes(self):
        validator.validate(self.item)

    def test_required_and_ranges(self):
        for field in ("verdict", "polarity"):
            self.invalid(lambda x, f=field: x.pop(f))
        self.invalid(lambda x: x.update(strength=101))
        self.invalid(lambda x: x.update(evidence_ids=["not-a-uuid"]))

    def test_mixed_requires_dominant_side(self):
        self.invalid(lambda x: x["judgement"].update(dominant_side="balanced"))

    def test_contested_requires_two_alternatives(self):
        self.invalid(lambda x: x.update(status="contested", alternatives=[]))

    def test_insufficient_requires_reason(self):
        self.invalid(lambda x: x.update(status="insufficient", insufficiency_reason=None))

    def test_exact_timing_requires_dates(self):
        self.invalid(lambda x: x["manifestation_period"].update(precision="exact"))

    def test_decisive_rejects_evasive_verdict(self):
        for word in ("可能", "也许", "似乎", "大概", "或许", "一切皆有可能"):
            self.invalid(lambda x, w=word: x.update(status="decisive", verdict=f"{w}存在某种影响。"))

    def test_llm_prose_requires_prompt_and_template_forbids_it(self):
        self.invalid(lambda x: x["provenance"].update(prose_source="llm"))
        self.invalid(lambda x: x.update(prompt_version="p1"))

    def test_human_override_requires_audit_provenance(self):
        self.invalid(lambda x: x["provenance"].update(verdict_source="human_override"))

    def test_insufficient_forbids_precise_timing(self):
        self.invalid(lambda x: x.update(
            status="insufficient", insufficiency_reason="资料不足",
            manifestation_period={**x["manifestation_period"], "precision": "exact",
                                  "from_date": "2026-01-01", "to_date": "2026-01-01"}))

    def test_decisive_neutral_requires_reason(self):
        self.invalid(lambda x: x.update(status="decisive", polarity="neutral", neutral_reason=None))
