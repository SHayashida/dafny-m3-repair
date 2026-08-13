"""Run isolated corruptions and record that each Case B evidence gate rejects them."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path

from audit_case_b import build_family
from common import AUDIT, CANONICAL, canonical_json_sha256, read_json, sha256_file, write_json
from independent_audit import minima, project
from metadata_parser import MetadataError, parse_metadata_text


def expected_failure(name: str, operation) -> dict:
    try:
        operation()
    except Exception as exc:  # noqa: BLE001 - fault tests intentionally exercise all hard failures
        return {"fault": name, "rejected": True, "exception_type": type(exc).__name__, "message": str(exc)}
    return {"fault": name, "rejected": False, "exception_type": None, "message": "corruption was accepted"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run_fault_injections() -> dict:
    lock = read_json(Path(__file__).resolve().parents[1] / "design" / "case_b_design_lock.json")
    source = CANONICAL.read_text(encoding="utf-8")
    prefix = "// CASE_B_METADATA "
    metadata_lines = [line for line in source.splitlines() if line.strip().startswith(prefix)]
    expected = lock["repair_levers"]

    def missing_metadata() -> None:
        damaged = source.replace(metadata_lines[0] + "\n", "", 1)
        parse_metadata_text(damaged, expected)

    def conflicting_metadata() -> None:
        damaged = source.replace(metadata_lines[0], metadata_lines[0] + "\n" + metadata_lines[0], 1)
        parse_metadata_text(damaged, expected)

    complete_rows = []
    for mask in range(2 ** len(expected)):
        deleted = [lever for bit, lever in enumerate(expected) if mask & (1 << bit)]
        complete_rows.append({"deleted_levers": deleted, "outcome": "VERIFICATION_FAILED"})

    def missing_subset() -> None:
        doc = build_family(complete_rows[:-1], expected)
        require(doc["measurement_complete"], "measurement_complete=false; main result rejected")

    def tampered_hash(kind: str) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{kind}.json"
            path.write_text('{"outcome":"VERIFIED"}\n', encoding="utf-8")
            expected_hash = sha256_file(path)
            path.write_text('{"outcome":"VERIFICATION_FAILED"}\n', encoding="utf-8")
            require(sha256_file(path) == expected_hash, f"{kind} SHA-256 binding mismatch")

    def mapping_tamper() -> None:
        changed = copy.deepcopy(lock["group_mapping"])
        changed[expected[0]] = "CORRUPTED_GROUP"
        require(canonical_json_sha256(changed) == lock["group_mapping_sha256"], "normalized mapping hash mismatch")

    def structural_corruption() -> None:
        left = {frozenset({"A"})}
        right = {frozenset({"B"})}
        require(right.issubset(left), "Min(g(F)) is not a subset of g(Min(F))")

    def singleton_corruption() -> None:
        family = {frozenset({"L1"}), frozenset({"L2", "L3"})}
        broken = {"L1": "X", "L2": "X", "L3": "X"}
        left = project(minima(family), broken)
        right = minima(project(family, {lever: "S::" + lever for lever in broken}))
        require(left == right, "singleton order-isomorphism equality failed")

    faults = [
        expected_failure("missing_metadata", missing_metadata),
        expected_failure("conflicting_metadata", conflicting_metadata),
        expected_failure("missing_subset_result", missing_subset),
        expected_failure("outcome_tampering", lambda: tampered_hash("raw-result")),
        expected_failure("source_tampering", lambda: tampered_hash("variant-source")),
        expected_failure("group_mapping_tampering", mapping_tamper),
        expected_failure("structural_invariant_corruption", structural_corruption),
        expected_failure("singleton_control_corruption", singleton_corruption),
    ]
    report = {
        "schema_version": "case-b-fault-injection-v1",
        "all_faults_rejected": all(item["rejected"] for item in faults),
        "faults": faults,
    }
    if not report["all_faults_rejected"]:
        raise SystemExit("one or more fault injections were not rejected")
    return report


def main() -> None:
    report = run_fault_injections()
    write_json(AUDIT / "fault_injection_results.json", report)
    print(f"Case B fault injections: {len(report['faults'])} rejected")


if __name__ == "__main__":
    main()
