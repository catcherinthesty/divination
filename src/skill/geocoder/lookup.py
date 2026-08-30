"""Deterministic city/address-to-coordinates resolver.

Reads a bundled CSV lookup table at import time. No network calls are made.
The same input always produces the same output (constitution Principle I).

Matching strategy (deterministic, in priority order):
1. Exact case-insensitive match on name → confidence HIGH
2. Hospital/landmark exact match → confidence HIGH
3. Partial substring match (case-insensitive) → confidence MEDIUM
4. Street address resolution (number + street pattern) → confidence MEDIUM
5. User-provided coordinates → confidence LOW

When multiple entries match with similar confidence, all candidates are
returned sorted by confidence then alphabetically by name, enabling the
clarification loop to present options to the user.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..data_types import GeocodeResult, Confidence

_DATA_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "city_coordinates.csv"

# Load lookup table at module level (deterministic — same file, same results)
_LOOKUP: list[dict[str, str]] = []


def _load_lookup() -> None:
    """Load the CSV lookup table into memory."""
    global _LOOKUP
    if _DATA_FILE.exists():
        with open(_DATA_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            _LOOKUP = list(reader)


_load_lookup()

# Street address pattern: "1234 Main St" or similar numeric prefix
_STREET_PATTERN = re.compile(
    r"\b(\d{1,5})\s+"  # street number
    r"(?P<street>[A-Z][a-zA-Z]+)"  # street name (first word after number)
    r"(?:\s+(?P<suffix>St|Street|Ave|Avenue|Blvd|Boulevard|Dr|Drive|"
         r"Rd|Road|Ln|Lane|Way|Court,Ct|Plaza|Place|Parkway))?\b",
)


def resolve(location: str) -> list[GeocodeResult]:
    """Resolve a location string to one or more coordinate results.

    Returns a list of GeocodeResult objects sorted by confidence (HIGH first),
    then alphabetically by matched_name. A single-element list means
    unambiguous match; multiple elements mean disambiguation is needed.
    Empty list means no match found.

    Matching strategy (deterministic, in priority order):
    1. Exact case-insensitive match on name → HIGH confidence
    2. Partial substring match (case-insensitive) → MEDIUM confidence
    3. Street address resolution (e.g., "1234 Main St Chicago") → MEDIUM
    """
    location_lower = location.strip().lower()

    # Pass 1: exact match (case-insensitive) — HIGH confidence
    exact_matches = [
        row for row in _LOOKUP
        if row["name"].strip().lower() == location_lower
    ]
    if len(exact_matches) == 1:
        return [_to_result(exact_matches[0], Confidence.HIGH)]
    elif len(exact_matches) > 1:
        # Multiple exact matches — all HIGH confidence, sorted alphabetically
        results = [_to_result(row, Confidence.HIGH) for row in exact_matches]
        return _sort_by_confidence_then_name(results)

    # Pass 2: partial match (substring, case-insensitive) → MEDIUM
    partial_matches = [
        row for row in _LOOKUP
        if location_lower in row["name"].strip().lower()
        or row["name"].strip().lower() in location_lower
    ]
    if partial_matches:
        results = [_to_result(row, Confidence.MEDIUM) for row in partial_matches]
        # If we got exactly one partial match and no exact match above,
        # check confidence: single medium is still usable
        if len(results) == 1:
            return results
        # Multiple partial matches — sort by confidence then name
        return _sort_by_confidence_then_name(results)

    # Pass 3: street address resolution (T028)
    # Try to extract a street address from the location string, then match
    # the city portion against the lookup table.
    street_match = _STREET_PATTERN.search(location.strip())
    if street_match:
        street_number = street_match.group(1)
        street_name = street_match.group("street")
        street_suffix = street_match.group("suffix") or ""
        suffix_str = f" {street_suffix}" if street_suffix else ""

        # Find entries whose name contains the street pattern (hospital names, etc.)
        street_candidates = [
            row for row in _LOOKUP
            if street_name.lower() in row["name"].strip().lower()
        ]

        # Also try matching the full location against entries containing the street number
        addr_candidates = [
            row for row in _LOOKUP
            if street_number in row["name"]
            and (street_name.lower() in row["name"].strip().lower() or suffix_str.lower() in row["name"].strip().lower())
        ]

        # Prefer address-specific matches, fall back to street-name matches
        if addr_candidates:
            results = [_to_result(row, Confidence.MEDIUM) for row in addr_candidates]
            return _sort_by_confidence_then_name(results)
        elif street_candidates:
            results = [_to_result(row, Confidence.MEDIUM) for row in street_candidates]
            return _sort_by_confidence_then_name(results)

    # Pass 4: token-based partial match (split on common delimiters)
    # Try matching individual tokens from the location against lookup names
    tokens = set(re.split(r"[,\s]+", location_lower))
    if len(tokens) > 1:
        token_matches: list[tuple[dict[str, str], int]] = []
        for row in _LOOKUP:
            row_name_lower = row["name"].strip().lower()
            row_tokens = set(re.split(r"[,\s]+", row_name_lower))
            overlap = tokens & row_tokens
            if len(overlap) >= 2:  # At least 2 tokens match
                token_matches.append((row, len(overlap)))
        if token_matches:
            # Sort by overlap count descending
            token_matches.sort(key=lambda x: -x[1])
            results = [_to_result(row, Confidence.MEDIUM) for row, _ in token_matches[:5]]
            return _sort_by_confidence_then_name(results)

    return []


def resolve_with_user_coords(
    location: str,
    latitude: Optional[float],
    longitude: Optional[float],
) -> GeocodeResult:
    """Resolve using user-provided coordinates if available, else lookup.

    Returns a single GeocodeResult. If user provides valid coordinates,
    they take precedence (confidence=LOW). Otherwise falls back to lookup
    and returns the best match (highest confidence, alphabetically first).
    """
    if latitude is not None and longitude is not None:
        return GeocodeResult(
            latitude=latitude,
            longitude=longitude,
            source_location=location,
            confidence=Confidence.LOW,
            matched_name=None,
        )

    results = resolve(location)
    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        # Return the first match (highest confidence, alphabetically by name)
        results.sort(key=lambda r: (r.matched_name or ""))
        return results[0]

    raise ValueError(f"No geocoding match found for location: {location!r}")


def _sort_by_confidence_then_name(results: list[GeocodeResult]) -> list[GeocodeResult]:
    """Sort results by confidence (HIGH first), then alphabetically by name."""
    confidence_order = {Confidence.HIGH: 0, Confidence.MEDIUM: 1, Confidence.LOW: 2}
    return sorted(results, key=lambda r: (confidence_order[r.confidence], r.matched_name or ""))


def _to_result(row: dict[str, str], confidence: Confidence) -> GeocodeResult:
    """Convert a CSV row to a GeocodeResult."""
    return GeocodeResult(
        latitude=float(row["latitude"]),
        longitude=float(row["longitude"]),
        source_location=row["name"],
        confidence=confidence,
        matched_name=row["name"],
    )
