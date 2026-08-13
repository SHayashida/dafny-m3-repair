"""Primary measured-family and operator-order audit for Case B."""

from __future__ import annotations

from itertools import combinations
from typing import Iterable

from common import AUDIT, DESIGN_LOCK, MEASUREMENTS, RAW, ROOT, read_json, relative, sha256_file, write_json
from design_lock import verify_lock


class EvidenceError(ValueError):
    pass


def as_set_family(serialized: Iterable[Iterable[str]]) -> set[frozenset[str]]:
    return {frozenset(item) for item in serialized}


def ordered_family(family: Iterable[frozenset[str]], universe_order: list[str]) -> list[list[str]]:
    index = {value: position for position, value in enumerate(universe_order)}
    values = [sorted(item, key=index.__getitem__) for item in set(family)]
    return sorted(values, key=lambda item: (len(item), [index[value] for value in item]))


def inclusion_minimal(family: Iterable[frozenset[str]]) -> set[frozenset[str]]:
    materialized = set(family)
    return {item for item in materialized if not any(other < item for other in materialized)}


def grouped_image(family: Iterable[frozenset[str]], mapping: dict[str, str]) -> set[frozenset[str]]:
    return {frozenset(mapping[lever] for lever in item) for item in family}


def load_bound_raw_results() -> tuple[dict, dict, list[dict]]:
    lock = verify_lock()
    index_path = MEASUREMENTS / "variant_results.json"
    index = read_json(index_path)
    manifest_path = ROOT / index["variant_manifest"]
    if sha256_file(manifest_path) != index["variant_manifest_sha256"]:
        raise EvidenceError("variant manifest hash mismatch")
    manifest = read_json(manifest_path)
    expected_ids = {variant["variant_id"] for variant in manifest["variants"]}
    indexed_ids = {entry["variant_id"] for entry in index["results"]}
    if expected_ids != indexed_ids or len(index["results"]) != len(expected_ids):
        raise EvidenceError("raw result lattice is missing, duplicated, or has unknown variants")
    results = []
    variants = {variant["variant_id"]: variant for variant in manifest["variants"]}
    for pointer in index["results"]:
        raw_path = ROOT / pointer["raw_result"]
        if sha256_file(raw_path) != pointer["raw_result_sha256"]:
            raise EvidenceError(f"raw evidence hash mismatch: {pointer['variant_id']}")
        raw = read_json(raw_path)
        variant = variants[pointer["variant_id"]]
        if raw["variant_id"] != pointer["variant_id"] or raw["outcome"] != pointer["outcome"]:
            raise EvidenceError(f"raw/index mismatch: {pointer['variant_id']}")
        source = ROOT / raw["source"]
        if sha256_file(source) != raw["source_sha256"] or raw["source_sha256"] != variant["source_sha256"]:
            raise EvidenceError(f"variant source hash mismatch: {pointer['variant_id']}")
        if raw["design_lock_sha256"] != sha256_file(DESIGN_LOCK):
            raise EvidenceError(f"design lock binding mismatch: {pointer['variant_id']}")
        if raw["group_mapping_sha256"] != lock["group_mapping_sha256"]:
            raise EvidenceError(f"group mapping binding mismatch: {pointer['variant_id']}")
        results.append(raw)
    return lock, index, results


def build_family(results: list[dict], universe: list[str]) -> dict:
    counts = {outcome: sum(row["outcome"] == outcome for row in results) for outcome in (
        "VERIFIED", "VERIFICATION_FAILED", "FRONTEND_ERROR", "TIMEOUT", "TOOL_ERROR"
    )}
    expected = 2 ** len(universe)
    complete = len(results) == expected and counts["VERIFIED"] + counts["VERIFICATION_FAILED"] == expected and all(
        counts[outcome] == 0 for outcome in ("FRONTEND_ERROR", "TIMEOUT", "TOOL_ERROR")
    )
    verified = {frozenset(row["deleted_levers"]) for row in results if row["outcome"] == "VERIFIED"}
    return {
        "schema_version": "case-b-family-v1",
        "lever_universe": universe,
        "variant_count_expected": expected,
        "variant_count_measured": len(results),
        "outcome_counts": counts,
        "verified_deletion_family": ordered_family(verified, universe),
        "measurement_complete": complete,
    }


