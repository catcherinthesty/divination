"""Deterministic filename generation from subject name initials.

Produces lowercase initial strings for use in output filenames.
Same input always produces same output (constitution Principle I).
"""

from __future__ import annotations

import re


def generate_initials(full_name: str) -> str:
    """Generate deterministic initials from a full name.

    Examples:
        "Bristol Ann Klok-Loomis" → "bakl"
        "Aria Rose Heinsen"       → "arh"
        "Jane Doe"                → "jd"

    Rules:
    - Take the first letter of each word
    - Hyphenated names: take first letter of each hyphen-separated part
      (e.g., "Klok-Loomis" contributes both 'k' and 'l')
    - All lowercase
    - Only alphabetic characters in output
    """
    # Split on whitespace, then split each part on hyphens/apostrophes
    parts = full_name.strip().split()
    initials: list[str] = []
    for part in parts:
        # Split on hyphens and apostrophes to handle compound names
        subparts = re.split(r"['\-]", part)
        for sp in subparts:
            if sp and sp[0].isalpha():
                initials.append(sp[0].lower())

    result = "".join(initials)
    # Validate: must be non-empty and purely alphabetic
    if not result or not result.isalpha():
        raise ValueError(f"Cannot generate valid initials from name: {full_name!r}")
    return result


def chart_filename(initials: str, ext: str = "svg") -> str:
    """Generate a chart output filename from initials.

    Example: chart_filename("bakl", "svg") → "bakl_chart.svg"
    """
    return f"{initials}_chart.{ext}"


def api_call_filename(initials: str) -> str:
    """Generate the API call record filename."""
    return f"{initials}_api_call.json"
