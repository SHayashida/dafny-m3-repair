from __future__ import annotations

import sys
from pathlib import Path

import pytest

CASE_B = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE_B / "scripts"))

from common import CANONICAL, DESIGN_LOCK, read_json  # noqa: E402
from design_lock import verify_lock  # noqa: E402
from metadata_parser import MetadataError, parse_metadata_file, parse_metadata_text  # noqa: E402


def test_frozen_design_lock_matches_inputs():
    lock = verify_lock()
    assert lock == read_json(DESIGN_LOCK)
    assert len(lock["repair_levers"]) == 3


def test_metadata_is_total_and_unique():
    lock = read_json(DESIGN_LOCK)
    records = parse_metadata_file(CANONICAL, lock["repair_levers"])
    assert {record["lever_id"] for record in records} == set(lock["repair_levers"])


def test_missing_and_conflicting_metadata_fail():
    lock = read_json(DESIGN_LOCK)
    source = CANONICAL.read_text(encoding="utf-8")
    lines = [line for line in source.splitlines() if "CASE_B_METADATA" in line]
    with pytest.raises(MetadataError):
        parse_metadata_text(source.replace(lines[0] + "\n", "", 1), lock["repair_levers"])
    with pytest.raises(MetadataError):
        parse_metadata_text(source.replace(lines[0], lines[0] + "\n" + lines[0], 1), lock["repair_levers"])
