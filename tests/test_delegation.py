from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from holographme.delegation import authority_allows, check_delegation


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class DelegationTests(unittest.TestCase):
    def setUp(self):
        self.twin = load_json(EXAMPLES / "human-digital-twin.example.json")

    def test_authority_order(self):
        self.assertTrue(authority_allows("recommend", "observe"))
        self.assertTrue(authority_allows("recommend", "recommend"))
        self.assertFalse(authority_allows("recommend", "represent"))
        self.assertFalse(authority_allows("unknown", "observe"))

    def test_allows_delegated_action_inside_band(self):
        decision = check_delegation(
            self.twin,
            agent_id="agent_intake_001",
            requested_action="recommend_missions",
            required_band="recommend",
            now="2026-05-04T18:30:00Z",
        )

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "allowed")
        self.assertEqual(decision["authority_band"], "recommend")

    def test_rejects_unknown_agent(self):
        decision = check_delegation(
            self.twin,
            agent_id="agent_unknown",
            requested_action="recommend_missions",
            required_band="recommend",
            now="2026-05-04T18:30:00Z",
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "agent_not_delegated")

    def test_rejects_action_not_allowed(self):
        decision = check_delegation(
            self.twin,
            agent_id="agent_intake_001",
            requested_action="accept_mission",
            required_band="commit",
            now="2026-05-04T18:30:00Z",
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "action_not_allowed")
        self.assertIn("recommend_missions", decision["allowed_actions"])

    def test_rejects_insufficient_authority(self):
        twin = copy.deepcopy(self.twin)
        twin["delegated_agents"][0]["allowed_actions"].append("answer_screening_questions")

        decision = check_delegation(
            twin,
            agent_id="agent_intake_001",
            requested_action="answer_screening_questions",
            required_band="represent",
            now="2026-05-04T18:30:00Z",
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "insufficient_authority")
        self.assertEqual(decision["authority_band"], "recommend")

    def test_rejects_expired_delegation(self):
        twin = copy.deepcopy(self.twin)
        twin["delegated_agents"][0]["expires_at"] = "2026-05-01T00:00:00Z"

        decision = check_delegation(
            twin,
            agent_id="agent_intake_001",
            requested_action="recommend_missions",
            required_band="recommend",
            now="2026-05-04T18:30:00Z",
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "delegation_expired")


if __name__ == "__main__":
    unittest.main()
