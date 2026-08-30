"""Structured input parser for JSON, YAML subset, and CSV formats.

Maps parsed data to BirthRecord dataclass. No external dependencies —
includes an inline YAML subset parser per research.md decision.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Optional

from ..data_types import BirthRecord


def parse_input(file_path: str, fmt: str) -> BirthRecord:
    """Parse an input file into a BirthRecord.

    Args:
        file_path: Path to the input file.
        fmt: One of "json", "yaml", "csv".

    Returns:
        A BirthRecord with parsed fields (state=DRAFT).

    Raises:
        ValueError: If the file cannot be parsed or required fields are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    text = path.read_text(encoding="utf-8")

    if fmt == "json":
        data = json.loads(text)
    elif fmt == "yaml":
        data = _parse_yaml_subset(text)
    elif fmt == "csv":
        data = _parse_csv(text)
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    return _to_birth_record(data)


def _to_birth_record(data: dict[str, Any]) -> BirthRecord:
    """Convert a parsed dict to a BirthRecord."""
    # Parse date
    dob_str = data.get("date_of_birth", "")
    if isinstance(dob_str, str):
        try:
            dob = date.fromisoformat(dob_str)
        except ValueError:
            raise ValueError(f"Invalid date format: {dob_str!r}. Expected YYYY-MM-DD.")
    else:
        raise ValueError(f"date_of_birth must be a string in YYYY-MM-DD format, got {type(dob_str)}")

    # Extract location
    loc = data.get("location", {})
    if isinstance(loc, dict):
        city = loc.get("city", "")
        address = loc.get("address", "")
        nation = loc.get("nation", "")
        location_desc = f"{address}, {city}" if address and city else (city or address)
    elif isinstance(loc, str):
        location_desc = loc
        city = loc
        nation = ""
    else:
        location_desc = str(data.get("location_description", ""))
        city = location_desc
        nation = ""

    # Extract coordinates (optional)
    lat = data.get("latitude")
    lon = data.get("longitude")
    if lat is not None:
        lat = float(lat)
    if lon is not None:
        lon = float(lon)

    return BirthRecord(
        name=data.get("name", ""),
        date_of_birth=dob,
        time_of_birth=data.get("time_of_birth"),
        location_description=location_desc,
        latitude=lat,
        longitude=lon,
        timezone=data.get("timezone"),
        nation_code=nation or None,
    )


def _parse_csv(text: str) -> dict[str, Any]:
    """Parse a single-row CSV into a dict."""
    reader = csv.DictReader(text.strip().splitlines())
    rows = list(reader)
    if not rows:
        raise ValueError("CSV input is empty.")
    row = rows[0]

    # Map CSV columns to the expected structure
    result: dict[str, Any] = {
        "name": row.get("name", ""),
        "date_of_birth": row.get("date_of_birth", ""),
        "time_of_birth": row.get("time_of_birth") or None,
        "timezone": row.get("timezone") or None,
    }

    # Build location dict from CSV columns
    city = row.get("location_city", "")
    address = row.get("location_address", "")
    nation = row.get("location_nation", "")
    if city or address:
        result["location"] = {
            "city": city,
            "address": address,
            "nation": nation,
        }

    # Coordinates (optional)
    lat = row.get("latitude")
    lon = row.get("longitude")
    if lat:
        result["latitude"] = float(lat)
    if lon:
        result["longitude"] = float(lon)

    return result


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    """Minimal YAML subset parser — no external dependencies.

    Supports:
    - Top-level key: value pairs
    - Nested objects via 2-space indentation
    - Quoted strings (single or double)
    - Comments (#) and blank lines
    - Integer/float values
    - null/None values

    Does NOT support: anchors, aliases, multi-line strings, complex lists.
    """
    result: dict[str, Any] = {}
    _parse_yaml_block(text.splitlines(), 0, result, 0)
    return result


def _parse_yaml_block(
    lines: list[str],
    start: int,
    target: dict[str, Any],
    base_indent: int,
) -> int:
    """Recursively parse a YAML block into a dict. Returns next line index."""
    i = start
    while i < len(lines):
        raw = lines[i]

        # Skip blank lines and comments
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        # Determine indentation level
        indent = len(raw) - len(raw.lstrip())
        if indent < base_indent:
            break

        # Must be at exactly base_indent for this block
        if indent > base_indent:
            i += 1
            continue

        # Parse key: value
        m = re.match(r"^(\w[\w\s]*):\s*(.*)$", stripped)
        if not m:
            i += 1
            continue

        key = m.group(1).strip()
        value_str = m.group(2).strip()

        # Remove trailing comments (but not inside quotes)
        if value_str and not value_str.startswith(("'", '"')):
            comment_idx = value_str.find(" #")
            if comment_idx != -1:
                value_str = value_str[:comment_idx].rstrip()

        if value_str == "" or value_str == "null" or value_str == "~":
            # Check if next lines are indented (nested object)
            j = i + 1
            while j < len(lines):
                next_stripped = lines[j].strip()
                if not next_stripped or next_stripped.startswith("#"):
                    j += 1
                    continue
                next_indent = len(lines[j]) - len(lines[j].lstrip())
                if next_indent > base_indent:
                    # Nested object
                    nested: dict[str, Any] = {}
                    i = _parse_yaml_block(lines, j, nested, next_indent)
                    target[key] = nested
                    break
                else:
                    target[key] = None
                    i += 1
                    break
            else:
                target[key] = None
                i += 1
        else:
            # Simple value
            target[key] = _parse_yaml_value(value_str)
            i += 1

    return i


def _parse_yaml_value(s: str) -> Any:
    """Parse a YAML scalar value."""
    if s in ("null", "~", ""):
        return None
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False

    # Quoted string
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]

    # Integer
    if re.match(r"^-?\d+$", s):
        return int(s)

    # Float
    if re.match(r"^-?\d+\.\d+$", s):
        return float(s)

    return s
