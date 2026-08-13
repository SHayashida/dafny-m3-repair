"""Shared paths and deterministic serialization for the isolated Case B artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CASE_B = Path(__file__).resolve().parents[1]
ROOT = CASE_B.parent
CANONICAL = CASE_B / "canonical" / "case_b.dfy"
DESIGN = CASE_B / "design"
DESIGN_LOCK = DESIGN / "case_b_design_lock.json"
LEVER_DEFINITIONS = DESIGN / "lever_definitions.json"
METADATA_SCHEMA = DESIGN / "metadata_schema.json"
GENERATED = CASE_B / "generated" / "variants"
MEASUREMENTS = CASE_B / "measurements"
RAW = MEASUREMENTS / "raw"
AUDIT = CASE_B / "audit"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def canonical_json_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()
