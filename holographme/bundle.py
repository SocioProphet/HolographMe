"""Governed export bundle manifest builder for HolographMe."""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class BundleError(ValueError):
    """Raised when a bundle manifest cannot be built."""


DEFAULT_ARTIFACT_TYPES = {
    "human-digital-twin": "human_digital_twin",
    "human_digital_twin": "human_digital_twin",
    "consent-policy": "consent_policy",
    "consent_policy": "consent_policy",
    "mission": "mission",
    "projection": "projection",
    "projection-decision-log": "projection_decision_log",
    "projection_decision_log": "projection_decision_log",
    "capability-claim-event-log": "capability_claim_event_log",
    "capability_claim_event_log": "capability_claim_event_log",
    "transition-receipt": "transition_receipt",
    "transition_receipt": "transition_receipt",
    "security-policy": "security_policy",
    "security_policy": "security_policy",
    "readme": "readme",
    "other": "other",
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_").lower()
    return slug or "artifact"


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise BundleError(f"artifact path does not exist: {path}")
    if not path.is_file():
        raise BundleError(f"artifact path is not a file: {path}")

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise BundleError(f"Expected JSON object in {path}")
    return value


def write_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


def parse_artifact_arg(raw: str) -> Tuple[str, Path]:
    if "=" not in raw:
        raise BundleError("artifact must be formatted as type=path")
    artifact_type, path = raw.split("=", 1)
    normalized_type = DEFAULT_ARTIFACT_TYPES.get(artifact_type.strip())
    if normalized_type is None:
        allowed = ", ".join(sorted(DEFAULT_ARTIFACT_TYPES))
        raise BundleError(f"unknown artifact type {artifact_type!r}; allowed aliases: {allowed}")
    return normalized_type, Path(path)


def infer_media_type(path: Path) -> str:
    if path.suffix.lower() == ".json":
        return "application/json"
    media_type, _ = mimetypes.guess_type(str(path))
    return media_type or "application/octet-stream"


def artifact_id(artifact_type: str, path: Path) -> str:
    stem = safe_slug(path.stem)
    return "artifact_" + safe_slug(f"{artifact_type}_{stem}")


def build_artifact(artifact_type: str, path: Path, *, root: Optional[Path] = None, required: bool = True) -> Dict[str, Any]:
    resolved = path.resolve()
    display_path = path.as_posix()
    if root is not None:
        try:
            display_path = resolved.relative_to(root.resolve()).as_posix()
        except ValueError:
            display_path = path.as_posix()

    return {
        "artifact_id": artifact_id(artifact_type, Path(display_path)),
        "artifact_type": artifact_type,
        "path": display_path,
        "digest": sha256_file(resolved),
        "media_type": infer_media_type(resolved),
        "required": required,
    }


def extract_identity(twin_path: Optional[Path]) -> Tuple[str, str]:
    if twin_path is None:
        return "hdt_unknown", "sub_unknown"
    twin = load_json(twin_path)
    subject = twin.get("subject", {}) if isinstance(twin.get("subject", {}), Mapping) else {}
    return str(twin.get("twin_id", "hdt_unknown")), str(subject.get("subject_id", "sub_unknown"))


def build_bundle_manifest(
    artifacts: Sequence[Tuple[str, Path]],
    *,
    bundle_id: str,
    created_at: Optional[str] = None,
    purpose: str = "portable_governed_export",
    custodian: Optional[str] = None,
    root: Optional[Path] = None,
) -> Dict[str, Any]:
    if not artifacts:
        raise BundleError("at least one artifact is required")

    artifact_records = [build_artifact(kind, path, root=root) for kind, path in artifacts]
    twin_path = next((path for kind, path in artifacts if kind == "human_digital_twin"), None)
    twin_id, subject_id = extract_identity(twin_path)

    manifest: Dict[str, Any] = {
        "schema_version": "0.1.0",
        "bundle_id": bundle_id,
        "created_at": created_at or now_utc_iso(),
        "twin_id": twin_id,
        "subject_id": subject_id,
        "purpose": purpose,
        "artifact_count": len(artifact_records),
        "artifacts": artifact_records,
    }
    if custodian:
        manifest["custodian"] = custodian

    manifest_without_digest = dict(manifest)
    manifest["bundle_digest"] = canonical_hash(manifest_without_digest)
    return manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a governed HolographMe export bundle manifest.")
    parser.add_argument("--bundle-id", required=True, help="Bundle id, e.g. bundle_example_alpha")
    parser.add_argument("--artifact", action="append", required=True, help="Artifact mapping formatted as type=path")
    parser.add_argument("--out", required=True, help="Path for bundle manifest JSON")
    parser.add_argument("--created-at", help="Override creation timestamp")
    parser.add_argument("--purpose", default="portable_governed_export", help="Bundle purpose")
    parser.add_argument("--custodian", help="Optional bundle custodian")
    parser.add_argument("--root", help="Optional root for relative display paths")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        artifacts = [parse_artifact_arg(raw) for raw in args.artifact]
        root = Path(args.root) if args.root else None
        manifest = build_bundle_manifest(
            artifacts,
            bundle_id=args.bundle_id,
            created_at=args.created_at,
            purpose=args.purpose,
            custodian=args.custodian,
            root=root,
        )
    except BundleError as exc:
        print(f"bundle rejected: {exc}", file=__import__("sys").stderr)
        return 2

    write_json(args.out, manifest)
    print(f"wrote bundle manifest: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
