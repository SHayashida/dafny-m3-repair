"""Create once, and subsequently verify, the pre-measurement Case B design lock."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import (
    CANONICAL, DESIGN_LOCK, LEVER_DEFINITIONS, METADATA_SCHEMA, canonical_json_sha256,
    read_json, sha256_file, write_json,
)
from metadata_parser import normalized_group_mapping, parse_metadata_file

SCRIPTS = Path(__file__).resolve().parent
GENERATOR = SCRIPTS / "generate_variants.py"
PARSER = SCRIPTS / "metadata_parser.py"
EXPECTED_DAFNY_VERSION = "4.11.0"


class DesignLockError(ValueError):
    pass


def build_lock() -> dict:
    definitions = read_json(LEVER_DEFINITIONS)
    lever_ids = [entry["lever_id"] for entry in definitions["repair_levers"]]
    if len(lever_ids) != len(set(lever_ids)):
        raise DesignLockError("lever definitions contain duplicate identifiers")
    records = parse_metadata_file(CANONICAL, lever_ids)
    mapping = normalized_group_mapping(records)
    declared_groups = {entry["group_id"] for entry in definitions["groups"]}
    if set(mapping.values()) != declared_groups:
        raise DesignLockError("source mapping and declared group universe differ")
    return {
        "schema_version": "case-b-design-lock-v1",
        "canonical_source_sha256": sha256_file(CANONICAL),
        "metadata_sha256": canonical_json_sha256(records),
        "metadata_schema_sha256": sha256_file(METADATA_SCHEMA),
        "group_mapping_sha256": canonical_json_sha256(mapping),
        "lever_definition_sha256": sha256_file(LEVER_DEFINITIONS),
        "generator_sha256": sha256_file(GENERATOR),
        "metadata_parser_sha256": sha256_file(PARSER),
        "dafny_version_expected": EXPECTED_DAFNY_VERSION,
        "dafny_invocation_protocol": ["<resolved-dafny-executable>", "verify", "<variant-source>"],
        "verification_timeout_seconds": 120,
        "repair_levers": lever_ids,
        "groups": [entry["group_id"] for entry in definitions["groups"]],
        "group_mapping": mapping,
        "design_notes": [
            "Retained-set/deletion-set convention: deleted_levers=R and retained_levers=Lambda\\R.",
            "The fully retained canonical program intentionally has an unprovable nonnegative postcondition.",
            "Grouping is parsed once from canonical source metadata before variant generation.",
            "Preregistered hypothesis: g(Min(F)) differs from Min(g(F)); equality remains a valid result.",
            "Case B is separate from M3 GroupSoundness, ResidualFaithfulness, and exactness.",
        ],
    }


def verify_lock() -> dict:
    if not DESIGN_LOCK.exists():
        raise DesignLockError(f"missing design lock: {DESIGN_LOCK}")
    stored = read_json(DESIGN_LOCK)
    expected = build_lock()
    if stored != expected:
        differing = sorted(key for key in set(stored) | set(expected) if stored.get(key) != expected.get(key))
        raise DesignLockError(f"design lock mismatch in fields: {differing}")
    return stored


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true", help="create/replace the lock before any measurement")
    args = parser.parse_args()
    if args.create:
        write_json(DESIGN_LOCK, build_lock())
        print(f"created {DESIGN_LOCK}")
    else:
        verify_lock()
        print("Case B design lock: OK")


if __name__ == "__main__":
    main()
