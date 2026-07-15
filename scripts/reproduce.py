"""
reproduce.py -- single reproduction entry point.

Steps:
  1. resolve + record Dafny version (mismatch is recorded, never silently ignored)
  2. generate all source variants
  3. verify local 8 + closed 8 implementation residuals
  4. verify local 4 + closed 4 contract residuals   (done together in step 2/3)
  5. run the reportability audit (M3 predicates from measurement)
  6. validate audit JSON against the required schema keys
  7. run pytest
  8. emit a hash manifest of every artifact

Usage:
  python scripts/reproduce.py [--dafny PATH] [--skip-tests]

Dafny path may also be supplied via the DAFNY_EXE environment variable.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import generate_dafny_variants  # noqa: E402
import run_dafny_lattice  # noqa: E402
import audit_reportability  # noqa: E402

RESULTS = ROOT / "m3" / "results"

REQUIRED_AUDIT_KEYS = [
    "schema_version", "dafny_version", "scope", "active_contract_atoms",
    "active_implementation_levers", "beta", "blocks_disjoint", "blocks_nonempty",
    "repair_atomicity", "raw_repairs", "raw_grouped_image", "grouped_repairs",
    "contract_repairs", "residual_faithfulness", "group_soundness",
    "psi_deletion_monotonicity", "grouped_correctness", "m3c_characterization",
]


def run(cmd, **kw):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, **kw)


def validate_schema():
    problems = []
    for name in ("reportability_audit_local.json", "reportability_audit_closed.json"):
        data = json.loads((RESULTS / name).read_text("utf-8"))
        for key in REQUIRED_AUDIT_KEYS:
            if key not in data:
                problems.append(f"{name}: missing key '{key}'")
        for sub in ("residual_faithfulness", "group_soundness",
                    "psi_deletion_monotonicity", "grouped_correctness"):
            for field in ("result", "checked_cases", "counterexamples"):
                if field not in data.get(sub, {}):
                    problems.append(f"{name}: {sub} missing '{field}'")
    if problems:
        print("SCHEMA VALIDATION FAILED:")
        for p in problems:
            print("  -", p)
        raise SystemExit(1)
    print("schema validation: OK")


def hash_manifest():
    manifest = {}
    for base in ("m3", "scripts", "tests"):
        for path in sorted((ROOT / base).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                rel = str(path.relative_to(ROOT)).replace("\\", "/")
                manifest[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    (ROOT / "m3" / "results" / "manifest.sha256.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
    print(f"wrote manifest with {len(manifest)} files")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dafny", default=None)
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()

    # 1-4: generate + verify (run_dafny_lattice resolves/records the version)
    generate_dafny_variants.main()
    sys.argv = ["run_dafny_lattice.py"] + (["--dafny", args.dafny] if args.dafny else [])
    run_dafny_lattice.main()

    # 5: audit
    sys.argv = ["audit_reportability.py"]
    audit_reportability.main()

    # 6: schema
    validate_schema()

    # 7: tests
    if not args.skip_tests:
        r = run([sys.executable, "-m", "pytest", "-q"], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit("pytest failed")

    # 8: manifest
    hash_manifest()

    # version-mismatch surfacing
    meas = json.loads((RESULTS / "lattice_measurements.json").read_text("utf-8"))
    if not meas["dafny_version_match"]:
        print(f"\nWARNING: measured Dafny version '{meas['dafny_version']}' "
              f"!= pinned '{meas['pinned_dafny_version']}'. Results recorded "
              "under the measured version; not treated as identical.")
    print("\nreproduce.py complete.")


if __name__ == "__main__":
    main()
