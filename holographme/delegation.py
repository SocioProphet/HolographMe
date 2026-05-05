"""Delegation permission checks for HolographMe."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional


AUTHORITY_ORDER = {
    "observe": 0,
    "recommend": 1,
    "represent": 2,
    "negotiate": 3,
    "commit": 4,
}


def parse_instant(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def authority_allows(granted_band: str, required_band: str) -> bool:
    """Return true when granted authority is at least the required band."""

    if granted_band not in AUTHORITY_ORDER:
        return False
    if required_band not in AUTHORITY_ORDER:
        return False
    return AUTHORITY_ORDER[granted_band] >= AUTHORITY_ORDER[required_band]


def find_delegation(twin: Mapping[str, Any], agent_id: str) -> Optional[Mapping[str, Any]]:
    for delegation in twin.get("delegated_agents", []):
        if delegation.get("agent_id") == agent_id:
            return delegation
    return None


def check_delegation(
    twin: Mapping[str, Any],
    *,
    agent_id: str,
    requested_action: str,
    required_band: str,
    now: Optional[str] = None,
) -> Dict[str, Any]:
    """Check whether an agent may perform an action for a twin.

    The function returns an auditable decision object instead of raising. This
    makes it usable in CLIs, APIs, and transition receipts.
    """

    decision: Dict[str, Any] = {
        "agent_id": agent_id,
        "requested_action": requested_action,
        "required_band": required_band,
        "allowed": False,
        "reason": "unknown",
    }

    delegation = find_delegation(twin, agent_id)
    if delegation is None:
        decision["reason"] = "agent_not_delegated"
        return decision

    expires_at = delegation.get("expires_at")
    if expires_at is not None:
        check_time = parse_instant(now or now_utc_iso())
        if check_time > parse_instant(str(expires_at)):
            decision["reason"] = "delegation_expired"
            decision["expires_at"] = expires_at
            return decision

    allowed_actions = set(delegation.get("allowed_actions", []))
    if requested_action not in allowed_actions:
        decision["reason"] = "action_not_allowed"
        decision["allowed_actions"] = sorted(allowed_actions)
        return decision

    authority_band = str(delegation.get("authority_band", "observe"))
    if not authority_allows(authority_band, required_band):
        decision["reason"] = "insufficient_authority"
        decision["authority_band"] = authority_band
        return decision

    decision.update(
        {
            "allowed": True,
            "reason": "allowed",
            "authority_band": authority_band,
            "expires_at": expires_at,
        }
    )
    return decision
