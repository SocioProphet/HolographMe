"""Regis Semantic Feature Plane export for HolographMe projections.

This module converts an already consent-scoped HolographMe Projection and
ProjectionDecisionLog into downstream TwinProjectionFeature records. It does
not read or export raw private twin state. The projection runtime owns consented
field selection; this module preserves the decision lineage, consent scope,
mission governance, transition receipt, retention, revocation, and authority
metadata needed by Regis gates.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from holographme.projection import canonical_hash, load_json, parse_instant, project_path, safe_slug, write_json


class RegisExportError(ValueError):
    """Raised when a projection cannot be safely exported to Regis."""


AUTHORITY_ORDER = ["observe", "recommend", "represent", "negotiate", "commit"]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def authority_rank(value: Optional[str]) -> int:
    if value not in AUTHORITY_ORDER:
        return 0
    return AUTHORITY_ORDER.index(value)


def minimum_authority(values: Iterable[Optional[str]]) -> str:
    present = [value for value in values if value]
    if not present:
        return "observe"
    return min(present, key=authority_rank)  # type: ignore[arg-type]


def ensure_match(left: Mapping[str, Any], right: Mapping[str, Any], keys: Sequence[str], right_name: str) -> None:
    for key in keys:
        if key in left and key in right and left[key] != right[key]:
            raise RegisExportError(f"{key} mismatch between projection and {right_name}")


def decision_by_field(decision_log: Mapping[str, Any]) -> Dict[str, Mapping[str, Any]]:
    result: Dict[str, Mapping[str, Any]] = {}
    for decision in decision_log.get("decisions", []):
        if isinstance(decision, Mapping) and "field" in decision:
            result[str(decision["field"])] = decision
    return result


def denied_field_set(projection: Mapping[str, Any], decision_log: Mapping[str, Any]) -> set[str]:
    denied = {str(item.get("field")) for item in projection.get("denied_fields", []) if isinstance(item, Mapping)}
    for decision in decision_log.get("decisions", []):
        if isinstance(decision, Mapping) and decision.get("decision") == "deny":
            denied.add(str(decision.get("field")))
    return denied


def infer_feature_family(field_path: str, value: Any) -> str:
    path = field_path.lower()
    if "capability" in path:
        return "capability"
    if "credential" in path:
        return "credential"
    if "preference" in path or "preferred" in path or "work_modes" in path:
        return "preference"
    if "constraint" in path or "availability" in path or "compensation" in path:
        return "constraint"
    if "delegated" in path or "agent" in path:
        return "delegation"
    if "assessment" in path:
        return "assessment"
    if "portfolio" in path or "evidence" in path or "proof" in path:
        return "proof"
    return "proof"


def consent_scope_snapshot(projection: Mapping[str, Any], consent: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {
        "policy_id": projection["policy_id"],
        "recipient_id": projection["recipient_id"],
        "purpose": projection["purpose"],
    }
    if consent:
        snapshot.update(
            {
                "subject_id": consent.get("subject_id"),
                "allowed_recipients": consent.get("allowed_recipients", []),
                "allowed_purposes": consent.get("allowed_purposes", []),
                "allowed_fields_digest": canonical_hash(consent.get("allowed_fields", [])),
                "forbidden_fields_digest": canonical_hash(consent.get("forbidden_fields", [])),
                "expires_at": consent.get("expires_at"),
                "retention_rule": consent.get("retention_rule"),
                "revocation": consent.get("revocation", {}),
                "delegation": consent.get("delegation", {}),
                "audit": consent.get("audit", {}),
            }
        )
    return snapshot


def mission_governance_snapshot(mission: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not mission:
        return {}
    governance = mission.get("governance", {}) if isinstance(mission.get("governance", {}), Mapping) else {}
    projection_request = mission.get("projection_request", {}) if isinstance(mission.get("projection_request", {}), Mapping) else {}
    return {
        "mission_id": mission.get("mission_id"),
        "authority_band": governance.get("authority_band"),
        "audit_required": governance.get("audit_required"),
        "human_approval_required": governance.get("human_approval_required"),
        "conformance_tags": governance.get("conformance_tags", []),
        "requested_fields": projection_request.get("requested_fields", []),
        "projection_request_expires_at": projection_request.get("expires_at"),
    }


def transition_receipt_ref(receipt: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    if not receipt:
        return None
    actor = receipt.get("actor", {}) if isinstance(receipt.get("actor", {}), Mapping) else {}
    rollback = receipt.get("rollback", {}) if isinstance(receipt.get("rollback", {}), Mapping) else {}
    replay_hints = receipt.get("replay_hints", {}) if isinstance(receipt.get("replay_hints", {}), Mapping) else {}
    return {
        "receipt_id": receipt.get("receipt_id"),
        "twin_id": receipt.get("twin_id"),
        "action": receipt.get("action"),
        "actor_id": actor.get("actor_id"),
        "actor_type": actor.get("actor_type"),
        "timestamp": receipt.get("timestamp"),
        "policy_version": receipt.get("policy_version"),
        "previous_state_hash": receipt.get("previous_state_hash"),
        "new_state_hash": receipt.get("new_state_hash"),
        "approval_band": receipt.get("approval_band"),
        "rollback_supported": rollback.get("rollback_supported"),
        "rollback_method": rollback.get("rollback_method"),
        "replay_hints": replay_hints,
    }


def compute_effective_authority(
    *,
    consent: Optional[Mapping[str, Any]],
    mission: Optional[Mapping[str, Any]],
    receipt: Optional[Mapping[str, Any]],
    policy_gate_authority: Optional[str] = None,
) -> str:
    consent_delegation = consent.get("delegation", {}) if consent and isinstance(consent.get("delegation", {}), Mapping) else {}
    mission_governance = mission.get("governance", {}) if mission and isinstance(mission.get("governance", {}), Mapping) else {}
    return minimum_authority(
        [
            consent_delegation.get("max_authority_band"),
            mission_governance.get("authority_band"),
            receipt.get("approval_band") if receipt else None,
            policy_gate_authority,
        ]
    )


def revocation_state(consent: Optional[Mapping[str, Any]], projection: Mapping[str, Any], now: str) -> str:
    if not consent:
        return "unknown"
    revocation = consent.get("revocation", {}) if isinstance(consent.get("revocation", {}), Mapping) else {}
    if revocation.get("revocable") is False:
        state = "active"
    else:
        state = "active"
    expires_at = consent.get("expires_at")
    if expires_at:
        try:
            if parse_instant(now) > parse_instant(str(expires_at)):
                return "expired"
        except ValueError:
            return "unknown"
    return state


def policy_state_from_revocation(state: str) -> str:
    if state in {"revoked", "expired"}:
        return "blocked"
    if state == "unknown":
        return "review_required"
    return "allowed"


def export_twin_projection_features(
    projection: Mapping[str, Any],
    decision_log: Mapping[str, Any],
    *,
    consent: Optional[Mapping[str, Any]] = None,
    mission: Optional[Mapping[str, Any]] = None,
    receipt: Optional[Mapping[str, Any]] = None,
    created_at: Optional[str] = None,
    denial_reason_visibility: str = "safe_reason_only",
) -> List[Dict[str, Any]]:
    """Export consent-scoped projection fields as Regis TwinProjectionFeature objects."""
    ensure_match(
        projection,
        decision_log,
        ["projection_id", "twin_id", "subject_id", "mission_id", "recipient_id", "policy_id", "purpose"],
        "decision_log",
    )
    if consent:
        if projection.get("policy_id") != consent.get("policy_id"):
            raise RegisExportError("policy_id mismatch between projection and consent")
        if projection.get("subject_id") != consent.get("subject_id"):
            raise RegisExportError("subject_id mismatch between projection and consent")
    if mission:
        if projection.get("mission_id") != mission.get("mission_id"):
            raise RegisExportError("mission_id mismatch between projection and mission")
        sponsor = mission.get("sponsor", {}) if isinstance(mission.get("sponsor", {}), Mapping) else {}
        if projection.get("recipient_id") != sponsor.get("recipient_id"):
            raise RegisExportError("recipient_id mismatch between projection and mission")
    if receipt:
        if projection.get("twin_id") != receipt.get("twin_id"):
            raise RegisExportError("twin_id mismatch between projection and transition receipt")

    timestamp = created_at or now_utc_iso()
    denied = denied_field_set(projection, decision_log)
    decisions = decision_by_field(decision_log)
    consent_snapshot = consent_scope_snapshot(projection, consent)
    mission_snapshot = mission_governance_snapshot(mission)
    receipt_ref = transition_receipt_ref(receipt)
    current_revocation_state = revocation_state(consent, projection, timestamp)
    effective_authority = compute_effective_authority(consent=consent, mission=mission, receipt=receipt)
    policy_state = policy_state_from_revocation(current_revocation_state)

    features: List[Dict[str, Any]] = []
    for field_path in projection.get("allowed_fields", []):
        if field_path in denied:
            continue
        decision = decisions.get(str(field_path), {})
        if decision and decision.get("decision") != "allow":
            continue
        value = project_path(projection.get("data", {}), str(field_path).split("."))
        if value in (None, {}, []):
            continue
        feature_id_seed = f"{projection['projection_id']}:{field_path}:{canonical_hash(value)}"
        features.append(
            {
                "schema_version": "0.1.0",
                "feature_id": "tpf_" + safe_slug(feature_id_seed)[:96],
                "projection_id": projection["projection_id"],
                "twin_id": projection["twin_id"],
                "subject_id": projection["subject_id"],
                "mission_id": projection["mission_id"],
                "recipient_id": projection["recipient_id"],
                "feature_family": infer_feature_family(str(field_path), value),
                "feature_name": str(field_path),
                "feature_value": value,
                "feature_confidence": "medium",
                "source_field_path": str(field_path),
                "source_field_decision": "allow",
                "source_field_reason": str(decision.get("reason", "allowed_by_projection")),
                "denial_reason_visibility": denial_reason_visibility,
                "domain_context": {
                    "domain_id": "holographme.mission_projection",
                    "source_modality": "structured_human_digital_twin_projection",
                    "calibration_state": "in_domain",
                },
                "consent_scope_snapshot": consent_snapshot,
                "mission_governance_snapshot": mission_snapshot,
                "transition_receipt_ref": receipt_ref,
                "projection_decision_log_ref": {
                    "schema_version": "0.1.0",
                    "decision_log_id": decision_log["decision_log_id"],
                    "projection_id": decision_log["projection_id"],
                    "twin_id": decision_log["twin_id"],
                    "subject_id": decision_log["subject_id"],
                    "mission_id": decision_log["mission_id"],
                    "recipient_id": decision_log["recipient_id"],
                    "policy_id": decision_log["policy_id"],
                    "purpose": decision_log["purpose"],
                    "generated_at": decision_log["generated_at"],
                },
                "retention_rule": consent.get("retention_rule") if consent else None,
                "revocation_state": current_revocation_state,
                "effective_authority_band": effective_authority,
                "policy_state": policy_state,
                "created_at": timestamp,
            }
        )
    return features


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export HolographMe projection fields as Regis TwinProjectionFeature records.")
    parser.add_argument("--projection", required=True, help="Path to HolographMe Projection JSON")
    parser.add_argument("--decision-log", required=True, help="Path to HolographMe ProjectionDecisionLog JSON")
    parser.add_argument("--consent", help="Optional path to ConsentPolicy JSON")
    parser.add_argument("--mission", help="Optional path to Mission JSON")
    parser.add_argument("--receipt", help="Optional path to TransitionReceipt JSON")
    parser.add_argument("--out", required=True, help="Path for Regis feature export JSON")
    parser.add_argument("--created-at", help="Override export timestamp")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    features = export_twin_projection_features(
        load_json(args.projection),
        load_json(args.decision_log),
        consent=load_json(args.consent) if args.consent else None,
        mission=load_json(args.mission) if args.mission else None,
        receipt=load_json(args.receipt) if args.receipt else None,
        created_at=args.created_at,
    )
    output = {"schema_version": "0.1.0", "features": features}
    write_json(args.out, output)
    print(f"wrote Regis feature export: {args.out} ({len(features)} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
