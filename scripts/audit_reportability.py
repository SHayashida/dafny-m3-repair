"""
audit_reportability.py

Consume the measured Dafny lattice (results/lattice_measurements.json), build the
per-scope SatPhi / SatPsi tables strictly from measurement, and machine-decide
the authoritative M3 (Sen24) reportability-contract predicates:

  RawRepair, GroupedRepair, ContractRepair,
  ResidualFaithfulness, GroupSoundness,
  PsiDeletionMonotonicity, GroupedCorrectness (pointwise / contract-relative
  exactness), and M3-C characterization applicability.

Separately (and clearly NOT M3 GroupSoundness), emit the application-side
CandidateAttributeValidity audit for the single-candidate edits C1/C2/C3.

No verification outcome is hardcoded; every SatPhi/SatPsi value comes from the
measurement table produced by run_dafny_lattice.py.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m3lib as m3

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "m3" / "results"
SCHEMA_VERSION = "m3-audit-1.0"

SCOPES = ["local", "closed_world"]


def load_measurements():
    data = json.loads((RESULTS / "lattice_measurements.json").read_text("utf-8"))
    return data


def build_sat_tables(data):
    """Return sat_phi[scope], sat_psi[scope], and residual detail rows."""
    sat_phi = {s: {} for s in SCOPES}
    sat_psi = {s: {} for s in SCOPES}
    impl_rows = {s: [] for s in SCOPES}
    contract_rows = {s: [] for s in SCOPES}
    for m in data["measurements"]:
        scope = m["scope"]
        if m["kind"] == "impl":
            k = frozenset(m["retained_levers"])
            sat_phi[scope][k] = m["verifier_passed"]
            impl_rows[scope].append(m)
        else:
            t = frozenset(m["retained_atoms"])
            sat_psi[scope][t] = m["verifier_passed"]
            contract_rows[scope].append(m)
    # completeness check: all 8 lever sets and 4 atom sets present per scope
    for s in SCOPES:
        assert len(sat_phi[s]) == 8, f"{s}: expected 8 impl residuals, got {len(sat_phi[s])}"
        assert len(sat_psi[s]) == 4, f"{s}: expected 4 contract residuals, got {len(sat_psi[s])}"
    return sat_phi, sat_psi, impl_rows, contract_rows


def as_atom_lists(sets):
    return [m3.sorted_atoms(s) for s in sets]


def as_lever_lists(sets):
    return [m3.sorted_levers(s) for s in sets]


def audit_scope(scope, sat_phi, sat_psi, data):
    sp, ps = sat_phi[scope], sat_psi[scope]

    raw = m3.raw_repairs(sp)
    grouped = m3.grouped_repairs(sp)
    contract = m3.contract_repairs(ps)
    raw_img = m3.raw_grouped_image(sp)

    rf_ok, rf_checked, rf_cex = m3.residual_faithfulness(sp, ps)
    gs_ok, gs_checked, gs_cex = m3.group_soundness(sp, ps)
    pm_ok, pm_checked, pm_cex = m3.psi_deletion_monotonicity(ps)
    gc_ok, gc_checked, gc_cex = m3.grouped_correctness(sp, ps)

    bd = m3.blocks_disjoint()
    m3c = m3.m3c_applicable(bd, rf_ok, pm_ok)

    audit = {
        "schema_version": SCHEMA_VERSION,
        "dafny_version": data["dafny_version"],
        "dafny_version_match": data["dafny_version_match"],
        "scope": scope,
        "active_contract_atoms": m3.sorted_atoms(m3.I),
        "active_implementation_levers": m3.sorted_levers(m3.LAMBDA_I),
        "beta": {m3.ATOM_CODE[a]: m3.sorted_levers(m3.BETA[a]) for a in m3.I},
        "blocks_disjoint": bd,
        "blocks_nonempty": m3.blocks_nonempty(),
        "repair_atomicity": m3.repair_atomicity(),
        "sat_phi": {m3.code_for_levers(k): sp[k] for k in m3.powerset(m3.LAMBDA_I)},
        "sat_psi": {m3.code_for_atoms(t): ps[t] for t in m3.powerset(m3.I)},
        "raw_repairs": as_lever_lists(raw),
        "raw_grouped_image": as_atom_lists(raw_img),
        "grouped_repairs": as_atom_lists(grouped),
        "contract_repairs": as_atom_lists(contract),
        "residual_faithfulness": {
            "result": rf_ok, "checked_cases": rf_checked, "counterexamples": rf_cex},
        "group_soundness": {
            "result": gs_ok, "checked_cases": gs_checked, "counterexamples": gs_cex},
        "psi_deletion_monotonicity": {
            "result": pm_ok, "checked_cases": pm_checked, "counterexamples": pm_cex},
        "grouped_correctness": {
            "result": gc_ok, "checked_cases": gc_checked, "counterexamples": gc_cex},
        "m3c_characterization": {
            "applicable": m3c,
            "assumptions": {
                "blocks_disjoint": bd,
                "residual_faithfulness": rf_ok,
                "psi_deletion_monotonicity": pm_ok,
            },
            "finite_result": (gs_ok == gc_ok) if m3c else None,
            "note": ("This finite artifact is consistent with the M3-C "
                     "characterization under the declared artifact-defined "
                     "contract and verified finite assumptions."
                     if m3c else
                     "M3-C characterization NOT APPLICABLE: a declared finite "
                     "assumption failed; GroupSoundness and GroupedCorrectness "
                     "results are reported as independent measured facts, not as "
                     "a proof of the iff."),
        },
    }
    return audit


def candidate_attribute_audit(sat_phi):
    """Application-side CandidateAttributeValidity audit for single edits C1/C2/C3.

    THIS IS NOT M3 GroupSoundness. It records the factual attributes of each
    candidate (input-domain change, public-contract change, implementation
    change, existing-client preservation, responsibility location) and separates
    'validated' from 'adopted'.
    """
    # single-lever deletions -> single candidate edits
    cands = [
        {
            "candidate_id": "C1",
            "edit": "Trend.requires span != 0 => span > 0",
            "deleted_lever": m3.LEVER_CODE[m3.T],
            "input_domain_change": "caller admissible input narrowed ({!=0} -> {>0})",
            "public_contract_changed": True,
            "implementation_changed": False,
            "responsibility_moved_to": "caller / upstream clients",
        },
        {
            "candidate_id": "C2",
            "edit": "Percent.requires whole > 0 => whole != 0",
            "deleted_lever": m3.LEVER_CODE[m3.P],
            "input_domain_change": "callee admissible input expanded ({>0} -> {!=0})",
            "public_contract_changed": True,
            "implementation_changed": False,
            "responsibility_moved_to": "callee",
        },
        {
            "candidate_id": "C3",
            "edit": "Trend body direct call => guarded implementation",
            "deleted_lever": m3.LEVER_CODE[m3.D],
            "input_domain_change": "public admissible input unchanged; runtime behavior changes for span<0",
            "public_contract_changed": False,
            "implementation_changed": True,
            "responsibility_moved_to": "implementation (no contract-level move)",
        },
    ]
    lever_of = {"C1": m3.T, "C2": m3.P, "C3": m3.D}
    for c in cands:
        lever = lever_of[c["candidate_id"]]
        k = m3.LAMBDA_I - frozenset({lever})  # retained after single deletion
        c["validated_local"] = sat_phi["local"][k]
        c["validated_closed_world"] = sat_phi["closed_world"][k]
        c["existing_clients_preserved"] = sat_phi["closed_world"][k]
        c["adopted"] = None  # human decision, deliberately not auto-set
        c["rejection_reason"] = (
            None if c["validated_closed_world"]
            else "fails closed-world compatibility: existing nonzero-only "
                 "upstream client (TrendUserNonzero) cannot prove the "
                 "strengthened caller precondition span > 0")
    return {
        "schema_version": SCHEMA_VERSION,
        "audit_name": "CandidateAttributeValidity",
        "disclaimer": ("CandidateAttributeValidity is an application-side "
                       "attribute-factuality audit. It is NOT M3 GroupSoundness "
                       "and must not be presented as such."),
        "candidates": cands,
    }


def residual_tables(impl_rows, contract_rows):
    """Materialize implementation_residuals / contract_residuals per scope."""
    out = {}
    for scope in SCOPES:
        out[("impl", scope)] = {
            "scope": scope,
            "kind": "implementation_residuals",
            "rows": [
                {
                    "retained_levers": r["retained_levers"],
                    "applied_edits": [m3.LEVER_EDIT[lv].split("_")[0]
                                      for lv in m3.sorted_levers(m3.LAMBDA_I)
                                      if lv not in frozenset(r["retained_levers"])] or ["base"],
                    "source": r["source"],
                    "verifier_command": r["verifier_command"],
                    "verifier_passed": r["verifier_passed"],
                    "source_sha256": r["source_sha256"],
                    "log_sha256": r["log_sha256"],
                }
                for r in sorted(impl_rows[scope], key=lambda x: x["source"])
            ],
        }
        out[("contract", scope)] = {
            "scope": scope,
            "kind": "contract_residuals",
            "rows": [
                {
                    "retained_contract_atoms": r["retained_atoms"],
                    "block_aligned_lever_set": r["retained_levers"],
                    "source": r["source"],
                    "verifier_command": r["verifier_command"],
                    "verifier_passed": r["verifier_passed"],
                    "source_sha256": r["source_sha256"],
                    "log_sha256": r["log_sha256"],
                }
                for r in sorted(contract_rows[scope], key=lambda x: x["source"])
            ],
        }
    return out


def write_summary(audits, cand):
    def fmt_sets(sets):
        return " ; ".join("{" + ", ".join(m3.ATOM_CODE.get(a, a) if a in m3.ATOM_CODE
                          else a for a in s) + "}" for s in sets) or "(none)"

    lines = []
    lines.append("# M3 reportability-contract finite audit -- summary\n")
    lines.append(f"Dafny version measured: `{audits['local']['dafny_version']}` "
                 f"(match={audits['local']['dafny_version_match']})\n")
    lines.append("RepairAtomicity (|beta(a)|=1 for all a): "
                 f"**{audits['local']['repair_atomicity']}** "
                 "(false => this is an M3-B, non-atomic reporting contract; "
                 "site-restricted generation is a separate experiment).\n")
    for scope in SCOPES:
        a = audits[scope]
        lines.append(f"\n## Scope: {scope}\n")
        lines.append("| predicate | result |")
        lines.append("|---|---|")
        lines.append(f"| RawRepair | {' ; '.join('{'+', '.join(x)+'}' for x in a['raw_repairs'])} |")
        lines.append(f"| GroupedRepair | {' ; '.join('{'+', '.join(x)+'}' for x in a['grouped_repairs'])} |")
        lines.append(f"| ContractRepair | {' ; '.join('{'+', '.join(x)+'}' for x in a['contract_repairs'])} |")
        lines.append(f"| ResidualFaithfulness | {a['residual_faithfulness']['result']} |")
        lines.append(f"| GroupSoundness | {a['group_soundness']['result']} |")
        lines.append(f"| PsiDeletionMonotonicity | {a['psi_deletion_monotonicity']['result']} |")
        lines.append(f"| GroupedCorrectness (exactness) | {a['grouped_correctness']['result']} |")
        lines.append(f"| M3-C applicable | {a['m3c_characterization']['applicable']} |")
        if a["group_soundness"]["counterexamples"]:
            lines.append("\nGroupSoundness counterexamples:")
            for c in a["group_soundness"]["counterexamples"]:
                lines.append(f"- deleted levers {c['deleted_levers']}: "
                             f"SatPhi(retained)={c['sat_phi_retained']} but "
                             f"SatPsi(I\\groupTouchAny)={c['sat_psi_retained']} "
                             f"(groupTouchAny={c['group_touch_any']})")
        if a["grouped_correctness"]["counterexamples"]:
            lines.append("\nGroupedCorrectness counterexamples:")
            for c in a["grouped_correctness"]["counterexamples"]:
                lines.append(f"- G={c['G']}: GroupedRepair={c['grouped_repair']} "
                             f"but ContractRepair={c['contract_repair']}")
        if a["psi_deletion_monotonicity"]["counterexamples"]:
            lines.append("\nPsiDeletionMonotonicity counterexamples:")
            for c in a["psi_deletion_monotonicity"]["counterexamples"]:
                lines.append(f"- SatPsi({c['retained_T']})={c['sat_psi_T']} but "
                             f"SatPsi({c['retained_Tprime']})={c['sat_psi_Tprime']} "
                             f"(T' subseteq T)")
    lines.append("\n## Application-side CandidateAttributeValidity (NOT GroupSoundness)\n")
    lines.append("| id | validated_local | validated_closed_world | "
                 "existing_clients_preserved | public_contract_changed | "
                 "implementation_changed | rejection_reason |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in cand["candidates"]:
        lines.append(f"| {c['candidate_id']} | {c['validated_local']} | "
                     f"{c['validated_closed_world']} | "
                     f"{c['existing_clients_preserved']} | "
                     f"{c['public_contract_changed']} | "
                     f"{c['implementation_changed']} | "
                     f"{c['rejection_reason'] or '-'} |")
    (RESULTS / "summary.md").write_text("\n".join(lines) + "\n",
                                        encoding="utf-8", newline="\n")


def main():
    data = load_measurements()
    sat_phi, sat_psi, impl_rows, contract_rows = build_sat_tables(data)

    audits = {}
    for scope in SCOPES:
        audit = audit_scope(scope, sat_phi, sat_psi, data)
        audits[scope] = audit
        suffix = "local" if scope == "local" else "closed"
        (RESULTS / f"reportability_audit_{suffix}.json").write_text(
            json.dumps(audit, indent=2), encoding="utf-8", newline="\n")

    tables = residual_tables(impl_rows, contract_rows)
    for scope in SCOPES:
        suffix = "local" if scope == "local" else "closed"
        (RESULTS / f"implementation_residuals_{suffix}.json").write_text(
            json.dumps(tables[("impl", scope)], indent=2), encoding="utf-8", newline="\n")
        (RESULTS / f"contract_residuals_{suffix}.json").write_text(
            json.dumps(tables[("contract", scope)], indent=2), encoding="utf-8", newline="\n")

    cand = candidate_attribute_audit(sat_phi)
    (RESULTS / "candidate_attribute_validity.json").write_text(
        json.dumps(cand, indent=2), encoding="utf-8", newline="\n")

    write_summary(audits, cand)
    print("audit complete; wrote reportability_audit_*, *_residuals_*, "
          "candidate_attribute_validity.json, summary.md")

    # console recap
    for scope in SCOPES:
        a = audits[scope]
        print(f"\n[{scope}]")
        print("  RawRepair       :", a["raw_repairs"])
        print("  GroupedRepair   :", a["grouped_repairs"])
        print("  ContractRepair  :", a["contract_repairs"])
        print("  ResidualFaithful:", a["residual_faithfulness"]["result"])
        print("  GroupSoundness  :", a["group_soundness"]["result"])
        print("  PsiDeletionMono :", a["psi_deletion_monotonicity"]["result"])
        print("  GroupedCorrect  :", a["grouped_correctness"]["result"])
        print("  M3-C applicable :", a["m3c_characterization"]["applicable"])


if __name__ == "__main__":
    main()
