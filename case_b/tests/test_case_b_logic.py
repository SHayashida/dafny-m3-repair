from __future__ import annotations

import sys
from pathlib import Path

CASE_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE_B / "scripts"))

from audit_case_b import build_family, grouped_image, inclusion_minimal  # noqa: E402
from measure_variants import classify_outcome  # noqa: E402


def test_inclusion_minimal_is_not_minimum_cardinality():
    family = {frozenset({"a"}), frozenset({"b", "c"}), frozenset({"a", "d"})}
    assert inclusion_minimal(family) == {frozenset({"a"}), frozenset({"b", "c"})}


def test_structural_inclusion_and_noncommuting_shape():
    family = {frozenset({"a"}), frozenset({"b", "c"}), frozenset({"a", "b"})}
    mapping = {"a": "X", "b": "X", "c": "Y"}
    raw_min = inclusion_minimal(family)
    left = grouped_image(raw_min, mapping)
    right = inclusion_minimal(grouped_image(family, mapping))
    assert right < left
    assert frozenset({"X", "Y"}) in left - right
    assert frozenset({"X"}) in right


def test_missing_result_marks_measurement_incomplete():
    universe = ["a", "b"]
    rows = [
        {"deleted_levers": [], "outcome": "VERIFICATION_FAILED"},
        {"deleted_levers": ["a"], "outcome": "VERIFIED"},
        {"deleted_levers": ["b"], "outcome": "VERIFIED"},
    ]
    assert build_family(rows, universe)["measurement_complete"] is False


def test_outcome_classifier_distinguishes_failures():
    assert classify_outcome(0, "Dafny program verifier finished with 1 verified, 0 errors", "") == "VERIFIED"
    assert classify_outcome(4, "Error: assertion might not hold\nDafny program verifier finished with 0 verified, 1 error", "") == "VERIFICATION_FAILED"
    assert classify_outcome(1, "Parser errors detected", "") == "FRONTEND_ERROR"
    assert classify_outcome(70, "", "host crashed") == "TOOL_ERROR"
