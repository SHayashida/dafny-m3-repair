"""
run_dafny_lattice.py

Verify every generated Dafny variant with the real Dafny verifier and record the
measured outcome, verifier command, source hash, and log hash. Outcomes are
NEVER hardcoded -- SatPhi/SatPsi are built from these measurements.

Dafny executable resolution order:
  1. --dafny CLI argument
  2. DAFNY_EXE environment variable
  3. `dafny` on PATH
  4. bundled fallback path used during development

If the resolved Dafny version differs from the pinned version, the mismatch is
recorded in metadata and NOT silently treated as identical.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m3lib as m3
from generate_dafny_variants import variant_records

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "m3" / "generated"
RESULTS = ROOT / "m3" / "results"

PINNED_DAFNY_VERSION = "4.11.0"
DEV_FALLBACK = Path(
    "C:/Users/hayas/AppData/Local/Temp/claude/"
    "C--Users-hayas-Documents-Fixed-atmic-test/"
    "82e1bd3b-2a6e-4e99-bab6-e918d012b99a/scratchpad/dafnydist/dafny/Dafny.exe"
)


def resolve_dafny(cli_arg):
    for cand in (cli_arg, os.environ.get("DAFNY_EXE"), shutil.which("dafny")):
        if cand and Path(cand).exists():
            return str(cand)
    if DEV_FALLBACK.exists():
        return str(DEV_FALLBACK)
    raise SystemExit("Dafny executable not found. Set --dafny or DAFNY_EXE.")


def dafny_version(exe):
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True,
                             timeout=120)
        return out.stdout.strip() or out.stderr.strip()
    except Exception as e:  # noqa: BLE001
        return f"unknown ({e})"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_one(exe, dfy_path):
    """Run `dafny verify` on one file. Return (passed, command, raw_output)."""
    cmd = [exe, "verify", str(dfy_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    out = (proc.stdout or "") + (proc.stderr or "")
    # Dafny prints "... finished with N verified, M errors". Pass iff 0 errors
    # AND exit code 0. Be strict: an error line or nonzero exit => fail.
    passed = (proc.returncode == 0) and ("0 errors" in out) and ("Error:" not in out)
    return passed, " ".join(cmd), out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dafny", default=None, help="path to Dafny executable")
    args = ap.parse_args()

    exe = resolve_dafny(args.dafny)
    ver = dafny_version(exe)
    version_match = PINNED_DAFNY_VERSION in ver

    RESULTS.mkdir(parents=True, exist_ok=True)
    (GEN / "local").mkdir(parents=True, exist_ok=True)
    (GEN / "closed").mkdir(parents=True, exist_ok=True)

    records = variant_records()
    measurements = []
    for rec in records:
        dfy = rec["path"]
        if not dfy.exists():
            raise SystemExit(f"missing generated variant {dfy}; run generate first")
        passed, cmd, raw = verify_one(exe, dfy)
        log_path = dfy.with_suffix(".log")
        log_path.write_text(raw, encoding="utf-8", newline="\n")
        entry = {
            "kind": rec["kind"],
            "scope": rec["scope"],
            "retained_levers": rec["retained_levers"],
            "source": str(dfy.relative_to(ROOT)).replace("\\", "/"),
            "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
            "verifier_command": cmd.replace(exe, "dafny"),
            "verifier_passed": passed,
            "source_sha256": sha256_file(dfy),
            "log_sha256": sha256_text(raw),
        }
        if rec["kind"] == "contract":
            entry["retained_atoms"] = rec["retained_atoms"]
        measurements.append(entry)
        tag = "PASS" if passed else "FAIL"
        print(f"[{tag}] {entry['source']}")

    out = {
        "dafny_executable": exe.replace("\\", "/"),
        "dafny_version": ver,
        "pinned_dafny_version": PINNED_DAFNY_VERSION,
        "dafny_version_match": version_match,
        "measurements": measurements,
    }
    (RESULTS / "lattice_measurements.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8", newline="\n")
    print(f"\nwrote {RESULTS / 'lattice_measurements.json'} "
          f"({len(measurements)} measurements)")
    if not version_match:
        print(f"WARNING: Dafny version '{ver}' != pinned {PINNED_DAFNY_VERSION}")


if __name__ == "__main__":
    main()
