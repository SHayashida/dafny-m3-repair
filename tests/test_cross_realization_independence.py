"""
Guard against the ResidualFaithfulness construction-tautology.

The implementation residuals and the reference-contract residuals must be
produced by DIFFERENT generators (different source, different hashes). This test
fails if any implementation residual for betaSet(T) shares a source hash with the
contract residual for T -- which would mean SatPsi was rebuilt from the same
rendering and ResidualFaithfulness would be trivially true.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, "..", "m3", "results", name), encoding="utf-8") as f:
        return json.load(f)


def _check_scope(audit):
    cr = audit["cross_realization"]
    assert cr["independent_source_realization"] is True
    for row in cr["rows"]:
        assert row["source_hashes_differ"] is True, (
            f"tautology: impl betaSet hash == contract hash for T="
            f"{row['retained_atoms']}")
    # faithfulness is now a genuine cross-realization conformance check
    assert audit["residual_faithfulness"]["result"] is True


def test_local_cross_realization_independent_and_faithful():
    _check_scope(load("reportability_audit_local.json"))


def test_closed_cross_realization_independent_and_faithful():
    _check_scope(load("reportability_audit_closed.json"))
