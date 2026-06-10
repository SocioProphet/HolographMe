#!/usr/bin/env python3
"""Validate SigningAuthorityBinding examples and anti-key-collapse rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "signing-authority-binding.schema.json"
EXAMPLE_DIR = ROOT / "examples"

VALID_EXAMPLES = [
    EXAMPLE_DIR / "signing-authority-binding.passkey.example.json",
]
REJECTED_EXAMPLES = {
    EXAMPLE_DIR / "signing-authority-binding.rejected.wallet-personhood.json": "wallet_authority_claims_personhood",
}

FORBIDDEN_SCOPES = {
    "personhood_claim",
    "sole_personhood_binding",
    "global_identity_correlation",
}

REQUIRED_NOT_ALLOWED = {
    "sole_personhood_binding",
    "global_identity_correlation",
}

REQUIRED_NON_CLAIM_PHRASES = (
    "scoped controller",
    "does not establish personhood by itself",
    "cannot override personhood binding ceremony",
)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to load {path}: {exc}") from exc


def semantic_errors(record: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    scopes = {str(item) for item in record.get("scopes", [])}
    not_allowed = {str(item) for item in record.get("not_allowed_for", [])}
    non_claims = "\n".join(str(item).lower() for item in record.get("non_claims", []))
    authority_type = str(record.get("authority_type", ""))

    forbidden = sorted(scopes & FORBIDDEN_SCOPES)
    if forbidden:
        errors.append(f"signing authority allowed forbidden scopes: {forbidden}")

    missing_not_allowed = sorted(REQUIRED_NOT_ALLOWED - not_allowed)
    if missing_not_allowed:
        errors.append(f"signing authority missing not_allowed_for safeguards: {missing_not_allowed}")

    if authority_type == "wallet" and "personhood_claim" not in not_allowed:
        errors.append("wallet authority must explicitly disallow personhood_claim")

    if authority_type == "wallet" and record.get("status") == "active_primary":
        errors.append("wallet authority must not be active_primary human identity authority")

    if record.get("recovery_posture") == "non_recoverable" and record.get("status") == "active_primary":
        errors.append("active_primary authority must not be non_recoverable")

    if not record.get("personhood_binding_ref"):
        errors.append("personhood_binding_ref required")

    if not record.get("proofs"):
        errors.append("control proof required")

    for phrase in REQUIRED_NON_CLAIM_PHRASES:
        if phrase not in non_claims:
            errors.append(f"missing non-claim phrase: {phrase}")

    if "not the person" not in non_claims:
        errors.append("authority must explicitly state it is not the person")

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

    for path in VALID_EXAMPLES:
        record = load_json(path)
        schema_errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        semantic = semantic_errors(record)
        if schema_errors or semantic:
            failures += 1
            print(f"FAIL {path.name}: expected valid")
            for error in schema_errors:
                loc = ".".join(str(part) for part in error.path) or "<root>"
                print(f"  - schema {loc}: {error.message}")
            for error in semantic:
                print(f"  - semantic: {error}")
        else:
            print(f"PASS {path.name}")

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
