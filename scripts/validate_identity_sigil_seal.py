#!/usr/bin/env python3
"""Validate IdentitySigilSeal examples and semantic non-collapse rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "identity-sigil-seal.schema.json"
EXAMPLE_DIR = ROOT / "examples"

VALID_EXAMPLE = EXAMPLE_DIR / "identity-sigil-seal.example.json"
REJECTED_EXAMPLES = {
    EXAMPLE_DIR / "identity-sigil-seal.rejected.wallet-is-person.json": "wallet_person_collapse",
    EXAMPLE_DIR / "identity-sigil-seal.rejected.portrait-biometric-default.json": "portrait_biometric_default",
}

REQUIRED_NON_CLAIM_PHRASES = (
    "sigil is not the person",
    "portrait is not biometric proof by default",
    "wallet is not the person",
    "agent action is not direct human action",
    "reputation is contextual evidence",
)

FORBIDDEN_AUTHORITY_SCOPES = {
    "personhood_claim",
    "biometric_identification",
    "unscoped_public_correlation",
    "global_identity_correlation",
}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to load {path}: {exc}") from exc


def semantic_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    if record.get("subject_id") == record.get("twin_id"):
        errors.append("subject_id must not collapse into twin_id")

    non_claims = "\n".join(str(item).lower() for item in record.get("non_claims", []))
    for phrase in REQUIRED_NON_CLAIM_PHRASES:
        if phrase not in non_claims:
            errors.append(f"missing non-claim phrase: {phrase}")

    portrait_policy = record.get("portrait_policy", {})
    if portrait_policy.get("biometric_identity_claim") is True:
        errors.append("portrait must not claim biometric identity by default")
    if portrait_policy.get("face_embedding_stored") is True:
        errors.append("v0.1 seal must not store face embeddings")
    if portrait_policy.get("public_default") is True:
        errors.append("portrait must not be public by default")
    if portrait_policy.get("portrait_bound") is True:
        if not portrait_policy.get("portrait_ref"):
            errors.append("bound portrait requires portrait_ref")
        if not portrait_policy.get("portrait_hash"):
            errors.append("bound portrait requires portrait_hash")

    for authority in record.get("signing_authorities", []):
        scopes = set(authority.get("scopes", []))
        if not scopes:
            errors.append(f"authority {authority.get('authority_id')} must declare scopes")
        forbidden = sorted(scopes & FORBIDDEN_AUTHORITY_SCOPES)
        if forbidden:
            errors.append(f"authority {authority.get('authority_id')} declares forbidden scopes: {forbidden}")
        if authority.get("authority_type") == "wallet":
            not_allowed = set(authority.get("not_allowed_for", []))
            if "personhood_claim" not in not_allowed:
                errors.append("wallet authority must explicitly reject personhood_claim")

    if record.get("delegation_refs") and not record.get("consent_policy_ids"):
        errors.append("delegation refs require consent policy ids")

    if record.get("reputation_refs"):
        if "global human worth" in "\n".join(record.get("reputation_refs", [])).lower():
            errors.append("reputation refs must not encode global human worth")

    if not record.get("transition_receipt_ids"):
        errors.append("seal requires transition receipt ids")

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
