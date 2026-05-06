"""Capability claim event helpers for HolographMe."""

from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


class CapabilityEventError(ValueError):
    """Raised when a capability claim event is invalid."""


TERMINAL_STATUSES = {"retired"}

LEGAL_TRANSITIONS = {
    (None, "claim_created", "self_attested"),
    ("self_attested", "evidence_attached", "evidence_attached"),
    ("self_attested", "status_changed", "disputed"),
    ("evidence_attached", "review_recorded", "verified"),
    ("evidence_attached", "status_changed", "disputed"),
    ("verified", "status_changed", "disputed"),
    ("disputed", "review_recorded", "verified"),
    ("disputed", "status_changed", "evidence_attached"),
    ("expired", "evidence_attached", "evidence_attached"),
    ("expired", "status_changed", "disputed"),
}

RETIREABLE_STATUSES = {"self_attested", "evidence_attached", "verified", "disputed", "expired"}
EXPIRABLE_STATUSES = {"self_attested", "evidence_attached", "verified", "disputed"}


def find_claim(twin: Mapping[str, Any], claim_id: str) -> Optional[Mapping[str, Any]]:
    for claim in twin.get("capability_claims", []):
        if claim.get("claim_id") == claim_id:
            return claim
    return None


def event_ids(event_log: Mapping[str, Any]) -> List[str]:
    return [str(event.get("event_id")) for event in event_log.get("events", [])]


def claim_state_from_events(event_log: Mapping[str, Any]) -> Dict[str, Any]:
    """Derive current claim state from an event log."""

    status: Optional[str] = None
    confidence: Optional[str] = None
    evidence_ids: List[str] = []

    for event in event_log.get("events", []):
        expected_before = event.get("status_before")
        if expected_before is not None and expected_before != status:
            raise CapabilityEventError(
                f"event {event.get('event_id')} status_before={expected_before} does not match current status={status}"
            )

        validate_transition(status, str(event.get("event_type")), str(event.get("status_after")))
        status = str(event.get("status_after"))
        confidence = event.get("confidence_after", confidence)

        for evidence_id in event.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                evidence_ids.append(str(evidence_id))

    if status is None:
        raise CapabilityEventError("capability claim event log has no events")

    return {
        "claim_id": event_log["claim_id"],
        "verification_status": status,
        "confidence": confidence,
        "evidence_ids": evidence_ids,
    }


def validate_transition(status_before: Optional[str], event_type: str, status_after: str) -> None:
    """Validate a capability claim lifecycle transition."""

    if status_before in TERMINAL_STATUSES:
        raise CapabilityEventError("retired capability claims are terminal")

    if event_type == "claim_expired":
        if status_before not in EXPIRABLE_STATUSES or status_after != "expired":
            raise CapabilityEventError(f"illegal expiration transition: {status_before} -> {status_after}")
        return

    if event_type == "claim_retired":
        if status_before not in RETIREABLE_STATUSES or status_after != "retired":
            raise CapabilityEventError(f"illegal retirement transition: {status_before} -> {status_after}")
        return

    if (status_before, event_type, status_after) not in LEGAL_TRANSITIONS:
        raise CapabilityEventError(f"illegal capability transition: {status_before} / {event_type} -> {status_after}")


def validate_next_event(event_log: Mapping[str, Any], event: Mapping[str, Any]) -> None:
    current = claim_state_from_events(event_log)
    status_before = event.get("status_before")
    if status_before != current["verification_status"]:
        raise CapabilityEventError(
            f"next event status_before={status_before} does not match current status={current['verification_status']}"
        )
    validate_transition(current["verification_status"], str(event.get("event_type")), str(event.get("status_after")))


def append_claim_event(event_log: Mapping[str, Any], event: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of the event log with one validated event appended."""

    if event.get("event_id") in event_ids(event_log):
        raise CapabilityEventError(f"duplicate event_id: {event.get('event_id')}")

    validate_next_event(event_log, event)
    updated = copy.deepcopy(dict(event_log))
    updated.setdefault("events", []).append(copy.deepcopy(dict(event)))
    return updated


def apply_event_log_to_twin(twin: Mapping[str, Any], event_log: Mapping[str, Any]) -> Dict[str, Any]:
    """Apply the derived capability state to the matching claim in a twin copy."""

    state = claim_state_from_events(event_log)
    updated = copy.deepcopy(dict(twin))
    claim_id = str(state["claim_id"])

    for claim in updated.get("capability_claims", []):
        if claim.get("claim_id") != claim_id:
            continue
        claim["verification_status"] = state["verification_status"]
        if state.get("confidence") is not None:
            claim["confidence"] = state["confidence"]
        return updated

    raise CapabilityEventError(f"claim not found in twin: {claim_id}")
