"""Generate all 2^|Lambda| retained-set variants without consulting outcomes."""

from __future__ import annotations

from itertools import combinations

from common import (
    CANONICAL, DESIGN_LOCK, GENERATED, canonical_json_sha256, read_json, relative,
    sha256_file, write_json,
)
from design_lock import verify_lock
from metadata_parser import normalized_group_mapping, parse_metadata_file


class GenerationError(ValueError):
    pass


def powerset(items: list[str]) -> list[frozenset[str]]:
    return [frozenset(choice) for size in range(len(items) + 1) for choice in combinations(items, size)]


def variant_id(deleted: frozenset[str], levers: list[str]) -> str:
    return "case_b_" + "".join("1" if lever in deleted else "0" for lever in levers)


def render_variant(canonical: str, deleted: frozenset[str]) -> str:
    requires: list[str] = []
    if "L1_REQUIRE_NONNEGATIVE" in deleted:
        requires.append("requires x >= 0")
    if "L2_REQUIRE_AT_LEAST_MINUS_ONE" in deleted:
        requires.append("requires x >= -1")
    requires_text = "\n  ".join(requires) if requires else "// no repair precondition inserted"
    assignment = "y := x + 1; // CASE_B_BODY_SLOT" if "L3_SHIFT_BODY_BY_ONE" in deleted else "y := x; // CASE_B_BODY_SLOT"
    if canonical.count("// CASE_B_REQUIRES_SLOT") != 1 or canonical.count("y := x; // CASE_B_BODY_SLOT") != 1:
        raise GenerationError("canonical source slots are missing or ambiguous")
    return canonical.replace("// CASE_B_REQUIRES_SLOT", requires_text).replace(
        "y := x; // CASE_B_BODY_SLOT", assignment
    )


def generate() -> dict:
    lock = verify_lock()
    source = CANONICAL.read_text(encoding="utf-8")
    records = parse_metadata_file(CANONICAL, lock["repair_levers"])
    mapping = normalized_group_mapping(records)
    if mapping != lock["group_mapping"] or canonical_json_sha256(mapping) != lock["group_mapping_sha256"]:
        raise GenerationError("canonical group mapping does not match the design lock")
    GENERATED.mkdir(parents=True, exist_ok=True)
    lock_sha = sha256_file(DESIGN_LOCK)
    variants = []
    universe = lock["repair_levers"]
    for deleted in powerset(universe):
        retained = frozenset(universe) - deleted
        identifier = variant_id(deleted, universe)
        source_path = GENERATED / f"{identifier}.dfy"
        metadata_path = GENERATED / f"{identifier}.variant.json"
        text = render_variant(source, deleted)
        source_path.write_text(text, encoding="utf-8")
        metadata = {
            "schema_version": "case-b-variant-v1",
            "variant_id": identifier,
            "deleted_levers": [lever for lever in universe if lever in deleted],
            "retained_levers": [lever for lever in universe if lever in retained],
            "source": relative(source_path),
            "source_sha256": sha256_file(source_path),
            "design_lock": relative(DESIGN_LOCK),
            "design_lock_sha256": lock_sha,
            "group_mapping_sha256": lock["group_mapping_sha256"],
        }
        write_json(metadata_path, metadata)
        variants.append({**metadata, "variant_metadata": relative(metadata_path)})
    manifest = {
        "schema_version": "case-b-variant-manifest-v1",
        "design_lock_sha256": lock_sha,
        "lever_universe": universe,
        "variant_count_expected": 2 ** len(universe),
        "variant_count_generated": len(variants),
        "variants": variants,
    }
    write_json(GENERATED.parent / "case_b_variants.json", manifest)
    return manifest


def main() -> None:
    manifest = generate()
    print(f"generated {manifest['variant_count_generated']} Case B variants")


if __name__ == "__main__":
    main()
