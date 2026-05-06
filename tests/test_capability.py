from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from holographme.capability import (
    CapabilityEventError,
    append_claim_event,
    append_claim_event_with_receipt,
    apply_event_log_to_twin,
    claim_state_from_events,
    validate_transition,
)


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SCHEMAS = ROOT / "schemas"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class CapabilityEventTests(unittest.TestCase):
    def setUp(self):
        self.twin = load_json(EXAMPLES / "human-digital-twin.example.json")
        self.event_log = load_json(EXAMPLES / "capability-claim-event.example.json")

    def test_event_log_validates_against_schema(self):
        schema = load_json(SCHEMAS / "capability-claim-event.schema.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(self.event_log)

    def test_derives_claim_state_from_events(self):
        state = claim_state_from_events(self.event_log)

        self.assertEqual(state["claim_id"], "claim_agentic_systems_001")
        self.assertEqual(state["verification_status"], "verified")
        self.assertEqual(state["confidence"], "high")
        self.assertEqual(state["evidence_ids"], ["ev_repo_001"])

    def test_apply_event_log_to_twin_updates_matching_claim(self):
        updated = apply_event_log_to_twin(self.twin, self.event_log)
        claim = updated["capability_claims"][0]

        self.assertEqual(claim["claim_id"], "claim_agentic_systems_001")
        self.assertEqual(claim["verification_status"], "verified")
        self.assertEqual(claim["confidence"], "high")

    def test_append_event_with_receipt_and_twin_update(self):
        event = load_json(EXAMPLES / "capability-claim-event.append.example.json")
        result = append_claim_event_with_receipt(
            self.twin,
            self.event_log,
            event,
            receipt_id="tr_ccev_claim_expired_001",
            apply_to_twin=True,
        )

        updated_log = result["event_log"]
        receipt = result["receipt"]
        updated_twin = result["twin"]

        self.assertEqual(updated_log["events"][-1]["event_id"], "ccev_claim_expired_001")
        self.assertEqual(claim_state_from_events(updated_log)["verification_status"], "expired")
        self.assertEqual(receipt["action"], "capability_claim_event_appended")
        self.assertEqual(receipt["details"]["claim_id"], "claim_agentic_systems_001")
        self.assertEqual(receipt["details"]["event_id"], "ccev_claim_expired_001")
        self.assertEqual(receipt["details"]["status_before"], "verified")
        self.assertEqual(receipt["details"]["status_after"], "expired")
        self.assertEqual(updated_twin["capability_claims"][0]["verification_status"], "expired")

        event_log_schema = load_json(SCHEMAS / "capability-claim-event.schema.json")
        receipt_schema = load_json(SCHEMAS / "transition-receipt.schema.json")
        twin_schema = load_json(SCHEMAS / "human-digital-twin.schema.json")
        Draft202012Validator(event_log_schema).validate(updated_log)
        Draft202012Validator(receipt_schema).validate(receipt)
        Draft202012Validator(twin_schema).validate(updated_twin)

    def test_append_retirement_event(self):
        retirement_event = {
            "event_id": "ccev_claim_retired_001",
            "event_type": "claim_retired",
            "timestamp": "2026-05-05T18:00:00Z",
            "actor": {"actor_id": "sub_example_alpha", "actor_type": "subject"},
            "status_before": "verified",
            "status_after": "retired",
            "confidence_before": "high",
            "confidence_after": "high",
            "summary": "Subject retired this capability claim from active mission-fit use.",
        }

        updated_log = append_claim_event(self.event_log, retirement_event)
        state = claim_state_from_events(updated_log)

        self.assertEqual(state["verification_status"], "retired")
        self.assertEqual(updated_log["events"][-1]["event_type"], "claim_retired")

    def test_retired_claim_is_terminal(self):
        retirement_event = {
            "event_id": "ccev_claim_retired_001",
            "event_type": "claim_retired",
            "timestamp": "2026-05-05T18:00:00Z",
            "actor": {"actor_id": "sub_example_alpha", "actor_type": "subject"},
            "status_before": "verified",
            "status_after": "retired",
            "confidence_before": "high",
            "confidence_after": "high",
        }
        updated_log = append_claim_event(self.event_log, retirement_event)
        forbidden_event = {
            "event_id": "ccev_evidence_after_retirement_001",
            "event_type": "evidence_attached",
            "timestamp": "2026-05-06T18:00:00Z",
            "actor": {"actor_id": "agent_intake_001", "actor_type": "agent"},
            "status_before": "retired",
            "status_after": "evidence_attached",
            "confidence_before": "high",
            "confidence_after": "high",
            "evidence_ids": ["ev_repo_001"],
        }

        with self.assertRaisesRegex(CapabilityEventError, "terminal"):
            append_claim_event(updated_log, forbidden_event)

    def test_rejects_duplicate_event_id(self):
        duplicate = copy.deepcopy(self.event_log["events"][-1])

        with self.assertRaisesRegex(CapabilityEventError, "duplicate"):
            append_claim_event(self.event_log, duplicate)

    def test_rejects_illegal_transition(self):
        with self.assertRaisesRegex(CapabilityEventError, "illegal"):
            validate_transition("self_attested", "review_recorded", "verified")

    def test_rejects_status_before_mismatch(self):
        event = {
            "event_id": "ccev_bad_before_001",
            "event_type": "claim_retired",
            "timestamp": "2026-05-05T18:00:00Z",
            "actor": {"actor_id": "sub_example_alpha", "actor_type": "subject"},
            "status_before": "self_attested",
            "status_after": "retired",
        }

        with self.assertRaisesRegex(CapabilityEventError, "status_before"):
            append_claim_event(self.event_log, event)

    def test_rejects_twin_claim_mismatch(self):
        twin = copy.deepcopy(self.twin)
        twin["capability_claims"] = []
        event = load_json(EXAMPLES / "capability-claim-event.append.example.json")

        with self.assertRaisesRegex(CapabilityEventError, "claim not found"):
            append_claim_event_with_receipt(twin, self.event_log, event)


if __name__ == "__main__":
    unittest.main()
