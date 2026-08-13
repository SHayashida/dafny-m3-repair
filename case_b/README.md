# Dafny Case B: grouping versus inclusion-minimalization

Case B is a constructive finite witness design whose verifier outcomes are
measured rather than stipulated. It asks whether the source-derived touch-any
grouping `g` commutes with inclusion-minimalization on one frozen, exhaustively
verified repair family:

```text
g(Min(F))  ?=  Min(g(F))
```

Here `Lambda` is the three-lever universe, `R` always means
`deleted_levers`, and `retained_levers = Lambda \ R`. The measured family is
constructed only from raw results classified `VERIFIED`:

```text
F = { R subseteq Lambda | Verify(Lambda \ R) = VERIFIED }
```

## Separation from the authoritative M3 implementation

Case B does not redefine, change, or test an M3 theorem. The authoritative
finite M3 implementation is in `scripts/m3lib.py`, with definitions documented
in `m3/README.md`:

| M3 name | Authoritative Python symbol |
|---|---|
| `RawRepair` | `scripts/m3lib.py::raw_repairs` |
| `GroupedRepair` | `scripts/m3lib.py::grouped_repairs` |
| `ContractRepair` | `scripts/m3lib.py::contract_repairs` |
| `ResidualFaithfulness` | `scripts/m3lib.py::residual_faithfulness` |
| `GroupSoundness` | `scripts/m3lib.py::group_soundness` |
| `PsiDeletionMonotonicity` | `scripts/m3lib.py::psi_deletion_monotonicity` |
| inclusion-minimality helpers | `raw_repairs`, `contract_repairs`, and `grouped_repairs` in `scripts/m3lib.py` |

In particular, the Case B equality or inequality is not M3 GroupSoundness,
ResidualFaithfulness, exactness, or GroupedRepair.

## Frozen design

The fully retained canonical source is `canonical/case_b.dfy`. Its postcondition
requires a nonnegative result although the input is unrestricted and the body
returns the input unchanged. The design was frozen before the first Dafny
measurement in `design/case_b_design_lock.json`.

| Lever | Retained semantics | Semantics when deleted | Dafny construct | Source-derived group |
|---|---|---|---|---|
| `L1_REQUIRE_NONNEGATIVE` | accept every integer | add `requires x >= 0` | caller/public input obligation | `INPUT_CONTRACT` |
| `L2_REQUIRE_AT_LEAST_MINUS_ONE` | no lower bound | add `requires x >= -1` | caller/public input obligation | `INPUT_CONTRACT` |
| `L3_SHIFT_BODY_BY_ONE` | assign `y := x` | assign `y := x + 1` | implementation body | `IMPLEMENTATION_BODY` |

The first two levers share a group because both edit the public input domain of
the same method. The third changes executable implementation behavior. These
assignments are carried by strict `CASE_B_METADATA` JSON comments in the
canonical source. The parser rejects missing, duplicate, conflicting, unknown,
or incomplete records. The normalized mapping and its hash are frozen before
generation; generated variants copy the binding and do not reinterpret the
metadata.

The preregistered hypothesis is non-commutativity. Equality is also a valid
result and must be preserved; the source, levers, semantics, and grouping must
not be tuned in response to measurements.

## Measurement and operators

All eight deletion subsets are materialized under `generated/variants/` and
each receives its own `dafny verify` process. Each raw JSON records command,
executable path, version, exit code, stdout, stderr, elapsed time, source hash,
design/group bindings, and one of:

- `VERIFIED`: well-formed and every requested obligation discharged;
- `VERIFICATION_FAILED`: the verifier evaluated the program but could not prove
  at least one obligation;
- `FRONTEND_ERROR`: parsing, resolution, typing, or option handling prevented
  the intended verification problem;
- `TIMEOUT`: the frozen 120-second invocation timeout elapsed;
- `TOOL_ERROR`: another executable, process, or environment failure occurred.

A complete scientific result requires eight outcomes split only between
`VERIFIED` and `VERIFICATION_FAILED`. Any other outcome invalidates completion.

`Min(X)` is computed from all proper-subset relations, not minimum cardinality.
The implementation separately computes `F`, `Min(F)`, `g(F)`, `g(Min(F))`, and
`Min(g(F))`; notably, `Min(g(F))` starts from the full grouped image.

For every finite family under a touch-any map, monotonicity implies:

```text
Min(g(F)) subseteq g(Min(F)).
```

The pipeline treats a reverse difference as corruption, never as an empirical
finding. A legitimate difference must be an element of
`g(Min(F)) \ Min(g(F))`, saved with a concrete smaller group image and raw
variants witnessing domination.

The singleton mapping gives every lever a unique group and is an
**implementation sanity control / order-isomorphism control**, not an empirical
positive control. It must satisfy
`g_id(Min(F)) = Min(g_id(F))` or the main evidence is rejected.

## Reproduction

Use Dafny 4.11.0 (the exact observed version and any mismatch are recorded):

```bash
python3 case_b/scripts/reproduce_case_b.py --dafny /path/to/dafny
```

The command verifies the design lock, validates metadata, generates all eight
variants, invokes Dafny eight times, classifies outcomes, constructs the family,
computes both operator paths, checks structural and singleton controls, performs
an independent raw-evidence recomputation, runs fault injections, and runs the
complete existing and Case B pytest suite.

Direct checks:

```bash
python3 case_b/scripts/design_lock.py
python3 case_b/scripts/independent_audit.py
python3 case_b/scripts/fault_injections.py
python3 -m pytest -q
```

## Interpretation and claim boundary

The deliberately designed repair interface is distinct from the measured
family `F`; the source-derived grouping is distinct from both; and raw
inclusion-minimal repairs are distinct from inclusion-minimal elements of the
full grouped image.

If strict non-commutativity is measured, its direct interpretation is:

> Touch-any grouping preserves inclusion but may collapse distinct low-level
> repair sets into a coarser quotient order. Consequently, a repair that is
> inclusion-minimal before grouping can cease to be inclusion-minimal after the
> complete feasible family is projected into the grouped domain.

The strongest permitted direct claim is:

> For this frozen Dafny program, exhaustively measured repair family, and
> declared source-metadata touch-any grouping, grouping the raw
> inclusion-minimal repairs produced a strict superset of the
> inclusion-minimal elements obtained after grouping the full verified family.

If equality is measured, the result instead is that grouping and
inclusion-minimalization were observed to commute for this frozen instance.

Case B alone makes no claim about M3 GroupSoundness, ResidualFaithfulness, M3
exactness, organizational correctness, prevalence in real projects, arbitrary
repair abstractions, pre-atomicization superiority, or semantic correctness
beyond the declared Dafny artifact. Pre-atomicization may avoid some post-hoc
grouping problems when its interface is fixed and lossless; fine-grained
candidates may permit later regrouping and audit; Case B establishes only the
measured operator-order result here.

> Source-derived grouping establishes reproducible provenance of the declared
> grouping, not empirical validity of that grouping as an actual organizational
> reporting workflow.
