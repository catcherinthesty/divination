"""Timezone-city mismatch detector.

Checks if a provided IANA timezone string matches the city's expected
timezone from the geocoder lookup table. Returns a ClarificationRequest
on mismatch (FR-008).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from ..data_types import ClarificationRequest, Severity

_DATA_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "city_coordinates.csv"


def check_timezone_mismatch(
    city: str,
    provided_tz: Optional[str],
) -> Optional[ClarificationRequest]:
    """Check if the provided timezone matches the city's expected timezone.

    Returns None if no mismatch (or no timezone provided), or a
    ClarificationRequest describing the mismatch.
    """
    if not provided_tz or not city:
        return None

    # Look up the city's expected timezone from the lookup table
    expected_tz = _lookup_city_timezone(city)
    if expected_tz is None:
        return None  # Unknown city — can't detect mismatch

    if provided_tz != expected_tz:
        return ClarificationRequest(
            field_name="timezone",
            reason=(
                f"Timezone mismatch: city '{city}' is typically in "
                f"{expected_tz}, but timezone specified as {provided_tz}. "
                f"Please confirm which is correct."
            ),
            suggested_options=[expected_tz, provided_tz],
            format_guidance="IANA timezone identifier (e.g., America/Chicago)",
            severity=Severity.BLOCKER,
        )

    return None


def city_timezone(city: str) -> Optional[str]:
    """Look up the expected IANA timezone for a city from the CSV table.

    Used both for mismatch detection and for inferring a timezone when the
    user does not provide one (research.md: Timezone Resolution Strategy).
    """
    if not _DATA_FILE.exists():
        return None
    city_lower = city.strip().lower()
    with open(_DATA_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["name"].strip().lower() == city_lower and row.get("type") == "city":
                return row.get("timezone")
    return None


def _lookup_city_timezone(city: str) -> Optional[str]:
    """Backward-compatible alias for city_timezone()."""
    return city_timezone(city)
