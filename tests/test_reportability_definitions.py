"""
Unit tests for the M3 definitions in scripts/m3lib.py, exercised on synthetic
SatPhi/SatPsi tables. These test the DEFINITIONS, independent of Dafny, so a
regression in the finite-model logic is caught even without re-running Dafny.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
import m3lib as m3  # noqa: E402


def phi_from_fail_set(fail_keys):
    """Build SatPhi over all 8 lever sets; PASS unless the retained set is in
    fail_keys (given as frozensets)."""
    return {k: (k not in fail_keys) for k in m3.powerset(m3.LAMBDA_I)}


def psi_from_fail_set(fail_keys):
    return {t: (t not in fail_keys) for t in m3.powerset(m3.I)}


def test_block_map_properties():
    assert m3.blocks_disjoint() is True
    assert m3.blocks_nonempty() is True
    # ORIGINAL_PUBLIC_CONTRACT_SURFACE has 2 levers -> not atomic
    assert m3.repair_atomicity() is False


def test_beta_set_and_group_touch():
    assert m3.beta_set(frozenset({m3.PC})) == frozenset({m3.T, m3.P})
    assert m3.beta_set(frozenset({m3.IB})) == frozenset({m3.D})
    assert m3.beta_set(m3.I) == m3.LAMBDA_I
    # deleting the C2 lever (P) touches only the public-contract atom
    assert m3.group_touch_any(frozenset({m3.P})) == frozenset({m3.PC})
    assert m3.group_touch_any(frozenset({m3.D})) == frozenset({m3.IB})
    assert m3.group_touch_any(frozenset({m3.T, m3.D})) == frozenset({m3.PC, m3.IB})


def test_raw_repair_minimality():
    # only the base (retain everything) fails => each single deletion is a raw repair
    sp = phi_from_fail_set({m3.LAMBDA_I})
    reps = set(m3.raw_repairs(sp))
    assert reps == {frozenset({m3.T}), frozenset({m3.P}), frozenset({m3.D})}


def test_grouped_repair_recomputes_minimality():
    # Construct SatPhi where raw repairs map to grouped images {PC} and {PC,IB};
    # GroupedRepair must drop the non-minimal {PC,IB}.
    # Fails: retain-all, and retain {P} (so R={T,D} not feasible as a repair base).
    sp = {k: True for k in m3.powerset(m3.LAMBDA_I)}
    sp[m3.LAMBDA_I] = False          # base fails
    sp[frozenset({m3.P})] = False    # retaining only P fails => R={T,D} infeasible
    reps = m3.raw_repairs(sp)
    imgs = m3.raw_grouped_image(sp)
    grouped = set(m3.grouped_repairs(sp))
    # {PC,IB} may appear in the raw image but must not be a grouped repair if {PC}
    # or {IB} is present and strictly smaller
    for g in grouped:
        assert not any(gp < g for gp in imgs)


def test_group_soundness_detects_nonatomic_leak():
    # closed-world-like table: SatPhi passes for retained {T},{T,P},{T,D};
    # SatPsi passes only for retained {PC}. Expect GroupSoundness False with the
    # counterexample R={P}.
    phi_pass = {frozenset({m3.T}), frozenset({m3.T, m3.P}), frozenset({m3.T, m3.D})}
    sp = {k: (k in phi_pass) for k in m3.powerset(m3.LAMBDA_I)}
    psi_pass = {frozenset({m3.PC})}
    ps = {t: (t in psi_pass) for t in m3.powerset(m3.I)}
    ok, _checked, cex = m3.group_soundness(sp, ps)
    assert ok is False
    deleted = [set(c["deleted_levers"]) for c in cex]
    assert {"KEEP_PERCENT_POSITIVE_PRECONDITION"} in deleted


def test_psi_monotonicity_direction():
    # SatPsi(T)=True but SatPsi(T' subset)=False must be flagged (deleting MORE
    # contract atoms should preserve feasibility; violation => False).
    psi_pass = {frozenset({m3.PC})}  # {} fails
    ps = {t: (t in psi_pass) for t in m3.powerset(m3.I)}
    ok, _checked, cex = m3.psi_deletion_monotonicity(ps)
    assert ok is False
    assert any(c["retained_Tprime"] == [] for c in cex)


def test_grouped_correctness_equivalence():
    # identical grouped and contract repairs => True
    sp = phi_from_fail_set({m3.LAMBDA_I})
    ps = psi_from_fail_set({m3.I})
    ok, _checked, _cex = m3.grouped_correctness(sp, ps)
    assert ok is True


def test_m3c_gate_requires_all_assumptions():
    assert m3.m3c_applicable(True, True, True) is True
    assert m3.m3c_applicable(True, True, False) is False
    assert m3.m3c_applicable(True, False, True) is False
