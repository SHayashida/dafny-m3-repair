# Protocol-bounded real Dafny workflow case 01

## Result

```text
REAL_DAFNY_CASE = FOUND
GRADE = GOLD
EVIDENCE_LEVEL = R2
E1 = PASS
E2 = PASS
E3 = PASS
OBSERVATION_INFERENCE_SEPARATION = PASS
SOURCE_PROVENANCE = PASS
SEARCH_PROTOCOL_COMPLETED = PASS
NEW_REAL_CASE_DAFNY_EXPERIMENTS = 0
NEW_LEAN_FORMALIZATION = 0
```

The selected case is [`dafny-lang/libraries` PR #99](https://github.com/dafny-lang/libraries/pull/99), linked from [`dafny-lang/dafny` PR #3609](https://github.com/dafny-lang/dafny/pull/3609). It records a standard-library frame repair in which contract restrictions, a broad frame, and an API-fork alternative were compared before an exact frame expression was adopted. Public review explicitly discusses breaking consumers, upgrade work, specification precision, and backward compatibility.

The evidence level is **R2**, not R3. The history directly records multiple repair directions, but it does not directly show that two distinct directions each passed Dafny verification.

## Search protocol and execution

The protocol was frozen before candidate evaluation at [`real_case_search_protocol.json`](real_case_search_protocol.json), SHA-256 `2ef3b43143a49aab678c100a09083a02579c44489acc81f607390d69d0ad3d7c`.

- Search date: 2026-08-13
- Scopes: `dafny-lang/dafny`, `dafny-lang/libraries`, and global public GitHub issue/PR search with the term `Dafny`
- Query families: verification failure with requires; verification failure with ensures; could-not-prove with requires; could-not-prove with ensures; contract change with verification; precondition with compatibility/breaking; postcondition with compatibility/API; wrapper/adapter with verification; caller/callee; requires with workaround; verification with public API; verification with backward compatibility
- Ordering: GitHub best match
- Cap: first five unique potentially relevant records per family and scope, scanning at most the first 20 API records
- Query definitions completed: 36 of 36
- API `total_count` occurrence sum: 743
- API records returned within the frozen top-20 windows: 341 occurrences
- Globally unique records inspected after screening and duplicate handling: 102
- Serious candidates: 2
- Grades: 1 GOLD, 0 SILVER, 1 REJECT

The first transport attempt reached GitHub's search rate limit after 30 query definitions and before persisting item checkpoints. After the published reset, the same frozen 36 queries were replayed with throttling and per-query checkpoints. No scope, query, ordering, cap, screen, threshold, rubric, or stopping rule changed. The complete replay supplies the counts above. The exact queries, inspected identities, and serious-candidate records are in [`search_ledger.json`](search_ledger.json).

## 1. Identification

| Item | Public record |
| --- | --- |
| Primary repository | `dafny-lang/libraries` |
| Primary PR | [#99, “fix: Change reads clause of filter to *”](https://github.com/dafny-lang/libraries/pull/99) |
| Primary PR dates | Created 2023-02-22; merged 2023-02-22 |
| Primary author | `RustanLeino` |
| Initial repair commit | [`9b39ed930b8074d98fb1493a160925c4a5cbad8a`](https://github.com/dafny-lang/libraries/commit/9b39ed930b8074d98fb1493a160925c4a5cbad8a) |
| Exact-frame commit | [`807e02d0c5125c76f99522a64a800733353936e9`](https://github.com/dafny-lang/libraries/commit/807e02d0c5125c76f99522a64a800733353936e9) |
| Final head | [`773971747ec76cd2f224000e2d42d6fd785e8f40`](https://github.com/dafny-lang/libraries/commit/773971747ec76cd2f224000e2d42d6fd785e8f40) |
| Merge commit | [`20d90ec43db21d224bb5db0020cc68a2d441143c`](https://github.com/dafny-lang/libraries/commit/20d90ec43db21d224bb5db0020cc68a2d441143c) |
| Source file | [`src/Collections/Sequences/Seq.dfy` at the final head](https://github.com/dafny-lang/libraries/blob/773971747ec76cd2f224000e2d42d6fd785e8f40/src%2FCollections%2FSequences%2FSeq.dfy) |
| Related Dafny change | [`dafny-lang/dafny` PR #3609](https://github.com/dafny-lang/dafny/pull/3609), merged as [`0ef55d2ce872036c9a84793d151aec653e07bde5`](https://github.com/dafny-lang/dafny/commit/0ef55d2ce872036c9a84793d151aec653e07bde5) |

Relevant review records are [review 1308549359](https://github.com/dafny-lang/libraries/pull/99#pullrequestreview-1308549359), [author update 1440811631](https://github.com/dafny-lang/libraries/pull/99#issuecomment-1440811631), and [compatibility follow-up 1440851004](https://github.com/dafny-lang/libraries/pull/99#issuecomment-1440851004).

## 2. Initial verification problem — E1

**E1 = PASS.**

Dafny PR #3609 corrected allocation-state handling and the resolver's acceptance of function expressions in `reads` clauses. Its public description explicitly links libraries PR #99 as a necessary standard-library change. Libraries PR #99 explains that `Seq.Filter` used `f.reads` in a way whose desugared set could depend on allocation state and that the change was needed to keep the libraries verifying under the corrected check.

This establishes an actual verification-acceptance problem in public Dafny history. It does not establish that every prior semantic use of `Filter` was wrong.

## 3. Repair directions — E2

**E2 = PASS.** Two taxonomy classes are directly evidenced.

| Direction | Repair class | Publicly evidenced statuses | Evidence |
| --- | --- | --- | --- |
| Restrict the function arrow, restrict `T` to `T(!new)`, use `reads *`, or use an exact index-bounded frame set | `CALLEE_SPEC` | `DISCUSSED`, `PROPOSED`, `IMPLEMENTED`, `ADOPTED` | [PR body](https://github.com/dafny-lang/libraries/pull/99), [author update](https://github.com/dafny-lang/libraries/pull/99#issuecomment-1440811631), [exact-frame commit](https://github.com/dafny-lang/libraries/commit/807e02d0c5125c76f99522a64a800733353936e9), [merge](https://github.com/dafny-lang/libraries/commit/20d90ec43db21d224bb5db0020cc68a2d441143c) |
| Provide more than one `Filter` function, each accommodating a different contract choice | `IMPLEMENTATION_OR_ADAPTER` | `DISCUSSED`, `PROPOSED` | [PR body](https://github.com/dafny-lang/libraries/pull/99), [review](https://github.com/dafny-lang/libraries/pull/99#pullrequestreview-1308549359) |

The multiple-`Filter` proposal is classified as implementation/adapter work because it would add separate public entry points to accommodate distinct contracts. The other directions change the exposed callee specification or type boundary. No `CALLER_SIDE` direction is directly evidenced, and none is claimed.

Neither row receives `VERIFIER_CONFIRMED`. The adopted row is merged, but the public history does not contain a direct verifier record for that exact library alternative. The API-fork direction was not publicly implemented or verifier-tested.

## 4. Final adopted repair

The first patch used `reads *`. After review, the author replaced that broad frame with an exact set of objects read by `f` for indices in `xs`, explaining that the formulation avoided the listed drawbacks. Commit `807e02d0c5125c76f99522a64a800733353936e9` implements the improved frame; the final state was merged in `20d90ec43db21d224bb5db0020cc68a2d441143c`.

The adopted direction is `CALLEE_SPEC` with statuses `IMPLEMENTED` and `ADOPTED`. It is not marked `VERIFIER_CONFIRMED` under the task's strict definition.

## 5. Specification/API decision — E3

**E3 = PASS.**

The public record makes the non-verification criteria explicit:

- The four approaches differ in which functions and sequence element types callers may use, and in the strength of the frame axiom.
- A reviewer calls the interim choice a tradeoff and warns that broadening the frame could break consumer verification that relied on the tighter contract.
- The same review contrasts accepting upgrade work now with potentially forking the API in the future to avoid unbounded consumer migration cost.
- After the exact frame was adopted, backward compatibility remained an explicit review concern rather than an inferred concern supplied by this report.

The final choice therefore cannot be reduced to “which text satisfies the corrected resolver?” The discussion also considered public contract precision, accepted inputs, downstream proof behavior, and consumer upgrade cost.

## 6. Evidence level

```text
EVIDENCE_LEVEL = R2
```

E1, E2, and explicit E3 pass. R3 is not allowed because the history does not directly show that at least two distinct repair directions each passed Dafny verification.

## 7. Analytical interpretation (not source terminology)

Allowed claim:

> This public workflow records multiple repair directions across different specification and API-implementation boundaries being considered in response to a Dafny verification problem, while the adopted choice was constrained by compatibility and specification considerations beyond verifier success alone.

Not allowed: multiple verifier-valid repairs existed; the case establishes prevalence; the case validates organizational report groups; or the case proves any M3 soundness, exactness, necessity, or transfer result.

## 8. Observation/inference separation

| OBSERVED_SOURCE_FACT | OUR_INTERPRETATION | CLAIM_ALLOWED | CLAIM_NOT_ALLOWED |
| --- | --- | --- | --- |
| Dafny PR #3609 links libraries PR #99 as a necessary standard-library change and says the corrected resolver rejects some functions in `reads` clauses. | The library PR responds to a concrete verification-acceptance change rather than a hypothetical redesign. | A real Dafny verification problem initiated the library repair. | The original `Filter` contract was semantically invalid in every Dafny version. |
| PR #99 lists four fixes: restrict the function arrow, restrict `T`, broaden `reads` to `*`, or provide multiple `Filter` functions. | The history directly crosses a callee-specification boundary and an implementation/API-adapter boundary. | At least two repair classes were publicly considered. | Every listed alternative was implemented or verified. |
| A reviewer warns of consumer breakage and upgrade cost; the author later adopts an exact frame described as avoiding the listed drawbacks. | Compatibility and specification precision constrained selection independently of verifier acceptance. | The choice involved explicit API/specification judgment beyond verifier success. | Backward compatibility was mechanically proved. |
| No public record directly demonstrates that two distinct alternatives each passed Dafny verification. | The case supports R2 but not R3. | Multiple repair directions were considered. | Multiple verifier-valid repair directions existed. |

## 9. Source provenance and snapshot binding

The structured record [`dafny_real_case_01.json`](dafny_real_case_01.json) stores retrieval time, stable source and comment identifiers, authors, dates, normalized structured paraphrases, and SHA-256 values. Each hash is computed over the exact UTF-8 `normalized_text` value without a trailing newline.

| Key | Source | Stable identifier | Content SHA-256 |
| --- | --- | --- | --- |
| SRC-001 | [Dafny PR #3609](https://github.com/dafny-lang/dafny/pull/3609) | `pull_request:3609` | `bbe55fb9e3702405bd159d00f1ea5b1b82a548c2c5b2831ceb21d41ef4292ea5` |
| SRC-002 | [Libraries PR #99](https://github.com/dafny-lang/libraries/pull/99) | `pull_request:99` | `99d0365c423f5d0ed196340eb236f0e11ae30e354c16ab89f6957869b7211126` |
| SRC-003 | [Review](https://github.com/dafny-lang/libraries/pull/99#pullrequestreview-1308549359) | `pull_request_review:1308549359` | `ea5aead69a8986754865e8d3d7b5c867f04d1b4d0aa5b827f72583555e7cf731` |
| SRC-004 | [Author update](https://github.com/dafny-lang/libraries/pull/99#issuecomment-1440811631) | `issue_comment:1440811631` | `e97ebc175f3d62f88b46c6a0c216160a29fb2752354ded72460dd57af5a1a309` |
| SRC-005 | [Compatibility follow-up](https://github.com/dafny-lang/libraries/pull/99#issuecomment-1440851004) | `issue_comment:1440851004` | `370b4dab2ade7dba5b19b09817964a6e7669fd4efe65d3483373bb7560c78afb` |
| SRC-006 | [Exact-frame commit](https://github.com/dafny-lang/libraries/commit/807e02d0c5125c76f99522a64a800733353936e9) | `commit:807e02d0c5125c76f99522a64a800733353936e9` | `6d999386edecbb86a4f603f690652379a98f39f2b2f7e9cee164563f1f4ea0cf` |
| SRC-007 | [Merge commit](https://github.com/dafny-lang/libraries/commit/20d90ec43db21d224bb5db0020cc68a2d441143c) | `commit:20d90ec43db21d224bb5db0020cc68a2d441143c` | `5f4ff225287d2e48e88b0b5436210ee2800a64bd9b1b1976356d1f5578f1b463` |

## 10. Serious rejected candidate

[`theronic/eacl` PR #101](https://github.com/theronic/eacl/pull/101) passed the serious-candidate threshold because it records real verification/CI findings and explicit assurance-boundary judgments. It is `REJECT`, not SILVER: it is a broad audit and multi-finding cutover, so repair directions belonging to different failures cannot be combined to satisfy E2 for one shared initial verification problem.

## 11. Limitations

- This is one selected public case and cannot support a prevalence estimate.
- Selection is protocol-bounded and subject to GitHub ranking and selection bias.
- Public issue/PR history may omit offline discussion.
- The history does not verifier-confirm two distinct alternatives.
- The source authors did not describe the workflow as reportability.
- No claim is made that their responsibility or API boundaries match our grouping abstractions.
- No claim is made that M3 was necessary for their workflow.
- The case is not used as evidence for any Candidate B manuscript claim in this task.
- No public case was reconstructed as a new Dafny experiment, benchmark, repair enumerator, or Lean formalization.
