from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from holographme.bundle import BundleError, build_bundle_manifest, parse_artifact_arg, sha256_file


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SCHEMAS = ROOT / "schemas"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class BundleManifestTests(unittest.TestCase):
    def test_example_validates_against_schema(self):
        schema = load_json(SCHEMAS / "export-bundle-manifest.schema.json")
        example = load_json(EXAMPLES / "export-bundle-manifest.example.json")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)

    def test_hash_generation_is_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "artifact.json"
            path.write_text('{"a":1}\n', encoding="utf-8")
            first = sha256_file(path)
            second = sha256_file(path)

        self.assertEqual(first, second)
        self.assertRegex(first, r"^sha256:[a-f0-9]{64}$")

    def test_build_manifest_from_artifacts(self):
        artifacts = [
            ("human_digital_twin", EXAMPLES / "human-digital-twin.example.json"),
            ("consent_policy", EXAMPLES / "consent-policy.example.json"),
            ("mission", EXAMPLES / "mission.example.json"),
            ("projection", EXAMPLES / "projection.example.json"),
            ("projection_decision_log", EXAMPLES / "projection-decision-log.example.json"),
            ("capability_claim_event_log", EXAMPLES / "capability-claim-event.example.json"),
            ("transition_receipt", EXAMPLES / "transition-receipt.example.json"),
        ]
        manifest = build_bundle_manifest(
            artifacts,
            bundle_id="bundle_test_alpha",
            created_at="2026-05-05T18:30:00Z",
            root=ROOT,
            custodian="SocioProphet HolographMe",
        )

        self.assertEqual(manifest["twin_id"], "hdt_example_alpha")
        self.assertEqual(manifest["subject_id"], "sub_example_alpha")
        self.assertEqual(manifest["artifact_count"], 7)
        self.assertRegex(manifest["bundle_digest"], r"^sha256:[a-f0-9]{64}$")
        self.assertEqual(manifest["artifacts"][0]["path"], "examples/human-digital-twin.example.json")

        schema = load_json(SCHEMAS / "export-bundle-manifest.schema.json")
        Draft202012Validator(schema).validate(manifest)

    def test_parse_artifact_arg_aliases(self):
        artifact_type, path = parse_artifact_arg("human-digital-twin=examples/human-digital-twin.example.json")
        self.assertEqual(artifact_type, "human_digital_twin")
        self.assertEqual(path.as_posix(), "examples/human-digital-twin.example.json")

    def test_missing_artifact_rejected(self):
        with self.assertRaisesRegex(BundleError, "does not exist"):
            build_bundle_manifest(
                [("human_digital_twin", EXAMPLES / "missing.json")],
                bundle_id="bundle_missing",
                created_at="2026-05-05T18:30:00Z",
            )

    def test_requires_artifact(self):
        with self.assertRaisesRegex(BundleError, "at least one"):
            build_bundle_manifest([], bundle_id="bundle_empty")


if __name__ == "__main__":
    unittest.main()
