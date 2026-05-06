from __future__ import annotations

import copy
import unittest
from pathlib import Path

from holographme.projection import generate_projection
from holographme.regis_export import RegisExportError, export_twin_projection_features
from holographme.projection import load_json


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


class RegisExportTests(unittest.TestCase):
    def setUp(self):
        self.twin = load_json(EXAMPLES / "human-digital-twin.example.json")
        self.consent = load_json(EXAMPLES / "consent-policy.example.json")
        self.mission = load_json(EXAMPLES / "mission.example.json")
        self.generated = generate_projection(
            self.twin,
            self.consent,
            self.mission,
            now="2026-05-04T18:30:00Z",
            receipt_id="tr_projection_001",
            decision_log_id="pdl_projection_001",
        )

    def test_exports_allowed_projection_fields(self):
        features = export_twin_projection_features(
            self.generated["projection"],
            self.generated["decision_log"],
            consent=self.consent,
            mission=self.mission,
            receipt=self.generated["receipt"],
            created_at="2026-05-04T18:31:00Z",
        )

        self.assertGreater(len(features), 0)
        names = {feature["feature_name"] for feature in features}
        self.assertIn("subject.display_name", names)
        self.assertIn("capability_claims.capability", names)
        self.assertNotIn("assessments.summary", names)

        first = features[0]
        self.assertEqual(first["projection_id"], self.generated["projection"]["projection_id"])
        self.assertEqual(first["projection_decision_log_ref"]["decision_log_id"], "pdl_projection_001")
        self.assertEqual(first["transition_receipt_ref"]["receipt_id"], "tr_projection_001")
        self.assertEqual(first["consent_scope_snapshot"]["policy_id"], self.consent["policy_id"])
        self.assertEqual(first["mission_governance_snapshot"]["authority_band"], "recommend")
        self.assertEqual(first["effective_authority_band"], "recommend")
        self.assertEqual(first["policy_state"], "allowed")

    def test_mismatched_decision_log_is_rejected(self):
        bad_decision_log = copy.deepcopy(self.generated["decision_log"])
        bad_decision_log["projection_id"] = "proj_wrong"

        with self.assertRaisesRegex(RegisExportError, "projection_id mismatch"):
            export_twin_projection_features(self.generated["projection"], bad_decision_log)

    def test_expired_consent_marks_features_blocked(self):
        consent = copy.deepcopy(self.consent)
        consent["expires_at"] = "2026-05-01T00:00:00Z"

        features = export_twin_projection_features(
            self.generated["projection"],
            self.generated["decision_log"],
            consent=consent,
            mission=self.mission,
            receipt=self.generated["receipt"],
            created_at="2026-05-04T18:31:00Z",
        )

        self.assertTrue(features)
        self.assertTrue(all(feature["revocation_state"] == "expired" for feature in features))
        self.assertTrue(all(feature["policy_state"] == "blocked" for feature in features))

    def test_authority_downgrades_to_consent_max(self):
        consent = copy.deepcopy(self.consent)
        consent.setdefault("delegation", {})["max_authority_band"] = "observe"

        features = export_twin_projection_features(
            self.generated["projection"],
            self.generated["decision_log"],
            consent=consent,
            mission=self.mission,
            receipt=self.generated["receipt"],
            created_at="2026-05-04T18:31:00Z",
        )

        self.assertTrue(features)
        self.assertTrue(all(feature["effective_authority_band"] == "observe" for feature in features))

    def test_consent_policy_mismatch_is_rejected(self):
        consent = copy.deepcopy(self.consent)
        consent["policy_id"] = "cp_wrong"

        with self.assertRaisesRegex(RegisExportError, "policy_id mismatch"):
            export_twin_projection_features(
                self.generated["projection"],
                self.generated["decision_log"],
                consent=consent,
            )


if __name__ == "__main__":
    unittest.main()
