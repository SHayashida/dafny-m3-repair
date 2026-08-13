# M3 reportability-contract finite audit -- summary

Dafny version measured: `4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2` (match=True)

RepairAtomicity (|beta(a)|=1 for all a): **False** (false => this is an M3-B, non-atomic reporting contract; site-restricted generation is a separate experiment).


## Scope: local

| predicate | result |
|---|---|
| RawRepair | {KEEP_PERCENT_POSITIVE_PRECONDITION} ; {KEEP_DIRECT_PERCENT_CALL} ; {KEEP_TREND_NONZERO_DOMAIN} |
| GroupedRepair | {ORIGINAL_PUBLIC_CONTRACT_SURFACE} ; {ORIGINAL_IMPLEMENTATION_BEHAVIOR} |
| ContractRepair | {ORIGINAL_PUBLIC_CONTRACT_SURFACE} ; {ORIGINAL_IMPLEMENTATION_BEHAVIOR} |
| ResidualFaithfulness | True |
| GroupSoundness | True |
| PsiDeletionMonotonicity | True |
| GroupedCorrectness (exactness) | True |
| M3-C applicable | True |

## Scope: closed_world

| predicate | result |
|---|---|
| RawRepair | {KEEP_PERCENT_POSITIVE_PRECONDITION} ; {KEEP_DIRECT_PERCENT_CALL} |
| GroupedRepair | {ORIGINAL_PUBLIC_CONTRACT_SURFACE} ; {ORIGINAL_IMPLEMENTATION_BEHAVIOR} |
| ContractRepair | {ORIGINAL_IMPLEMENTATION_BEHAVIOR} |
| ResidualFaithfulness | True |
| GroupSoundness | False |
| PsiDeletionMonotonicity | False |
| GroupedCorrectness (exactness) | False |
| M3-C applicable | False |

GroupSoundness counterexamples:
- deleted levers ['KEEP_PERCENT_POSITIVE_PRECONDITION']: SatPhi(retained)=True but SatPsi(I\groupTouchAny)=False (groupTouchAny=['ORIGINAL_PUBLIC_CONTRACT_SURFACE'])
- deleted levers ['KEEP_PERCENT_POSITIVE_PRECONDITION', 'KEEP_DIRECT_PERCENT_CALL']: SatPhi(retained)=True but SatPsi(I\groupTouchAny)=False (groupTouchAny=['ORIGINAL_PUBLIC_CONTRACT_SURFACE', 'ORIGINAL_IMPLEMENTATION_BEHAVIOR'])

GroupedCorrectness counterexamples:
- G=['ORIGINAL_PUBLIC_CONTRACT_SURFACE']: GroupedRepair=True but ContractRepair=False

PsiDeletionMonotonicity counterexamples:
- SatPsi(['ORIGINAL_PUBLIC_CONTRACT_SURFACE'])=True but SatPsi([])=False (T' subseteq T)

## Application-side CandidateAttributeValidity (NOT GroupSoundness)

| id | validated_local | validated_closed_world | existing_clients_preserved | public_contract_changed | implementation_changed | rejection_reason |
|---|---|---|---|---|---|---|
| C1 | True | False | False | True | False | fails closed-world compatibility: existing nonzero-only upstream client (TrendUserNonzero) cannot prove the strengthened caller precondition span > 0 |
| C2 | True | True | True | True | False | - |
| C3 | True | True | True | False | True | - |
