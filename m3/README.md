# M3 reportability-contract finite audit (Dafny Percent/Trend example)

This artifact aligns the soundness/exactness terminology of this repository with
the **Sen24 M3 reportability-contract** definitions, and adds an executable,
machine-decided finite audit over a small Dafny example. Every verification
outcome is **measured** with Dafny 4.11.0; nothing is hardcoded.

> Scope-honest claims are stated up front:
>
> * `CandidateAttributeValidity` is **not** M3 `GroupSoundness`.
> * `C1` is a **local** repair but **not** a closed-world repair.
> * `A-only` and `B-only` are **site-restricted generation policies, not
>   `RepairAtomicity`**.
> * The reference predicate `SatPsi` is **artifact-defined**.
> * **No Lean theorem is proved** in this repository.
> * The finite audit **does not establish a general result** about Dafny or
>   formal model repair.
> * **Exactness** means pointwise equality between `GroupedRepair` and
>   `ContractRepair` under the declared contract.

---

## 1. Research question

Given one Dafny verification failure caused by a caller/callee contract
mismatch, several low-level repairs make the verifier succeed. They imply
**different** upper-level specification changes (responsibility, admissible
input, API compatibility). The question is which **reportability** relationship
holds between low-level repairs and contract-level repairs, and under which
declared assumptions the M3-C exactness characterization applies.

## 2. Dafny failure and C1/C2/C3 candidates

Base example (`base.dfy`): `Percent` has an over-restrictive precondition
(`whole > 0`) even though its body is total for `whole != 0`; `Trend` calls it
with only `span != 0` guaranteed.

```dafny
method Percent(part: int, whole: int) returns (r: int)
  requires whole > 0
  ensures  r == part * 100 / whole
{ r := part * 100 / whole; }

method Trend(delta: int, span: int) returns (r: int)
  requires span != 0
{ r := Percent(delta, span); }     // FAIL: cannot prove whole > 0
```

Three candidate edits:

| id | edit | public contract changed | implementation changed |
|---|---|---|---|
| C1 | `Trend.requires span != 0 => span > 0` | yes (caller) | no |
| C2 | `Percent.requires whole > 0 => whole != 0` | yes (callee) | no |
| C3 | `Trend` direct call => guarded body | no | yes |

The hand-written `base.dfy`, `C1_caller_strengthen.dfy`, `C2_callee_weaken.dfy`,
`C3_impl_change.dfy` and their `.csv` logs are retained as primary evidence.

## 3. Validation scopes

Verification success is **scope-relative**. Two scopes are evaluated over the
same lattice:

* **Local scope**: `Percent`, `Ratio`, `Trend`.
* **Closed-world scope**: adds `TrendUserOK` (guarantees `s > 0`) and
  `TrendUserNonzero` (guarantees only `s != 0`).

Corrected claim (replacing the earlier, wrong "C1/C2/C3 all succeed"):

```text
C1 is locally validated for the repaired caller-callee pair, but fails
closed-world compatibility validation when the existing nonzero-only upstream
client (TrendUserNonzero) is included.

C2 and C3 pass both the local target scope and the declared closed-world
client scope.
```

Per-candidate fields are recorded in `results/candidate_attribute_validity.json`:
`validated_local`, `validated_closed_world`, `existing_clients_preserved`,
`public_contract_changed`, `implementation_changed`, `adopted`,
`rejection_reason`.

## 4. Application-side candidate attribute audit (NOT GroupSoundness)

The predicate previously written as "if a low-level repair verifies, `rho(e)`
satisfies `Q`" is **renamed** to `CandidateAttributeValidity` (a.k.a.
`DecisionAuditPredicate` / `ApplicationSideAudit`). It records the factual
attributes of each candidate (input-domain change, public-contract change,
implementation change, existing-client preservation, responsibility location)
and separates `validated` from `adopted`. It is a decision-support audit and is
**deliberately kept in a separate section and file** from M3 `GroupSoundness`.

Measured (`results/candidate_attribute_validity.json`):

| id | validated_local | validated_closed_world | existing_clients_preserved | rejection_reason |
|---|---|---|---|---|
| C1 | true | **false** | false | breaks nonzero-only upstream client (closed world) |
| C2 | true | true | true | — |
| C3 | true | true | true | — |

## 5. M3 reportability contract

Retained-set convention (feasibility indexed by the **kept** set):

Implementation levers `LambdaI` (a lever = "keep the original commitment"):

