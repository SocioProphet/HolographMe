#!/usr/bin/env python3
"""Validate PersonhoodBindingRecord examples and anti-object-collapse rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "personhood-binding-record.schema.json"
EXAMPLE_DIR = ROOT / "examples"

VALID_EXAMPLE = EXAMPLE_DIR / "personhood-binding-record.example.json"
REJECTED_EXAMPLES = {
    EXAMPLE_DIR / "personhood-binding-record.rejected.wallet-only.json": "wallet_only_personhood",
    EXAMPLE_DIR / "personhood-binding-record.rejected.portrait-only.json": "portrait_only_personhood",
    EXAMPLE_DIR / "personhood-binding-record.rejected.no-recovery.json": "missing_recovery_path",
}

REQUIRED_NON_CLAIM_PHRASES = (
    "wallet the person",
    "portrait biometric proof by default",
    "account the person",
    "does not expose all identity contexts",
    "correct, revoke, or contest",
)

MINIMUM_ACTIVE_CLASSES_FOR_P3_PLUS = 3

OBJECT_ONLY_EVIDENCE_CLASSES = {
    "account_continuity",
    "device_key_continuity",
    "liveness_or_presence",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to load {path}: {exc}") from exc


def active_evidence_classes(record: Mapping[str, Any]) -> set[str]:
    return {
        str(item.get("class"))
        for item in record.get("evidence_classes", [])
        if item.get("status") == "active"
    }


def semantic_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    if record.get("subject_id") == record.get("twin_id"):
        errors.append("subject_id must not collapse into twin_id")

    non_claims = "\n".join(str(item).lower() for item in record.get("non_claims", []))
    for phrase in REQUIRED_NON_CLAIM_PHRASES:
        if phrase not in non_claims:
            errors.append(f"missing non-claim phrase: {phrase}")

    policy = record.get("proof_policy", {})
    classes = active_evidence_classes(record)
    required_count = int(policy.get("minimum_independent_evidence_classes", 0))
    assurance = str(record.get("assurance_level", ""))

    if policy.get("requires_subject_consent") is not True:
        errors.append("personhood binding requires subject consent")
    if not record.get("ceremony", {}).get("subject_consent_ref"):
        errors.append("ceremony requires subject_consent_ref")

    if policy.get("forbids_single_factor_personhood") is not True:
        errors.append("personhood binding must forbid single-factor personhood")
    if required_count < MINIMUM_ACTIVE_CLASSES_FOR_P3_PLUS and assurance.startswith(("P3_", "P4_", "P5_")):
        errors.append("P3+ personhood binding requires at least three independent evidence classes")
    if assurance.startswith(("P3_", "P4_", "P5_")) and len(classes) < MINIMUM_ACTIVE_CLASSES_FOR_P3_PLUS:
        errors.append("P3+ personhood binding has fewer than three active evidence classes")

    if classes and classes.issubset(OBJECT_ONLY_EVIDENCE_CLASSES):
        errors.append("personhood binding cannot be based only on object/control evidence classes")

    if "self_attestation" not in classes:
        errors.append("personhood binding requires active self_attestation evidence")
    if assurance.startswith(("P2_", "P3_", "P4_", "P5_")) and "liveness_or_presence" not in classes:
        errors.append("P2+ personhood binding requires liveness_or_presence evidence")
    if assurance.startswith(("P3_", "P4_", "P5_")) and "guardian_or_witness_attestation" not in classes:
        errors.append("P3+ personhood binding requires guardian_or_witness_attestation evidence")
    if assurance.startswith(("P4_", "P5_")) and "credential_attestation" not in classes:
        errors.append("P4+ personhood binding requires credential_attestation evidence")

    if policy.get("forbids_biometric_mandate") is not True:
        errors.append("personhood binding must forbid biometric mandate")
    all_refs = "\n".join(
        str(ref).lower()
        for item in record.get("evidence_classes", [])
        for ref in item.get("evidence_refs", [])
    )
    if "biometric" in all_refs or "face-match" in all_refs:
        errors.append("personhood binding must not rely on biometric or face-match evidence as a required sole basis")

    if policy.get("requires_recovery_path") is not True:
        errors.append("personhood binding requires recovery path")
    if str(record.get("recovery_policy_ref", "")).lower() in {"", "none", "null"}:
        errors.append("personhood binding requires concrete recovery_policy_ref")
    if "recovery_policy" not in classes:
        errors.append("personhood binding requires active recovery_policy evidence class")

    revocation = record.get("revocation", {})
    if policy.get("requires_revocation_path") is not True:
        errors.append("personhood binding requires revocation path")
    if revocation.get("revocable") is not True:
        errors.append("personhood binding must be revocable")
    if revocation.get("subject_can_contest") is not True:
        errors.append("subject must be able to contest personhood binding")
    if revocation.get("correction_supported") is not True:
        errors.append("personhood binding must support correction")
    if "revocation_policy" not in classes:
        errors.append("personhood binding requires active revocation_policy evidence class")

    if not record.get("transition_receipt_ids"):
        errors.append("personhood binding requires transition receipt continuity")

    return errors


def main() -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise SystemExit("Missing dependency: jsonschema. Install with `python -m pip install jsonschema`.") from exc

    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)

    failures = 0

    valid_record = load_json(VALID_EXAMPLE)
    schema_errors = sorted(validator.iter_errors(valid_record), key=lambda error: list(error.path))
    semantic = semantic_errors(valid_record)
    if schema_errors or semantic:
        failures += 1
        print(f"FAIL {VALID_EXAMPLE.name}: expected valid")
        for error in schema_errors:
            path = ".".join(str(part) for part in error.path) or "<root>"
            print(f"  - schema {path}: {error.message}")
        for error in semantic:
            print(f"  - semantic: {error}")
    else:
        print(f"PASS {VALID_EXAMPLE.name}")

    for path, expected_reason in REJECTED_EXAMPLES.items():
        record = load_json(path)
        schema_errors = list(validator.iter_errors(record))
        semantic = semantic_errors(record)
        if schema_errors:
            print(f"PASS {path.name}: rejected by schema before semantic gate")
            continue
        if semantic:
            print(f"PASS {path.name}: rejected semantically ({expected_reason})")
            for error in semantic:
                print(f"  - {error}")
            continue
        failures += 1
        print(f"FAIL {path.name}: expected semantic rejection for {expected_reason}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
