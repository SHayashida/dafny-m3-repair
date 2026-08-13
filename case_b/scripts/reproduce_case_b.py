"""Canonical exhaustive Case B reproduction command."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from audit_case_b import run_audit
from design_lock import verify_lock
from fault_injections import run_fault_injections
from generate_variants import generate
from independent_audit import recompute
from measure_variants import measure
from common import AUDIT, ROOT, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dafny", default=None)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    verify_lock()
    generate()
    measurement = measure(args.dafny)
    audit = run_audit()
    independent = recompute()
    write_json(AUDIT / "independent_recomputation.json", independent)
    faults = run_fault_injections()
    write_json(AUDIT / "fault_injection_results.json", faults)
    if not args.skip_tests:
        result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
        if result.returncode != 0:
            raise SystemExit("pytest failed")
    print(
        "Case B reproduction complete: "
        f"variants={measurement['variant_count_measured']}, commutes={audit['commutes']}"
    )


if __name__ == "__main__":
    main()
