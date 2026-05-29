#!/usr/bin/env python3
"""Validate the projection-loss profile example.

This validator is deliberately schema-light because the formal JSON Schema write
for projection-loss profiles was blocked during the first tranche. It keeps the
contract executable by checking required fields and the core semantic invariants
from docs/projection-loss-profiles.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "projection-loss-profile.example.json"
HIGH_CONSEQUENCE_USES = {"publication", "export", "memory_promotion", "graph_promotion"}


def load_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_profile(profile: dict) -> None:
    for field in [
        "schema_version",
        "profile_id",
        "projection_id",
        "projection_kind",
        "generated_at",
        "source_basis",
        "projection_method",
        "loss_profile",
        "freshness_window",
        "consent_policy_refs",
        "evidence_refs",
        "confidence",
        "allowed_uses",
        "disallowed_uses",
        "repair",
        "non_claims",
    ]:
        require(field in profile, f"missing required field: {field}")

    source_basis = profile["source_basis"]
    for field in ["source_refs", "channel_refs", "selection_criteria", "coverage_basis"]:
        require(field in source_basis, f"source_basis missing {field}")
    require(source_basis["source_refs"], "source_basis.source_refs must not be empty")
    require(source_basis["channel_refs"], "source_basis.channel_refs must not be empty")
    require(source_basis["selection_criteria"], "source_basis.selection_criteria must not be empty")

    method = profile["projection_method"]
    for field in ["method", "compression_basis", "human_facing_rendering"]:
        require(field in method, f"projection_method missing {field}")

    loss = profile["loss_profile"]
    for field in ["omitted_fields", "denied_fields", "loss_modes", "known_blind_spots"]:
        require(field in loss, f"loss_profile missing {field}")
    require(loss["loss_modes"], "loss_profile.loss_modes must not be empty")
    require(loss["denied_fields"] or loss["omitted_fields"] or loss["known_blind_spots"], "loss profile must disclose at least one omission, denied field, or blind spot")

    freshness = profile["freshness_window"]
    for field in ["valid_from", "valid_to", "stale_after", "revalidation_ref"]:
        require(field in freshness, f"freshness_window missing {field}")
    require(freshness["valid_to"] is not None or freshness["stale_after"] is not None or freshness["revalidation_ref"], "open-ended projection profile requires stale_after or revalidation_ref")

    require(profile["consent_policy_refs"], "consent_policy_refs must not be empty")
    require(profile["evidence_refs"], "evidence_refs must not be empty")

    confidence = profile["confidence"]
    for field in ["confidence_type", "level"]:
        require(field in confidence, f"confidence missing {field}")

    allowed = set(profile["allowed_uses"])
    disallowed = set(profile["disallowed_uses"])
    repair = profile["repair"]
    for field in ["repair_required_for", "repair_event_refs", "revalidation_path"]:
        require(field in repair, f"repair missing {field}")
    repair_required = set(repair["repair_required_for"])

    unsafe_allowed = sorted(allowed & HIGH_CONSEQUENCE_USES)
    require(not unsafe_allowed, f"high-consequence uses require additional approval and must not be allowed in this example: {unsafe_allowed}")
    require(HIGH_CONSEQUENCE_USES <= disallowed, "high-consequence uses must be disallowed in the first profile example")
    require(HIGH_CONSEQUENCE_USES <= repair_required, "high-consequence uses must require repair/revalidation")

    require(profile["non_claims"], "non_claims must not be empty")
    require(any("entire twin" in claim or "whole" in claim for claim in profile["non_claims"]), "non_claims should disclose that this is not a whole-source projection")


def main() -> int:
    profile = load_json(EXAMPLE)
    validate_profile(profile)
    print(json.dumps({"ok": True, "checked": str(EXAMPLE.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
