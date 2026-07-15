"""
Boundary tests for the CLOSED-WORLD scope, asserted against the MEASURED audit
artifact (m3/results/reportability_audit_closed.json).

Key expected facts (from declared source-generation semantics, measured, not
hardcoded into the audit):
  * C1 (KEEP_TREND_NONZERO_DOMAIN deletion) is NOT a closed-world raw repair.
  * GroupSoundness FAILS with counterexample R = {KEEP_PERCENT_POSITIVE_PRECONDITION}.
  * GroupedCorrectness FAILS with counterexample G = {ORIGINAL_PUBLIC_CONTRACT_SURFACE}.
  * PsiDeletionMonotonicity FAILS.
  * M3-C characterization is NOT APPLICABLE.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "..", "m3", "results", "reportability_audit_closed.json")


def load():
    with open(AUDIT, encoding="utf-8") as f:
        return json.load(f)


def as_set_of_frozensets(list_of_lists):
    return {frozenset(x) for x in list_of_lists}


def test_closed_raw_repairs_exclude_c1():
    a = load()
    raw = as_set_of_frozensets(a["raw_repairs"])
    assert raw == {
        frozenset({"KEEP_PERCENT_POSITIVE_PRECONDITION"}),
        frozenset({"KEEP_DIRECT_PERCENT_CALL"}),
    }
    assert frozenset({"KEEP_TREND_NONZERO_DOMAIN"}) not in raw


def test_closed_contract_repair_is_impl_behavior_only():
    a = load()
    contract = as_set_of_frozensets(a["contract_repairs"])
    assert contract == {frozenset({"ORIGINAL_IMPLEMENTATION_BEHAVIOR"})}


def test_closed_group_soundness_fails_with_expected_counterexample():
    a = load()
    gs = a["group_soundness"]
    assert gs["result"] is False
    deleted = [set(c["deleted_levers"]) for c in gs["counterexamples"]]
    assert {"KEEP_PERCENT_POSITIVE_PRECONDITION"} in deleted


def test_closed_grouped_correctness_fails_with_expected_counterexample():
    a = load()
    gc = a["grouped_correctness"]
    assert gc["result"] is False
    gs = [set(c["G"]) for c in gc["counterexamples"]]
    assert {"ORIGINAL_PUBLIC_CONTRACT_SURFACE"} in gs


def test_closed_psi_monotonicity_fails():
    a = load()
    assert a["psi_deletion_monotonicity"]["result"] is False


def test_closed_m3c_not_applicable():
    a = load()
    m3c = a["m3c_characterization"]
    assert m3c["applicable"] is False
    # residual faithfulness still holds; the failure is NOT a faithfulness failure
    assert a["residual_faithfulness"]["result"] is True
