from __future__ import annotations

import sys
from pathlib import Path

CASE_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE_B / "scripts"))

from common import AUDIT, MEASUREMENTS, read_json  # noqa: E402
from fault_injections import run_fault_injections  # noqa: E402
from independent_audit import recompute  # noqa: E402


def test_independent_recomputation_exactly_matches_frozen_evidence():
    assert (MEASUREMENTS / "variant_results.json").exists()
    assert recompute()["passed"] is True


def test_fault_injections_are_all_rejected():
    report = run_fault_injections()
    assert report["all_faults_rejected"] is True
    assert len(report["faults"]) == 8


def test_stored_operator_invariants():
    audit = read_json(AUDIT / "case_b_operator_audit.json")
    assert audit["measurement_complete"] is True
    assert audit["structural_invariant_passed"] is True
    assert audit["singleton_order_isomorphism_passed"] is True
    assert audit["unexpected_reverse_difference"] == []
