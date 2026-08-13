"""Independent Case B recomputation path; intentionally does not call audit helpers."""

from __future__ import annotations

from common import (
    AUDIT, CANONICAL, DESIGN_LOCK, MEASUREMENTS, ROOT, canonical_json_sha256, read_json,
    sha256_file, write_json,
)
from design_lock import verify_lock
from metadata_parser import parse_metadata_file


class IndependentAuditError(ValueError):
    pass


def serialize(family: set[frozenset[str]], order: list[str]) -> list[list[str]]:
    positions = {item: number for number, item in enumerate(order)}
    rows = [sorted(item, key=positions.__getitem__) for item in family]
    return sorted(rows, key=lambda row: (len(row), [positions[item] for item in row]))


def minima(family: set[frozenset[str]]) -> set[frozenset[str]]:
    answer: set[frozenset[str]] = set()
    for candidate in family:
        proper_subset_exists = False
        for possible_subset in family:
            if possible_subset != candidate and possible_subset.issubset(candidate):
                proper_subset_exists = True
                break
        if not proper_subset_exists:
            answer.add(candidate)
    return answer


def project(family: set[frozenset[str]], mapping: dict[str, str]) -> set[frozenset[str]]:
    answer: set[frozenset[str]] = set()
    for raw in family:
        image: set[str] = set()
        for lever in raw:
            image.add(mapping[lever])
        answer.add(frozenset(image))
    return answer


def recompute() -> dict:
    lock = verify_lock()
    records = parse_metadata_file(CANONICAL, lock["repair_levers"])
    parsed_mapping = {record["lever_id"]: record["report_group"] for record in records}
    parsed_mapping = {lever: parsed_mapping[lever] for lever in sorted(parsed_mapping)}
    if parsed_mapping != lock["group_mapping"]:
        raise IndependentAuditError("independently parsed mapping differs from frozen mapping")
    if canonical_json_sha256(parsed_mapping) != lock["group_mapping_sha256"]:
        raise IndependentAuditError("independently parsed mapping hash differs from frozen hash")

    index = read_json(MEASUREMENTS / "variant_results.json")
    manifest_path = ROOT / index["variant_manifest"]
    if sha256_file(manifest_path) != index["variant_manifest_sha256"]:
        raise IndependentAuditError("variant manifest was modified")
    manifest = read_json(manifest_path)
    by_id = {variant["variant_id"]: variant for variant in manifest["variants"]}
    if len(by_id) != 2 ** len(lock["repair_levers"]):
        raise IndependentAuditError("variant manifest does not cover the exhaustive lattice")

    measured: dict[str, dict] = {}
    for pointer in index["results"]:
        path = ROOT / pointer["raw_result"]
        if sha256_file(path) != pointer["raw_result_sha256"]:
            raise IndependentAuditError(f"raw result was modified: {pointer['variant_id']}")
        row = read_json(path)
        identifier = row["variant_id"]
        if identifier in measured or identifier not in by_id:
            raise IndependentAuditError(f"duplicate or unknown result: {identifier}")
        if row["outcome"] != pointer["outcome"]:
            raise IndependentAuditError(f"index/raw outcome mismatch: {identifier}")
        source = ROOT / row["source"]
        if sha256_file(source) != row["source_sha256"] or row["source_sha256"] != by_id[identifier]["source_sha256"]:
            raise IndependentAuditError(f"source binding failed: {identifier}")
        measured[identifier] = row
    if set(measured) != set(by_id):
        raise IndependentAuditError("one or more subset results are missing")

    allowed = {"VERIFIED", "VERIFICATION_FAILED"}
    if any(row["outcome"] not in allowed for row in measured.values()):
        raise IndependentAuditError("measurement contains frontend, timeout, or tool outcomes")
    family = {frozenset(row["deleted_levers"]) for row in measured.values() if row["outcome"] == "VERIFIED"}
    raw_min = minima(family)
    full_image = project(family, parsed_mapping)
    raw_min_image = project(raw_min, parsed_mapping)
    min_full_image = minima(full_image)
    if not min_full_image.issubset(raw_min_image):
        raise IndependentAuditError("structural inclusion failed")

    singleton_mapping = {lever: "SINGLETON::" + lever for lever in lock["repair_levers"]}
    singleton_left = project(raw_min, singleton_mapping)
    singleton_right = minima(project(family, singleton_mapping))
    if singleton_left != singleton_right:
        raise IndependentAuditError("singleton order-isomorphism control failed")

    stored_family = read_json(MEASUREMENTS / "case_b_family.json")
    stored_audit = read_json(AUDIT / "case_b_operator_audit.json")
    expected_fields = {
        "verified_family": serialize(family, lock["repair_levers"]),
        "raw_minimal_family": serialize(raw_min, lock["repair_levers"]),
        "grouped_full_image": serialize(full_image, lock["groups"]),
        "grouped_raw_minimal_image": serialize(raw_min_image, lock["groups"]),
        "minimal_grouped_full_image": serialize(min_full_image, lock["groups"]),
        "structural_invariant_passed": True,
        "singleton_order_isomorphism_passed": True,
        "commutes": raw_min_image == min_full_image,
        "unexpected_reverse_difference": [],
    }
    for field, expected in expected_fields.items():
        if stored_audit.get(field) != expected:
            raise IndependentAuditError(f"stored audit mismatch in {field}")
    if stored_family.get("verified_deletion_family") != expected_fields["verified_family"]:
        raise IndependentAuditError("stored family differs from raw-result reconstruction")
    if stored_family.get("measurement_complete") is not True:
        raise IndependentAuditError("stored family is not marked complete")
    return {
        "schema_version": "case-b-independent-audit-v1",
        "design_lock_sha256": sha256_file(DESIGN_LOCK),
        "raw_results_reconstructed": len(measured),
        "mapping_independently_parsed": True,
        "stored_family_exact_match": True,
        "stored_operator_audit_exact_match": True,
        "structural_invariant_passed": True,
        "singleton_order_isomorphism_passed": True,
        "passed": True,
    }


def main() -> None:
    report = recompute()
    write_json(AUDIT / "independent_recomputation.json", report)
    print("Case B independent recomputation: OK")


if __name__ == "__main__":
    main()
