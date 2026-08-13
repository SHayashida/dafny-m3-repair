"""
Boundary tests for the LOCAL scope, asserted against the MEASURED audit artifact
(m3/results/reportability_audit_local.json). If Dafny ever measures a different
boundary, these tests fail loudly rather than silently agreeing with prior text.

Run scripts/reproduce.py (or generate+run+audit) first to produce the artifact.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.join(HERE, "..", "m3", "results", "reportability_audit_local.json")


def load():
    with open(AUDIT, encoding="utf-8") as f:
        return json.load(f)


def as_set_of_frozensets(list_of_lists):
    return {frozenset(x) for x in list_of_lists}


def test_local_raw_repairs_are_three_singletons():
    a = load()
    raw = as_set_of_frozensets(a["raw_repairs"])
    assert raw == {
        frozenset({"KEEP_TREND_NONZERO_DOMAIN"}),
        frozenset({"KEEP_PERCENT_POSITIVE_PRECONDITION"}),
        frozenset({"KEEP_DIRECT_PERCENT_CALL"}),
    }


def test_local_grouped_and_contract_repairs_match():
    a = load()
    grouped = as_set_of_frozensets(a["grouped_repairs"])
    contract = as_set_of_frozensets(a["contract_repairs"])
    expected = {
        frozenset({"ORIGINAL_PUBLIC_CONTRACT_SURFACE"}),
        frozenset({"ORIGINAL_IMPLEMENTATION_BEHAVIOR"}),
    }
    assert grouped == expected
    assert contract == expected


def test_local_all_predicates_pass():
    a = load()
    assert a["residual_faithfulness"]["result"] is True
    assert a["group_soundness"]["result"] is True
    assert a["psi_deletion_monotonicity"]["result"] is True
    assert a["grouped_correctness"]["result"] is True


def test_local_m3c_applicable():
    a = load()
    assert a["m3c_characterization"]["applicable"] is True
    # applicability requires all three declared assumptions
    assn = a["m3c_characterization"]["assumptions"]
    assert assn["blocks_disjoint"] is True
    assert assn["residual_faithfulness"] is True
    assert assn["psi_deletion_monotonicity"] is True
