#!/usr/bin/env python3
"""Validate HolographMe JSON examples against local JSON Schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXAMPLE_DIR = ROOT / "examples"

EXAMPLE_TO_SCHEMA: Dict[str, str] = {
    "human-digital-twin.example.json": "human-digital-twin.schema.json",
    "consent-policy.example.json": "consent-policy.schema.json",
    "mission.example.json": "mission.schema.json",
    "transition-receipt.example.json": "transition-receipt.schema.json",
    "projection.example.json": "projection.schema.json",
    "projection-decision-log.example.json": "projection-decision-log.schema.json",
    "projection-decision-log.rejected.example.json": "projection-decision-log.schema.json",
    "capability-claim-event.example.json": "capability-claim-event.schema.json",
}


def load_json(path: Path) -> object:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def main() -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise SystemExit("Missing dependency: jsonschema. Install with `python -m pip install jsonschema`.") from exc

    failures = 0

    for example_name, schema_name in EXAMPLE_TO_SCHEMA.items():
        schema_path = SCHEMA_DIR / schema_name
        example_path = EXAMPLE_DIR / example_name

        schema = load_json(schema_path)
        example = load_json(example_path)

        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        errors = sorted(validator.iter_errors(example), key=lambda error: list(error.path))

        if errors:
            failures += 1
            print(f"FAIL {example_name} -> {schema_name}")
            for error in errors:
                path = ".".join(str(part) for part in error.path) or "<root>"
                print(f"  - {path}: {error.message}")
        else:
            print(f"PASS {example_name} -> {schema_name}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