```text
KEEP_TREND_NONZERO_DOMAIN          delete -> C1
KEEP_PERCENT_POSITIVE_PRECONDITION delete -> C2
KEEP_DIRECT_PERCENT_CALL           delete -> C3
```

Contract atoms `I` and block map `beta` (`model/reportability_contract.json`):

```text
I = { ORIGINAL_PUBLIC_CONTRACT_SURFACE (PC), ORIGINAL_IMPLEMENTATION_BEHAVIOR (IB) }
beta(PC) = { KEEP_TREND_NONZERO_DOMAIN, KEEP_PERCENT_POSITIVE_PRECONDITION }
beta(IB) = { KEEP_DIRECT_PERCENT_CALL }
```

`beta` is pairwise disjoint and nonempty. `|beta(PC)| = 2`, so **RepairAtomicity
(`forall a in I, |beta(a)| = 1`) is false** — this is an **M3-B (non-atomic)**
case. Site-restricted generation (section 12) is a separate policy, **not**
RepairAtomicity.

Derived operators: `betaSet(T) = union of beta(a) for a in T`,
`groupTouchAny(R) = { a in I | R ∩ beta(a) ≠ ∅ }`.

## 6. Authoritative definitions (implemented in `scripts/m3lib.py`)

```text
RawFeasible_scope(R)      iff R ⊆ LambdaI and SatPhi_scope(LambdaI \ R)
RawRepair_scope(R)        iff RawFeasible(R) and no proper subset is RawFeasible
ContractFeasible_scope(G) iff G ⊆ I and SatPsi_scope(I \ G)
ContractRepair_scope(G)   iff ContractFeasible(G) and no proper subset is ContractFeasible
IsRawGroup_scope(G)       iff exists R, RawRepair(R) and groupTouchAny(R) = G
GroupedRepair_scope(G)    iff IsRawGroup(G) and G inclusion-minimal in the raw grouped image
ResidualFaithfulness_scope   iff forall T ⊆ I, SatPhi(betaSet(T)) iff SatPsi(T)
GroupSoundness_scope         iff forall R ⊆ LambdaI, SatPhi(LambdaI\R) => SatPsi(I\groupTouchAny(R))
GroupedCorrectness_scope     iff forall G ⊆ I, GroupedRepair(G) iff ContractRepair(G)
PsiDeletionMonotonicity_scope iff forall T' ⊆ T ⊆ I, SatPsi(T) => SatPsi(T')
```

Notes:
* `GroupSoundness` checks **all** feasible implementation deletions, not only raw
  repairs. Checking raw repairs only is the weaker **raw-minimal audit**; it can
  be promoted to unrestricted `GroupSoundness` only when `PsiDeletionMonotonicity`
  holds (M3 `audit_cost_collapse`).
* `GroupedRepair` recomputes inclusion-minimality over the grouped image; it is
  not merely `groupTouchAny(RawRepair)` deduplicated.
* `SatPsi` is the measured outcome of an **independently materialized**
  block-aligned artifact, not a code alias of `SatPhi`.
* The prior definition "low-level repairs under `rho` equal repairs under `Q`" is
  **removed**; exactness is `GroupedRepair(G) iff ContractRepair(G)`.

## 7. Local-scope finite audit (measured)

`results/reportability_audit_local.json`, `results/summary.md`:

```text
RawRepair       = { {KEEP_TREND_NONZERO_DOMAIN}, {KEEP_PERCENT_POSITIVE_PRECONDITION}, {KEEP_DIRECT_PERCENT_CALL} }
GroupedRepair   = { {PC}, {IB} }
ContractRepair  = { {PC}, {IB} }
ResidualFaithfulness    = PASS
GroupSoundness          = PASS
PsiDeletionMonotonicity = PASS
GroupedCorrectness      = PASS
M3-C characterization applicable = YES
```

## 8. Closed-world finite audit (measured)

`results/reportability_audit_closed.json`:

```text
RawRepair       = { {KEEP_PERCENT_POSITIVE_PRECONDITION}, {KEEP_DIRECT_PERCENT_CALL} }   (C1 excluded)
GroupedRepair   = { {PC}, {IB} }
ContractRepair  = { {IB} }
ResidualFaithfulness    = PASS
GroupSoundness          = FAIL
PsiDeletionMonotonicity = FAIL
GroupedCorrectness      = FAIL
M3-C characterization applicable = NO
```

`C1` is **not** a closed-world `RawRepair`: deleting only
`KEEP_TREND_NONZERO_DOMAIN` yields retained set `{P, D}`, whose closed-world
artifact fails because `TrendUserNonzero` cannot prove `span > 0`.

