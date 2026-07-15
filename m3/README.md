# M3 Contract Repair Research: Dafny Specification Change Study

## Research Problem

When Dafny verification fails due to contract mismatch between `caller` and `callee`, multiple technically valid repairs exist:
- **C1**: Strengthen caller's precondition (narrower input)
- **C2**: Weaken callee's precondition (broader input)
- **C3**: Change implementation (preserve contracts)

Each repair succeeds verification but implies different responsibility assignments, API compatibility, and specification semantics. The research hypothesis is:

**Pre-selecting a fixed repair scope (A-only or B-only) loses alternative repairs and may incur over-repair or re-solve cycles. Holding low-level candidates and post-auditing them against declared responsibilities enables reuse across multiple specification judgments.**

## Minimum Example

File: `base.dfy`

```dafny
method Percent(part: int, whole: int) returns (r: int)
  requires whole > 0              // Over-restrictive: implementation works for whole != 0
  ensures r == part * 100 / whole
{ r := part * 100 / whole; }

method Trend(delta: int, span: int) returns (r: int)
  requires span != 0              // Caller only guarantees non-zero
{ r := Percent(delta, span); }    // FAIL: Trend cannot prove whole > 0
```

**Verification result**: base.dfy fails at `Trend (correctness)` — precondition `whole > 0` not provable from `span != 0`.

## Three Repair Candidates

| File | Repair | Contracts Changed | Verification | Existing Clients | Semantics |
|---|---|---|---|---|---|
| `C1_caller_strengthen.dfy` | Strengthen `Trend.requires: span != 0 → span > 0` | Caller narrowed input | ✅ (but `TrendUserBROKEN` fails) | Obligation propagates upstream | Caller responsibility ↑ |
| `C2_callee_weaken.dfy` | Weaken `Percent.requires: whole > 0 → whole != 0` | Callee broadened input | ✅ (all 5 tasks pass) | Preserved (Ratio still passes) | Callee responsibility ↑ / backward compat |
| `C3_impl_change.dfy` | Guard `Trend.body` for `span < 0` | Implementation only | ✅ (all 5 tasks pass) | Unchanged contracts | Silent behavior change (`span < 0` → 0) |

## Verification Logs

All logs are in `.csv` format (Dafny `--log-format csv`), showing per-method results:

```
base.csv:          base state (1 failure)
C1_caller_strengthen.csv:   Trend passes; TrendUserBROKEN fails (chain propagation)
C2_callee_weaken.csv:       All 5 pass; backward compatible
C3_impl_change.csv:         All 5 pass; implementation sealed
```

## M3 Framework Elements (in this example)

**Implementation Levers** (low-level edits):
- `Percent.requires` token change from `>` to `!=`
- `Trend.requires` token change from `!=` to `>`
- `Trend.body` branch addition

**Contract Report Items** (high-level):
- callee admissible input expanded / responsibility increased
- caller admissible input narrowed / responsibility increased
- implementation behavior changed / public contracts preserved
- backward compatibility maintained / broken

**Raw Repairs**: {C1, C2, C3} — three mutually non-included minimal edits

**Reporting Contract ρ**: Maps each repair to its responsibility implications (e.g., C1 → caller resp ↑, C2 → callee resp ↑)

**Declared Predicates Q**: verifier success, no unwanted input shrinkage, existing clients preserved, minimal edit, responsibility not moved to forbidden party

**Soundness**: If low-level repair e succeeds verification, then ρ(e) satisfies all declared Q predicates.

**Exactness** (future work): Low-level minimal repairs under ρ = contract-level minimal repairs under Q (over-under correspondence, if any).

## Method Comparison: A-only vs B-only vs C post-audit

| Method | Exploration Set | C1 Found | C2 Found | C3 Found | Chain Failure | Re-solve |
|---|---|---|---|---|---|---|
| **A (caller-only)** | {caller.requires} | ✅ | ✗ (excluded) | ✗ (excluded) | Yes (1 case) | +1 |
| **B (callee-only)** | {callee.requires} | ✗ (excluded) | ✅ | ✗ (excluded) | No | 0 |
| **C (post-audit)** | {caller.*, callee.*, body} | ✅ | ✅ | ✅ | Detected | 0 |

## Declarations (§13)

### Verified This Session
- ✅ Base failure + C1/C2/C3 all succeed
- ✅ Different responsibility implications for each repair
- ✅ Different input-set changes (C1 narrows, C2 widens)
- ✅ Different compatibility (C1 breaks upstream; C2 preserves)
- ✅ Pre-fixing to A loses C2; to B loses C1

### Not Yet Verified (for future work)
- ⏳ Formal soundness/exactness under ρ and Q
- ⏳ Multiple case studies
- ⏳ Frequency in real Dafny codebases
- ⏳ Automatic repair candidate generation

### Cannot Claim (§11)
- ❌ Best repair was auto-decided
- ❌ Existing Dafny tools are wrong
- ❌ Post-audit always beats pre-fixing
- ❌ General claim beyond this case

## Artifacts

- `base.dfy` — original failing spec (v0)
- `C1_caller_strengthen.dfy` — repair candidate 1
- `C2_callee_weaken.dfy` — repair candidate 2
- `C3_impl_change.dfy` — repair candidate 3
- `*.csv` — Dafny verifier output (per-method results)
- `README.md` — this file

## Reproduction

```bash
dafny verify base.dfy --log-format "csv;LogFileName=base.csv"
dafny verify C1_caller_strengthen.dfy --log-format "csv;LogFileName=C1_caller_strengthen.csv"
dafny verify C2_callee_weaken.dfy --log-format "csv;LogFileName=C2_callee_weaken.csv"
dafny verify C3_impl_change.dfy --log-format "csv;LogFileName=C3_impl_change.csv"
```

**Dafny version**: 4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2 (official release)

## References

- Hypothesis based on M3 contract repair framework (declared predicates, reporting contracts, soundness, exactness)
- Complements earlier `Divide` experiment (fan-out scaling, re-solve counts)
- Follows §12 priority: hand-constructed case before automated generation
