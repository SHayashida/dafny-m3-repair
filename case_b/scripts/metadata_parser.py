"""Strict parser for machine-readable metadata frozen in the canonical source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from common import METADATA_SCHEMA, read_json


class MetadataError(ValueError):
    pass


def parse_metadata_text(source: str, expected_levers: Optional[Iterable[str]] = None) -> List[dict]:
    schema = read_json(METADATA_SCHEMA)
    prefix = schema["line_prefix"]
    required = set(schema["required_fields"])
    records: Dict[str, dict] = {}
    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith(prefix):
            continue
        payload = stripped[len(prefix):]
        try:
            record = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise MetadataError(f"line {line_number}: invalid metadata JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise MetadataError(f"line {line_number}: metadata must be an object")
        fields = set(record)
        if fields != required:
            missing = sorted(required - fields)
            unknown = sorted(fields - required)
            raise MetadataError(f"line {line_number}: metadata fields mismatch; missing={missing}, unknown={unknown}")
        if not all(isinstance(record[field], str) and record[field] for field in required):
            raise MetadataError(f"line {line_number}: every metadata field must be a non-empty string")
        lever = record["lever_id"]
        if lever in records:
            raise MetadataError(f"line {line_number}: duplicate/conflicting metadata for {lever}")
        records[lever] = record

    expected = set(expected_levers) if expected_levers is not None else None
    if expected is not None and set(records) != expected:
        raise MetadataError(
            f"metadata lever set mismatch; missing={sorted(expected - set(records))}, "
            f"unknown={sorted(set(records) - expected)}"
        )
    if not records:
        raise MetadataError("canonical source contains no Case B metadata")
    return [records[key] for key in sorted(records)]


def parse_metadata_file(path: Path, expected_levers: Optional[Iterable[str]] = None) -> List[dict]:
    return parse_metadata_text(path.read_text(encoding="utf-8"), expected_levers)


def normalized_group_mapping(records: Iterable[dict]) -> dict:
    mapping: dict[str, str] = {}
    for record in records:
        lever = record["lever_id"]
        group = record["report_group"]
        if lever in mapping:
            raise MetadataError(f"duplicate group assignment for {lever}")
        mapping[lever] = group
    return {key: mapping[key] for key in sorted(mapping)}
