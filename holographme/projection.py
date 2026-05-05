"""Consent-scoped projection generation for HolographMe.

This module implements the first executable slice:
HumanDigitalTwin + ConsentPolicy + Mission -> mission-fit projection + receipt.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


class ProjectionError(ValueError):
    """Raised when a projection request violates policy or input constraints."""


def load_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ProjectionError(f"Expected JSON object in {path}")
    return value


def write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def parse_instant(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def path_is_within(path: str, container: str) -> bool:
    return path == container or path.startswith(container + ".")


def requested_allows_field(requested_field: str, allowed_field: str) -> bool:
    """Return true when an allowed field can satisfy a requested field.

    Examples:
      requested capability_claims allows capability_claims.capability
      requested subject.display_name allows subject.display_name
      requested capability_claims.capability allows capability_claims.capability
    """
    return allowed_field == requested_field or allowed_field.startswith(requested_field + ".")


def is_forbidden(path: str, forbidden_fields: Iterable[str]) -> bool:
    for forbidden in forbidden_fields:
        if path_is_within(path, forbidden) or path_is_within(forbidden, path):
            return True
    return False


def project_path(value: Any, parts: List[str]) -> Any:
    """Project a dotted path from nested dict/list data.

    When the current value is a list, the same remaining path is applied to each
    item and empty projections are removed.
    """
    if not parts:
        return copy.deepcopy(value)

    if isinstance(value, list):
        projected_items = []
        for item in value:
            projected = project_path(item, parts)
            if projected not in (None, {}, []):
                projected_items.append(projected)
        return projected_items

    if isinstance(value, dict):
        head, *tail = parts
        if head not in value:
            return None
        projected = project_path(value[head], tail)
        if projected in (None, {}, []):
            return None
        return {head: projected}

    return None


def deep_merge(target: MutableMapping[str, Any], patch: Mapping[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)  # type: ignore[index]
        elif isinstance(value, list) and isinstance(target.get(key), list):
            target[key] = merge_lists(target[key], value)  # type: ignore[index]
        else:
            target[key] = value


def merge_lists(existing: List[Any], incoming: List[Any]) -> List[Any]:
    """Merge list projections by position.

    Projection paths over arrays produce partial objects. Merging by position lets
    capability_claims.capability and capability_claims.level become one list of
    partial capability objects rather than separate duplicate rows.
    """
    result = copy.deepcopy(existing)
    for index, item in enumerate(incoming):
        if index >= len(result):
            result.append(item)
            continue
        if isinstance(result[index], dict) and isinstance(item, dict):
            deep_merge(result[index], item)
        elif result[index] != item:
            result[index] = item
    return result


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")


def validate_projection_inputs(
    twin: Mapping[str, Any],
    consent: Mapping[str, Any],
    mission: Mapping[str, Any],
    *,
    now: Optional[str] = None,
) -> None:
    subject_id = twin.get("subject", {}).get("subject_id")
    if consent.get("subject_id") != subject_id:
        raise ProjectionError("Consent policy subject_id does not match twin subject.subject_id")

    recipient_id = mission.get("sponsor", {}).get("recipient_id")
    if recipient_id not in consent.get("allowed_recipients", []):
        raise ProjectionError(f"Mission recipient is not allowed by consent policy: {recipient_id}")

    purpose = mission.get("projection_request", {}).get("purpose")
    if purpose not in consent.get("allowed_purposes", []):
        raise ProjectionError(f"Mission projection purpose is not allowed by consent policy: {purpose}")

    check_time = parse_instant(now or now_utc_iso())
    expires_at = parse_instant(str(consent["expires_at"]))
    if check_time > expires_at:
        raise ProjectionError(f"Consent policy expired at {consent['expires_at']}")


def make_decision(
    *,
    field: str,
    decision: str,
    reason: str,
    requested_field: Optional[str] = None,
) -> Dict[str, str]:
    payload = {"field": field, "decision": decision, "reason": reason}
    if requested_field is not None:
        payload["requested_field"] = requested_field
    return payload


def generate_projection(
    twin: Mapping[str, Any],
    consent: Mapping[str, Any],
    mission: Mapping[str, Any],
    *,
    now: Optional[str] = None,
    receipt_id: Optional[str] = None,
    decision_log_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a consent-scoped mission-fit projection, receipt, and decision log."""

    generated_at = now or now_utc_iso()
    validate_projection_inputs(twin, consent, mission, now=generated_at)

    requested_fields = list(mission.get("projection_request", {}).get("requested_fields", []))
    allowed_fields = list(consent.get("allowed_fields", []))
    forbidden_fields = list(consent.get("forbidden_fields", []))

    data: Dict[str, Any] = {}
    exposed_fields: List[str] = []
    denied_fields: List[Dict[str, str]] = []
    decisions: List[Dict[str, str]] = []

    for requested in requested_fields:
        matching_allowed = [
            field
            for field in allowed_fields
            if requested_allows_field(requested, field) and not is_forbidden(field, forbidden_fields)
        ]

        if not matching_allowed:
            denied_fields.append({"field": requested, "reason": "not_allowed_by_consent_policy"})
            decisions.append(
                make_decision(
                    field=requested,
                    requested_field=requested,
                    decision="deny",
                    reason="not_allowed_by_consent_policy",
                )
            )
            continue

        for allowed in matching_allowed:
            if is_forbidden(allowed, forbidden_fields):
                denied_fields.append({"field": allowed, "reason": "forbidden_by_consent_policy"})
                decisions.append(
                    make_decision(
                        field=allowed,
                        requested_field=requested,
                        decision="deny",
                        reason="forbidden_by_consent_policy",
                    )
                )
                continue

            patch = project_path(twin, allowed.split("."))
            if patch in (None, {}, []):
                denied_fields.append({"field": allowed, "reason": "field_missing_from_twin"})
                decisions.append(
                    make_decision(
                        field=allowed,
                        requested_field=requested,
                        decision="deny",
                        reason="field_missing_from_twin",
                    )
                )
                continue

            deep_merge(data, patch)
            exposed_fields.append(allowed)
            decisions.append(
                make_decision(
                    field=allowed,
                    requested_field=requested,
                    decision="allow",
                    reason="allowed_by_consent_policy",
                )
            )

    twin_id = str(twin["twin_id"])
    mission_id = str(mission["mission_id"])
    projection_id = "proj_" + safe_slug(f"{mission_id}_{twin_id}")
    receipt_identifier = receipt_id or "tr_" + safe_slug(f"projection_{mission_id}_{twin_id}")
    decision_log_identifier = decision_log_id or "pdl_" + safe_slug(f"{mission_id}_{twin_id}")

    projection_body = {
        "schema_version": "0.1.0",
        "projection_id": projection_id,
        "twin_id": twin_id,
        "subject_id": twin["subject"]["subject_id"],
        "mission_id": mission_id,
        "recipient_id": mission["sponsor"]["recipient_id"],
        "purpose": mission["projection_request"]["purpose"],
        "generated_at": generated_at,
        "policy_id": consent["policy_id"],
        "allowed_fields": sorted(set(exposed_fields)),
        "denied_fields": denied_fields,
        "data": data,
    }

    decision_log = {
        "schema_version": "0.1.0",
        "decision_log_id": decision_log_identifier,
        "projection_id": projection_id,
        "twin_id": twin_id,
        "subject_id": twin["subject"]["subject_id"],
        "mission_id": mission_id,
        "recipient_id": mission["sponsor"]["recipient_id"],
        "policy_id": consent["policy_id"],
        "purpose": mission["projection_request"]["purpose"],
        "generated_at": generated_at,
        "decisions": decisions,
    }

    receipt = {
        "schema_version": "0.1.0",
        "receipt_id": receipt_identifier,
        "twin_id": twin_id,
        "action": "mission_fit_projection",
        "actor": {
            "actor_id": "holographme_projection_runtime",
            "actor_type": "system",
        },
        "timestamp": generated_at,
        "policy_version": str(consent.get("schema_version", "0.1.0")),
        "previous_state_hash": str(twin.get("state_hash", "sha256:unknown")),
        "new_state_hash": canonical_hash(projection_body),
        "evidence_links": [consent["policy_id"], mission_id, decision_log_identifier],
        "approval_band": mission["governance"]["authority_band"],
        "rollback": {
            "rollback_supported": True,
            "rollback_method": "expire_projection_and_revoke_access",
            "irreversible_acknowledged": False,
        },
        "replay_hints": {
            "transition_library_version": "0.1.0",
            "input_snapshot_uri": f"urn:holographme:projection-input:{projection_id}",
            "runtime_version": "holographme-projection-runtime-0.1.0",
        },
    }

    return {"projection": projection_body, "receipt": receipt, "decision_log": decision_log}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a consent-scoped HolographMe mission projection.")
    parser.add_argument("--twin", required=True, help="Path to HumanDigitalTwin JSON")
    parser.add_argument("--consent", required=True, help="Path to ConsentPolicy JSON")
    parser.add_argument("--mission", required=True, help="Path to Mission JSON")
    parser.add_argument("--out", required=True, help="Path for projection output JSON")
    parser.add_argument("--receipt-out", required=True, help="Path for transition receipt output JSON")
    parser.add_argument("--decision-log-out", help="Optional path for projection decision log JSON")
    parser.add_argument("--now", help="Override generation timestamp, ISO-8601 UTC preferred")
    parser.add_argument("--receipt-id", help="Override generated transition receipt id")
    parser.add_argument("--decision-log-id", help="Override generated projection decision log id")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        result = generate_projection(
            load_json(args.twin),
            load_json(args.consent),
            load_json(args.mission),
            now=args.now,
            receipt_id=args.receipt_id,
            decision_log_id=args.decision_log_id,
        )
    except ProjectionError as exc:
        print(f"projection rejected: {exc}", file=__import__("sys").stderr)
        return 2

    write_json(args.out, result["projection"])
    write_json(args.receipt_out, result["receipt"])
    if args.decision_log_out:
        write_json(args.decision_log_out, result["decision_log"])
    print(f"wrote projection: {args.out}")
    print(f"wrote receipt: {args.receipt_out}")
    if args.decision_log_out:
        print(f"wrote decision log: {args.decision_log_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