## 9. GroupSoundness counterexample

Measured counterexample `R = { KEEP_PERCENT_POSITIVE_PRECONDITION }` (apply C2
only):

```text
SatPhi_closed(LambdaI \ R) = SatPhi_closed({T, D}) = true
groupTouchAny(R) = { ORIGINAL_PUBLIC_CONTRACT_SURFACE }
SatPsi_closed(I \ groupTouchAny(R)) = SatPsi_closed({IB}) = false
=> true implies false  => GroupSoundness FAILS
```

Deleting the whole non-atomic block `PC` couples C1 and C2; C1 breaks the
nonzero-only client, so the block-aligned reference residual is infeasible even
though the C2-only implementation residual is feasible. This is a **non-atomic
block leak**, not a faithfulness failure (`ResidualFaithfulness` still PASSES).

## 10. Grouped correctness / exactness result

Local: `GroupedRepair = ContractRepair = {{PC},{IB}}` → exactness holds.

Closed-world: `GroupedRepair = {{PC},{IB}}` but `ContractRepair = {{IB}}`.
Counterexample `G = {PC}`: `GroupedRepair(G)=true`, `ContractRepair(G)=false` →
exactness **fails**.

## 11. M3-C applicability boundary

M3-C exactness characterization is reported only when `BlocksDisjoint`,
`ResidualFaithfulness`, and `PsiDeletionMonotonicity` all hold.

* Local: all three hold → **applicable**; `GroupSoundness` and
  `GroupedCorrectness` are both PASS, **consistent with** the M3-C
  characterization under the declared artifact-defined contract and verified
  finite assumptions.
* Closed-world: `PsiDeletionMonotonicity` fails → **NOT APPLICABLE**.
  `GroupSoundness` and `GroupedCorrectness` both FAIL, but this is recorded as
  two independent measured facts, **not** as an empirical proof of the
  necessary-and-sufficient condition.

## 12. Site-restricted generation experiment

Three candidate-generation policies (renamed from the earlier, incorrect
"atomic" naming):

```text
A: caller-site-restricted candidate generation             -> finds C1 only
B: callee-contract-site-restricted candidate generation    -> finds C2 only
C: raw-candidate retention with post-hoc audit             -> retains C1, C2, C3
```

These are **generation-site restrictions, not `RepairAtomicity`**. In the local
scope, A loses C2 and B loses C1; C retains all candidates and audits them.

## 13. Claim boundary

Allowed: multiple technical repairs exist for one failure; they differ in
caller/callee responsibility, admissible input, and compatibility;
site-restriction excludes alternatives; post-hoc audit reuses one candidate set
across contract judgments; soundness/exactness are checked **relative to the
declared artifact-defined contract**.

Not claimed: best repair auto-decided; existing Dafny repair research is wrong;
post-hoc audit always beats site restriction; generalization to all
specification-model repair; frequency in practice from one case; verifier
success equals specification-intent correctness; any Lean/semantic theorem.

## 14. Reproduction

```bash
python scripts/reproduce.py                 # version -> generate -> verify -> audit -> schema -> tests -> manifest
python -m pytest -q
git diff --check
```

Override the Dafny binary with `--dafny PATH` or `DAFNY_EXE`. A version other
than 4.11.0 is recorded as a mismatch in metadata and **not** silently treated
as identical. Pinned version:
`4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2`.

## 15. Artifact manifest

```text
m3/
  README.md
  base.dfy  C1_caller_strengthen.dfy  C2_callee_weaken.dfy  C3_impl_change.dfy   (+ .csv)
  model/    reportability_contract.json   contract_reference.json
  templates/program_template.dfy
  generated/local/   8 impl + 4 contract variants (.dfy, .log)
  generated/closed/  8 impl + 4 contract variants (.dfy, .log)
  results/  lattice_measurements.json
            implementation_residuals_{local,closed}.json
            contract_residuals_{local,closed}.json
            reportability_audit_{local,closed}.json
            candidate_attribute_validity.json
            summary.md   manifest.sha256.json
scripts/  m3lib.py  generate_dafny_variants.py  run_dafny_lattice.py
          audit_reportability.py  reproduce.py
tests/    test_reportability_definitions.py
          test_expected_local_boundary.py  test_expected_closed_boundary.py
```

`m3/results/manifest.sha256.json` lists SHA-256 of every tracked artifact for
integrity checking.
