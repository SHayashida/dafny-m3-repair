"""
m3lib: shared finite-model definitions for the M3 (Sen24) reportability-contract
audit over the Percent/Trend Dafny minimal example.

Conventions (match README section 3 and 6):

* Retained-set convention. Feasibility is indexed by the set of KEPT
  implementation levers K (subseteq LambdaI). Deleting a lever applies its
  corresponding source edit. SatPhi(K) is the measured Dafny verification
  outcome of the variant whose retained lever set is K.

* Levers (LambdaI): each lever means "keep the original commitment".
    T = KEEP_TREND_NONZERO_DOMAIN         (delete -> C1: Trend.requires span>0)
    P = KEEP_PERCENT_POSITIVE_PRECONDITION(delete -> C2: Percent.requires whole!=0)
    D = KEEP_DIRECT_PERCENT_CALL          (delete -> C3: Trend body guarded)

* Contract atoms (I):
    PC = ORIGINAL_PUBLIC_CONTRACT_SURFACE
    IB = ORIGINAL_IMPLEMENTATION_BEHAVIOR
  Block map beta:
    beta(PC) = {T, P}
    beta(IB) = {D}

This module contains NO hardcoded verification outcomes. SatPhi/SatPsi are
supplied at audit time from the measured Dafny results table.
"""

from itertools import chain, combinations

# ---- lever / atom identifiers -------------------------------------------------

T = "KEEP_TREND_NONZERO_DOMAIN"
P = "KEEP_PERCENT_POSITIVE_PRECONDITION"
D = "KEEP_DIRECT_PERCENT_CALL"

LAMBDA_I = frozenset({T, P, D})

PC = "ORIGINAL_PUBLIC_CONTRACT_SURFACE"
IB = "ORIGINAL_IMPLEMENTATION_BEHAVIOR"

I = frozenset({PC, IB})

BETA = {
    PC: frozenset({T, P}),
    IB: frozenset({D}),
}

# short codes for filenames / display
LEVER_CODE = {T: "T", P: "P", D: "D"}
ATOM_CODE = {PC: "PC", IB: "IB"}

# which edit a *deleted* lever applies
LEVER_EDIT = {
    T: "C1_caller_strengthen",
    P: "C2_callee_weaken",
    D: "C3_impl_change",
}


# ---- set utilities ------------------------------------------------------------

def powerset(s):
    s = list(s)
    return [frozenset(c) for c in chain.from_iterable(
        combinations(s, r) for r in range(len(s) + 1))]


def code_for_levers(k):
    """Stable filename token for a retained lever set K."""
    order = [T, P, D]
    tok = "".join(LEVER_CODE[x] for x in order if x in k)
    return tok if tok else "none"


def code_for_atoms(t):
    order = [PC, IB]
    tok = "".join(ATOM_CODE[x] for x in order if x in t)
    return tok if tok else "none"


def sorted_levers(k):
    order = [T, P, D]
    return [x for x in order if x in k]


def sorted_atoms(t):
    order = [PC, IB]
    return [x for x in order if x in t]


# ---- block-map derived operators (README 4) -----------------------------------

def beta_set(t):
    """betaSet(T) = union of beta(a) for a in T. Retained levers for a retained
    contract-atom set T."""
    out = set()
    for a in t:
        out |= set(BETA[a])
    return frozenset(out)


def group_touch_any(r):
    """groupTouchAny(R) = { a in I | R intersect beta(a) nonempty }.
    R is a *deletion* set of levers."""
    return frozenset(a for a in I if set(r) & set(BETA[a]))


def blocks_disjoint():
    seen = set()
    for a in I:
        b = set(BETA[a])
        if b & seen:
            return False
        seen |= b
    return True


def blocks_nonempty():
    return all(len(BETA[a]) > 0 for a in I)


def repair_atomicity():
    """M3 RepairAtomicity: forall a in I, |beta(a)| == 1. This is NOT the same as
    site-restricted candidate generation."""
    return all(len(BETA[a]) == 1 for a in I)


# ---- authoritative M3 definitions (README 6) ----------------------------------
# sat_phi : dict[frozenset lever] -> bool   (measured)
# sat_psi : dict[frozenset atom]  -> bool   (measured, from independent artifacts)

def raw_feasible(r, sat_phi):
    """RawFeasible(R) iff R subseteq LambdaI and SatPhi(LambdaI \\ R)."""
    if not r <= LAMBDA_I:
        return False
    return sat_phi[LAMBDA_I - r]


def raw_repairs(sat_phi):
    """RawRepair(R): raw-feasible and inclusion-minimal (no proper subset feasible)."""
    feas = [r for r in powerset(LAMBDA_I) if raw_feasible(r, sat_phi)]
    reps = []
    for r in feas:
        if not any((rp < r) for rp in feas):
            reps.append(r)
    return reps


def contract_feasible(g, sat_psi):
    """ContractFeasible(G) iff G subseteq I and SatPsi(I \\ G)."""
    if not g <= I:
        return False
    return sat_psi[I - g]


