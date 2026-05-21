from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SCHEMAS = ROOT / "schemas"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class LaborCoordinationSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_json(SCHEMAS / "labor-coordination-record.schema.json")
        self.example = load_json(EXAMPLES / "labor-coordination-record.example.json")
        Draft202012Validator.check_schema(self.schema)
        self.validator = Draft202012Validator(self.schema)

    def test_example_validates_against_schema(self):
        self.validator.validate(self.example)

    def test_staffing_operation_requires_decision_card(self):
        record = copy.deepcopy(self.example)
        record.pop("decision_card")
        with self.assertRaisesRegex(Exception, "decision_card"):
            self.validator.validate(record)

    def test_non_staffing_operation_allows_missing_decision_card(self):
        record = copy.deepcopy(self.example)
        record["operation_type"] = "identity.claim.review"
        record.pop("decision_card")
        self.validator.validate(record)


if __name__ == "__main__":
    unittest.main()
