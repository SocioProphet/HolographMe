"""Capability claim event helpers for HolographMe."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional


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


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def build_claim_event_receipt(
    twin: Mapping[str, Any],
    before_event_log: Mapping[str, Any],
    after_event_log: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    receipt_id: Optional[str] = None,
    approval_band: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a transition receipt for an appended capability claim event."""

    claim_id = str(after_event_log["claim_id"])
    event_id = str(event["event_id"])
    actor = copy.deepcopy(dict(event.get("actor", {"actor_id": "unknown", "actor_type": "system"})))
    evidence_links = [str(after_event_log.get("event_log_id", "cce_unknown")), claim_id, event_id]
    evidence_links.extend(str(evidence_id) for evidence_id in event.get("evidence_ids", []))

    return {
        "schema_version": "0.1.0",
        "receipt_id": receipt_id or f"tr_{event_id}",
        "twin_id": str(twin["twin_id"]),
        "action": "capability_claim_event_appended",
        "actor": actor,
        "timestamp": str(event.get("timestamp", now_utc_iso())),
        "policy_version": "0.1.0",
        "previous_state_hash": canonical_hash(before_event_log),
        "new_state_hash": canonical_hash(after_event_log),
        "evidence_links": evidence_links,
        "approval_band": approval_band or ("commit" if event.get("event_type") == "claim_retired" else "recommend"),
        "details": {
            "claim_id": claim_id,
            "event_id": event_id,
            "event_type": str(event.get("event_type")),
            "status_before": str(event.get("status_before", "")),
            "status_after": str(event.get("status_after")),
            "confidence_before": str(event.get("confidence_before", "")),
            "confidence_after": str(event.get("confidence_after", "")),
        },
        "rollback": {
            "rollback_supported": False,
            "rollback_method": "append_compensating_event_or_retire_claim",
            "irreversible_acknowledged": True,
        },
        "replay_hints": {
            "transition_library_version": "0.1.0",
            "input_snapshot_uri": f"urn:holographme:capability-event:{event_id}",
            "runtime_version": "holographme-capability-runtime-0.1.0",
        },
    }


def append_claim_event_with_receipt(
    twin: Mapping[str, Any],
    event_log: Mapping[str, Any],
    event: Mapping[str, Any],
    *,
    receipt_id: Optional[str] = None,
    approval_band: Optional[str] = None,
    apply_to_twin: bool = False,
) -> Dict[str, Any]:
    """Append a capability event and emit a receipt.

    When apply_to_twin is true, a copy of the twin with the derived claim status
    is included in the result. The original input is not mutated.
    """

    if str(twin.get("twin_id")) != str(event_log.get("twin_id")):
        raise CapabilityEventError("event log twin_id does not match twin")

    if find_claim(twin, str(event_log.get("claim_id"))) is None:
        raise CapabilityEventError(f"claim not found in twin: {event_log.get('claim_id')}")

    updated_log = append_claim_event(event_log, event)
    receipt = build_claim_event_receipt(
        twin,
        event_log,
        updated_log,
        event,
        receipt_id=receipt_id,
        approval_band=approval_band,
    )
    result: Dict[str, Any] = {"event_log": updated_log, "receipt": receipt}
    if apply_to_twin:
        result["twin"] = apply_event_log_to_twin(twin, updated_log)
    return result


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
