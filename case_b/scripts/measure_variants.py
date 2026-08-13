"""Invoke Dafny separately for every generated Case B lattice variant."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from common import (
    GENERATED, MEASUREMENTS, RAW, ROOT, read_json, relative, sha256_file, write_json,
)
from design_lock import verify_lock

OUTCOMES = ("VERIFIED", "VERIFICATION_FAILED", "FRONTEND_ERROR", "TIMEOUT", "TOOL_ERROR")


class MeasurementError(RuntimeError):
    pass


def resolve_dafny(cli_value: Optional[str]) -> str:
    candidates = (cli_value, os.environ.get("DAFNY_EXE"), shutil.which("dafny"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate).resolve())
    raise MeasurementError("Dafny executable not found; pass --dafny or set DAFNY_EXE")


def dafny_version(executable: str) -> tuple[str, int]:
    proc = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=120)
    output = (proc.stdout or proc.stderr).strip()
    return output, proc.returncode


def classify_outcome(exit_code: int, stdout: str, stderr: str) -> str:
    combined = stdout + "\n" + stderr
    lower = combined.lower()
    if exit_code == 0 and re.search(r"\b0 errors?\b", lower):
        return "VERIFIED"
    frontend_markers = (
        "parser errors detected", "resolution/type errors detected", "name resolution failed",
        "type checking failed", "parse error", "unresolved identifier", "invalid option",
    )
    if any(marker in lower for marker in frontend_markers):
        return "FRONTEND_ERROR"
    verifier_markers = (
        "assertion might not hold", "postcondition might not hold", "precondition for this call might not hold",
        "invariant might not be maintained", "decreases expression might not decrease",
    )
    verifier_summary = re.search(r"dafny program verifier finished with .*\b[1-9]\d* errors?\b", lower)
    if verifier_summary or any(marker in lower for marker in verifier_markers):
        return "VERIFICATION_FAILED"
    return "TOOL_ERROR"


def run_one(executable: str, source: Path, timeout: int) -> dict:
    command = [executable, "verify", str(source)]
    started = time.monotonic()
    try:
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        elapsed = time.monotonic() - started
        outcome = classify_outcome(proc.returncode, proc.stdout or "", proc.stderr or "")
        return {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "elapsed_seconds": round(elapsed, 6),
            "outcome": outcome,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "outcome": "TIMEOUT",
        }
    except OSError as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "outcome": "TOOL_ERROR",
        }


def measure(dafny: Optional[str] = None) -> dict:
    lock = verify_lock()
    manifest_path = GENERATED.parent / "case_b_variants.json"
    manifest = read_json(manifest_path)
    if manifest["variant_count_generated"] != manifest["variant_count_expected"]:
        raise MeasurementError("variant generation is not exhaustive")
    executable = resolve_dafny(dafny)
    version, version_exit = dafny_version(executable)
    if version_exit != 0:
        raise MeasurementError(f"Dafny --version failed with exit {version_exit}: {version}")
    version_match = lock["dafny_version_expected"] in version
    RAW.mkdir(parents=True, exist_ok=True)
    results = []
    timeout = int(lock["verification_timeout_seconds"])
    for variant in manifest["variants"]:
        source = ROOT / variant["source"]
        if sha256_file(source) != variant["source_sha256"]:
            raise MeasurementError(f"source hash mismatch before invocation: {variant['variant_id']}")
        measured = run_one(executable, source, timeout)
        entry = {
            "schema_version": "case-b-raw-measurement-v1",
            "variant_id": variant["variant_id"],
            "deleted_levers": variant["deleted_levers"],
            "retained_levers": variant["retained_levers"],
            "source": variant["source"],
            "source_sha256": variant["source_sha256"],
            "design_lock_sha256": manifest["design_lock_sha256"],
            "group_mapping_sha256": lock["group_mapping_sha256"],
            "dafny_executable": executable,
            "dafny_version": version,
            "dafny_version_expected": lock["dafny_version_expected"],
            "dafny_version_match": version_match,
            **measured,
        }
        raw_path = RAW / f"{variant['variant_id']}.result.json"
        write_json(raw_path, entry)
        results.append({
            "variant_id": variant["variant_id"],
            "raw_result": relative(raw_path),
            "raw_result_sha256": sha256_file(raw_path),
            "outcome": entry["outcome"],
        })
        print(f"[{entry['outcome']}] {variant['variant_id']}")
    counts = {outcome: sum(result["outcome"] == outcome for result in results) for outcome in OUTCOMES}
    aggregate = {
        "schema_version": "case-b-measurement-index-v1",
        "dafny_executable": executable,
        "dafny_version": version,
        "dafny_version_expected": lock["dafny_version_expected"],
        "dafny_version_match": version_match,
        "variant_manifest": relative(manifest_path),
        "variant_manifest_sha256": sha256_file(manifest_path),
        "variant_count_expected": manifest["variant_count_expected"],
        "variant_count_measured": len(results),
        "outcome_counts": counts,
        "results": results,
    }
    write_json(MEASUREMENTS / "variant_results.json", aggregate)
    return aggregate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dafny", default=None)
    args = parser.parse_args()
    aggregate = measure(args.dafny)
    print(f"measured {aggregate['variant_count_measured']} Case B variants")


if __name__ == "__main__":
    main()
