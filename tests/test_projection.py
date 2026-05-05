from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from holographme.projection import ProjectionError, ProjectionRejected, generate_projection


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SCHEMAS = ROOT / "schemas"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.twin = load_json(EXAMPLES / "human-digital-twin.example.json")
        self.consent = load_json(EXAMPLES / "consent-policy.example.json")
        self.mission = load_json(EXAMPLES / "mission.example.json")

    def test_generates_consent_scoped_projection(self):
        result = generate_projection(
            self.twin,
            self.consent,
            self.mission,
            now="2026-05-04T18:30:00Z",
            receipt_id="tr_projection_001",
            decision_log_id="pdl_projection_001",
        )

        projection = result["projection"]
        receipt = result["receipt"]
        decision_log = result["decision_log"]

        self.assertEqual(projection["purpose"], "mission_fit")
        self.assertEqual(projection["data"]["subject"]["display_name"], "Example Operator")
        self.assertNotIn("preferred_contact", projection["data"]["subject"])
        self.assertEqual(
            projection["data"]["capability_claims"][0],
            {
                "capability": "Agentic systems design",
                "level": "practitioner",
                "verification_status": "evidence_attached",
            },
        )
        self.assertEqual(
            projection["denied_fields"],
            [{"field": "assessments.summary", "reason": "not_allowed_by_consent_policy"}],
        )
        self.assertEqual(receipt["action"], "mission_fit_projection")
        self.assertEqual(receipt["approval_band"], "recommend")
        self.assertIn("pdl_projection_001", receipt["evidence_links"])
        self.assertTrue(receipt["new_state_hash"].startswith("sha256:"))

        self.assertEqual(decision_log["decision_log_id"], "pdl_projection_001")
        self.assertEqual(decision_log["projection_id"], projection["projection_id"])
        self.assertEqual(decision_log["decisions"][-1]["decision"], "deny")
        self.assertEqual(decision_log["decisions"][-1]["field"], "assessments.summary")

    def test_projection_receipt_and_decision_log_validate_against_schemas(self):
        result = generate_projection(
            self.twin,
            self.consent,
            self.mission,
            now="2026-05-04T18:30:00Z",
            receipt_id="tr_projection_001",
            decision_log_id="pdl_projection_001",
        )

        projection_schema = load_json(SCHEMAS / "projection.schema.json")
        receipt_schema = load_json(SCHEMAS / "transition-receipt.schema.json")
        decision_log_schema = load_json(SCHEMAS / "projection-decision-log.schema.json")

        Draft202012Validator.check_schema(projection_schema)
        Draft202012Validator(projection_schema).validate(result["projection"])
        Draft202012Validator(receipt_schema).validate(result["receipt"])
        Draft202012Validator(decision_log_schema).validate(result["decision_log"])

    def test_decision_log_records_missing_fields(self):
        consent = copy.deepcopy(self.consent)
        consent["allowed_fields"].append("preferences.nonexistent")
        mission = copy.deepcopy(self.mission)
        mission["projection_request"]["requested_fields"] = ["preferences.nonexistent"]

        result = generate_projection(
            self.twin,
            consent,
            mission,
            now="2026-05-04T18:30:00Z",
            receipt_id="tr_projection_missing_001",
            decision_log_id="pdl_projection_missing_001",
        )

        self.assertEqual(
            result["projection"]["denied_fields"],
            [{"field": "preferences.nonexistent", "reason": "field_missing_from_twin"}],
        )
        self.assertEqual(result["decision_log"]["decisions"][0]["decision"], "deny")
        self.assertEqual(result["decision_log"]["decisions"][0]["reason"], "field_missing_from_twin")

    def test_rejected_expired_consent_has_decision_log(self):
        consent = copy.deepcopy(self.consent)
        consent["expires_at"] = "2026-05-01T00:00:00Z"

        with self.assertRaisesRegex(ProjectionRejected, "consent_policy_expired") as raised:
            generate_projection(
                self.twin,
                consent,
                self.mission,
                now="2026-05-04T18:30:00Z",
                decision_log_id="pdl_rejected_expired_001",
            )

        decision_log = raised.exception.decision_log
        self.assertEqual(decision_log["decision_log_id"], "pdl_rejected_expired_001")
        self.assertEqual(decision_log["decisions"][0]["reason"], "consent_policy_expired")

    def test_rejected_mismatched_recipient_has_decision_log(self):
        mission = copy.deepcopy(self.mission)
        mission["sponsor"]["recipient_id"] = "recipient_untrusted"

        with self.assertRaisesRegex(ProjectionRejected, "recipient_not_allowed") as raised:
            generate_projection(
                self.twin,
                self.consent,
                mission,
                now="2026-05-04T18:30:00Z",
                decision_log_id="pdl_rejected_recipient_001",
            )

        self.assertEqual(raised.exception.decision_log["decisions"][0]["reason"], "recipient_not_allowed")

    def test_rejected_mismatched_subject_has_decision_log(self):
        consent = copy.deepcopy(self.consent)
        consent["subject_id"] = "sub_other"

        with self.assertRaisesRegex(ProjectionRejected, "subject_mismatch") as raised:
            generate_projection(
                self.twin,
                consent,
                self.mission,
                now="2026-05-04T18:30:00Z",
                decision_log_id="pdl_rejected_subject_001",
            )

        self.assertEqual(raised.exception.decision_log["decisions"][0]["reason"], "subject_mismatch")

    def test_rejected_purpose_has_decision_log(self):
        mission = copy.deepcopy(self.mission)
        mission["projection_request"]["purpose"] = "unapproved_purpose"

        with self.assertRaisesRegex(ProjectionRejected, "purpose_not_allowed") as raised:
            generate_projection(
                self.twin,
                self.consent,
                mission,
                now="2026-05-04T18:30:00Z",
                decision_log_id="pdl_rejected_purpose_001",
            )

        self.assertEqual(raised.exception.decision_log["decisions"][0]["reason"], "purpose_not_allowed")

    def test_field_forbidden_by_policy_is_logged(self):
        consent = copy.deepcopy(self.consent)
        consent["allowed_fields"].append("subject.preferred_contact")
        consent["forbidden_fields"].append("subject.preferred_contact")
        mission = copy.deepcopy(self.mission)
        mission["projection_request"]["requested_fields"] = ["subject.preferred_contact"]

        result = generate_projection(
            self.twin,
            consent,
            mission,
            now="2026-05-04T18:30:00Z",
            receipt_id="tr_projection_forbidden_001",
            decision_log_id="pdl_projection_forbidden_001",
        )

        self.assertEqual(
            result["projection"]["denied_fields"],
            [{"field": "subject.preferred_contact", "reason": "forbidden_by_consent_policy"}],
        )
        self.assertEqual(result["decision_log"]["decisions"][0]["reason"], "forbidden_by_consent_policy")


if __name__ == "__main__":
    unittest.main()