def contract_repairs(sat_psi):
    feas = [g for g in powerset(I) if contract_feasible(g, sat_psi)]
    reps = []
    for g in feas:
        if not any((gp < g) for gp in feas):
            reps.append(g)
    return reps


def raw_grouped_image(sat_phi):
    """{ groupTouchAny(R) | RawRepair(R) }."""
    imgs = []
    for r in raw_repairs(sat_phi):
        g = group_touch_any(r)
        if g not in imgs:
            imgs.append(g)
    return imgs


def grouped_repairs(sat_phi):
    """GroupedRepair(G): in raw grouped image AND inclusion-minimal *recomputed*
    over the grouped image (not merely dedup of groupTouchAny)."""
    img = raw_grouped_image(sat_phi)
    reps = []
    for g in img:
        if not any((gp < g) for gp in img):
            reps.append(g)
    return reps


def residual_faithfulness(sat_phi, sat_psi):
    """forall T subseteq I: SatPhi(betaSet(T)) iff SatPsi(T)."""
    checked = []
    cex = []
    result = True
    for t in powerset(I):
        lhs = sat_phi[beta_set(t)]
        rhs = sat_psi[t]
        ok = (lhs == rhs)
        checked.append({
            "retained_atoms": sorted_atoms(t),
            "beta_set_levers": sorted_levers(beta_set(t)),
            "sat_phi_beta_set": lhs,
            "sat_psi": rhs,
            "consistent": ok,
        })
        if not ok:
            result = False
            cex.append({"retained_atoms": sorted_atoms(t),
                        "sat_phi_beta_set": lhs, "sat_psi": rhs})
    return result, checked, cex


def group_soundness(sat_phi, sat_psi):
    """forall R subseteq LambdaI: SatPhi(LambdaI\\R) implies SatPsi(I\\groupTouchAny(R)).
    Checks ALL feasible implementation deletions, not just raw repairs."""
    checked = []
    cex = []
    result = True
    for r in powerset(LAMBDA_I):
        antecedent = sat_phi[LAMBDA_I - r]
        g = group_touch_any(r)
        consequent = sat_psi[I - g]
        ok = (not antecedent) or consequent
        checked.append({
            "deleted_levers": sorted_levers(r),
            "sat_phi_retained": antecedent,
            "group_touch_any": sorted_atoms(g),
            "retained_atoms_after_group_delete": sorted_atoms(I - g),
            "sat_psi_retained": consequent,
            "sound": ok,
        })
        if not ok:
            result = False
            cex.append({
                "deleted_levers": sorted_levers(r),
                "sat_phi_retained": antecedent,
                "group_touch_any": sorted_atoms(g),
                "sat_psi_retained": consequent,
            })
    return result, checked, cex


def psi_deletion_monotonicity(sat_psi):
    """forall T' subseteq T subseteq I: SatPsi(T) implies SatPsi(T').
    'Keeping fewer contract atoms (deleting more) preserves feasibility.'"""
    checked = []
    cex = []
    result = True
    atoms_ps = powerset(I)
    for t in atoms_ps:
        for tp in powerset(t):
            if not (tp <= t):
                continue
            antecedent = sat_psi[t]
            consequent = sat_psi[tp]
            ok = (not antecedent) or consequent
            checked.append({
                "retained_T": sorted_atoms(t),
                "retained_Tprime": sorted_atoms(tp),
                "sat_psi_T": antecedent,
                "sat_psi_Tprime": consequent,
                "monotone": ok,
            })
            if not ok:
                result = False
                cex.append({
                    "retained_T": sorted_atoms(t),
                    "retained_Tprime": sorted_atoms(tp),
                    "sat_psi_T": antecedent,
                    "sat_psi_Tprime": consequent,
                })
    return result, checked, cex


def grouped_correctness(sat_phi, sat_psi):
    """Pointwise grouped correctness (contract-relative exactness):
    forall G subseteq I: GroupedRepair(G) iff ContractRepair(G)."""
    greps = set(grouped_repairs(sat_phi))
    creps = set(contract_repairs(sat_psi))
    checked = []
    cex = []
    result = True
    for g in powerset(I):
        lhs = g in greps
        rhs = g in creps
        ok = (lhs == rhs)
        checked.append({
            "G": sorted_atoms(g),
            "grouped_repair": lhs,
            "contract_repair": rhs,
            "equal": ok,
        })
        if not ok:
            result = False
            cex.append({"G": sorted_atoms(g),
                        "grouped_repair": lhs, "contract_repair": rhs})
    return result, checked, cex


def m3c_applicable(blocks_disjoint_ok, residual_faithful_ok, psi_monotone_ok):
    """M3-C exactness characterization is applicable only when all three declared
    finite assumptions hold. Applicability is NOT a general theorem claim."""
    return bool(blocks_disjoint_ok and residual_faithful_ok and psi_monotone_ok)