def compute_audit(lock: dict, family_doc: dict) -> tuple[dict, dict]:
    if not family_doc["measurement_complete"]:
        raise EvidenceError("measurement is incomplete; refusing to accept a main Case B result")
    universe = lock["repair_levers"]
    groups = lock["groups"]
    family = as_set_family(family_doc["verified_deletion_family"])
    raw_minimal = inclusion_minimal(family)
    grouped_full = grouped_image(family, lock["group_mapping"])
    grouped_raw_minimal = grouped_image(raw_minimal, lock["group_mapping"])
    minimal_grouped_full = inclusion_minimal(grouped_full)
    unexpected_reverse = minimal_grouped_full - grouped_raw_minimal
    structural_passed = not unexpected_reverse
    if not structural_passed:
        raise EvidenceError("structural invariant violated: Min(g(F)) is not a subset of g(Min(F))")

    excess = grouped_raw_minimal - minimal_grouped_full
    witnesses = []
    for group_set in sorted(excess, key=lambda value: (len(value), sorted(value))):
        dominators = [candidate for candidate in grouped_full if candidate < group_set]
        if not dominators:
            raise EvidenceError(f"missing domination witness for {sorted(group_set)}")
        dominated_raw = next(raw for raw in raw_minimal if frozenset(lock["group_mapping"][x] for x in raw) == group_set)
        dominating_group = min(dominators, key=lambda value: (len(value), sorted(value)))
        dominating_raw = next(raw for raw in family if frozenset(lock["group_mapping"][x] for x in raw) == dominating_group)
        witnesses.append({
            "G": sorted(group_set, key=groups.index),
            "H": sorted(dominating_group, key=groups.index),
            "raw_variant_R_G": sorted(dominated_raw, key=universe.index),
            "raw_variant_R_H": sorted(dominating_raw, key=universe.index),
            "relation": "H is a proper subset of G",
        })

    singleton_mapping = {lever: f"SINGLETON::{lever}" for lever in universe}
    singleton_groups = [singleton_mapping[lever] for lever in universe]
    singleton_left = grouped_image(raw_minimal, singleton_mapping)
    singleton_right = inclusion_minimal(grouped_image(family, singleton_mapping))
    singleton_passed = singleton_left == singleton_right
    singleton_doc = {
        "schema_version": "case-b-singleton-control-v1",
        "control_type": "implementation sanity control / order-isomorphism control",
        "singleton_mapping": singleton_mapping,
        "grouped_raw_minimal_image": ordered_family(singleton_left, singleton_groups),
        "minimal_grouped_full_image": ordered_family(singleton_right, singleton_groups),
        "passed": singleton_passed,
    }
    if not singleton_passed:
        raise EvidenceError("singleton order-isomorphism control failed")

    audit = {
        "schema_version": "case-b-operator-audit-v1",
        "design_lock_sha256": sha256_file(DESIGN_LOCK),
        "measurement_complete": True,
        "lever_universe": universe,
        "group_mapping": lock["group_mapping"],
        "verified_family": ordered_family(family, universe),
        "raw_minimal_family": ordered_family(raw_minimal, universe),
        "grouped_full_image": ordered_family(grouped_full, groups),
        "grouped_raw_minimal_image": ordered_family(grouped_raw_minimal, groups),
        "minimal_grouped_full_image": ordered_family(minimal_grouped_full, groups),
        "structural_invariant_passed": structural_passed,
        "singleton_order_isomorphism_passed": singleton_passed,
        "commutes": grouped_raw_minimal == minimal_grouped_full,
        "noncommutativity_witnesses": witnesses,
        "unexpected_reverse_difference": ordered_family(unexpected_reverse, groups),
        "claim_scope": "this frozen finite Dafny Case B only",
    }
    return audit, singleton_doc


def run_audit() -> dict:
    lock, _index, results = load_bound_raw_results()
    family = build_family(results, lock["repair_levers"])
    write_json(MEASUREMENTS / "case_b_family.json", family)
    audit, singleton = compute_audit(lock, family)
    write_json(AUDIT / "case_b_operator_audit.json", audit)
    write_json(AUDIT / "singleton_sanity_control.json", singleton)
    return audit


def main() -> None:
    audit = run_audit()
    print(f"Case B operator audit complete; commutes={audit['commutes']}")


if __name__ == "__main__":
    main()
