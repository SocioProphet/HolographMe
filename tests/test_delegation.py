from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from holographme.delegation import authority_allows, check_agent_operation_authority, check_delegation


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

    def test_rejects_revoked_delegation(self):
        twin = copy.deepcopy(self.twin)
        twin["delegated_agents"][0]["status"] = "revoked"
        twin["delegated_agents"][0]["revoked_at"] = "2026-05-03T00:00:00Z"

        decision = check_delegation(
            twin,
            agent_id="agent_intake_001",
            requested_action="recommend_missions",
            required_band="recommend",
            now="2026-05-04T18:30:00Z",
        )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "delegation_revoked")

    def test_agent_operation_authority_requires_policy_and_registry_checks(self):
        twin = copy.deepcopy(self.twin)
        twin["delegated_agents"][0]["allowed_actions"] = ["staffing.assignment.propose"]
        twin["delegated_agents"][0]["authority_band"] = "represent"

        denied_policy = check_agent_operation_authority(
            twin,
            agent_id="agent_intake_001",
            operation_type="staffing.assignment.propose",
            required_band="represent",
            policy_fabric_allowed=False,
            agent_registry_allowed=True,
            now="2026-05-04T18:30:00Z",
        )
        self.assertFalse(denied_policy["allowed"])
        self.assertEqual(denied_policy["reason"], "policy_fabric_check_required")

        denied_registry = check_agent_operation_authority(
            twin,
            agent_id="agent_intake_001",
            operation_type="staffing.assignment.propose",
            required_band="represent",
            policy_fabric_allowed=True,
            agent_registry_allowed=False,
            now="2026-05-04T18:30:00Z",
        )
        self.assertFalse(denied_registry["allowed"])
        self.assertEqual(denied_registry["reason"], "agent_registry_check_required")

    def test_agent_operation_authority_allows_when_all_boundaries_pass(self):
        twin = copy.deepcopy(self.twin)
        twin["delegated_agents"][0]["allowed_actions"] = ["staffing.assignment.propose"]
        twin["delegated_agents"][0]["authority_band"] = "represent"

        decision = check_agent_operation_authority(
            twin,
            agent_id="agent_intake_001",
            operation_type="staffing.assignment.propose",
            required_band="represent",
            policy_fabric_allowed=True,
            agent_registry_allowed=True,
            now="2026-05-04T18:30:00Z",
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["reason"], "allowed")

    def test_agent_operation_authority_rejects_unknown_operation(self):
        decision = check_agent_operation_authority(
            self.twin,
            agent_id="agent_intake_001",
            operation_type="staffing.assignment.hidden",
            required_band="observe",
            policy_fabric_allowed=True,
            agent_registry_allowed=True,
            now="2026-05-04T18:30:00Z",
        )
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "unsupported_operation_type")


if __name__ == "__main__":
    unittest.main()
