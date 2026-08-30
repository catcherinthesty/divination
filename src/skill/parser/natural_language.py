"""Regex-based natural language birth data extractor (US-2).

Extracts name, date, time, and location from plain English birth
descriptions using deterministic regex patterns with named capture
groups — no LLM or probabilistic parsing (constitution Principle I).

Supported phrasings:
- Name:     "Bristol Ann Klok-Loomis was born ..." / "My daughter Bristol was born ..."
- Date:     "August 26, 2026" / "Aug. 26 2026" / "2026-08-26" / "08/26/2026"
- Time:     "10:02 PM" / "22:02" / "at noon" / "at midnight" (optional)
- Location: "in Chicago" / "at Bronson Methodist Hospital Room 310"

Fields not found in the text are left as None/empty on the BirthRecord,
so the shared validator pipeline (US-3) produces the clarification.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from ..data_types import BirthRecord, ClarificationRequest, Severity

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Proper name immediately preceding "was born" (capitalized words only)
_NAME_BEFORE_BORN = re.compile(
    r"\b(?P<name>[A-Z][a-zA-Z'’\-]+(?:\s+[A-Z][a-zA-Z'’\-]+)*)\s+was\s+born\b"
)

# Relational references instead of a proper name ("my daughter", "our son")
_RELATIONAL = re.compile(
    r"\b(?P<rel>my|our|his|her|their)\s+(?P<who>daughter|son|baby|child|girl|boy)\b",
    re.IGNORECASE,
)

# "born to <Parent Name>" — parent, not the subject
_BORN_TO = re.compile(
    r"\bborn\s+to\s+(?P<parent>[A-Z][a-zA-Z'’\-]+(?:\s+[A-Z][a-zA-Z'’\-]+)*)\b"
)

_STOPWORDS = {
    "The", "A", "An", "My", "Our", "His", "Her", "Their", "Your",
    "I", "We", "On", "In", "At", "It", "That", "This",
}

# --- Date patterns (tried in order) ---
_DATE_MONTH_NAME = re.compile(
    r"\b(?P<mon>[A-Za-z.]+)\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?\s*,?\s+(?P<year>\d{4})\b"
)
_DATE_ISO = re.compile(r"\b(?P<year>\d{4})-(?P<mon>\d{2})-(?P<day>\d{2})\b")
_DATE_SLASH = re.compile(r"\b(?P<mon>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b")

# --- Time patterns (tried in order) ---
_TIME_12H = re.compile(
    r"\b(?P<hour>\d{1,2}):(?P<min>\d{2})\s*(?P<ampm>[APap][\.]?[Mm][\.]?)\b"
)
_TIME_24H = re.compile(r"\b(?P<hour>0\d|1\d|2[0-3]):(?P<min>\d{2})\b")
_TIME_WORD = re.compile(r"\bat\s+(?P<word>noon|midnight)\b", re.IGNORECASE)

# --- Location pattern: capitalized phrase after in/at, optional Room N and , State ---
_LOCATION = re.compile(
    r"\b(?:in|at)\s+"
    r"(?P<loc>[A-Z][a-zA-Z'’\-]+"
    r"(?:\s+[A-Z][a-zA-Z'’\-]+)*"
    r"(?:\s+(?:Room|Rm\.?)\s*\d+)?"
    r"(?:,\s*[A-Z][a-z]+)?)"
)


def parse_natural_language(text: str) -> tuple[BirthRecord, list[ClarificationRequest]]:
    """Extract birth data from a plain English description.

    Returns:
        (BirthRecord with found fields, list of ClarificationRequest for
        ambiguous extractions such as relational name references).
        Fields not present in the text are None/empty.
    """
    issues: list[ClarificationRequest] = []

    name, name_issue = _extract_name(text)
    if name_issue:
        issues.append(name_issue)

    dob = _extract_date(text)
    time_of_birth = _extract_time(text)
    location = _extract_location(text)

    record = BirthRecord(
        name=name or "",
        date_of_birth=dob,  # type: ignore[arg-type]
        time_of_birth=time_of_birth,
        location_description=location or "",
    )
    return record, issues


def _extract_name(text: str) -> tuple[Optional[str], Optional[ClarificationRequest]]:
    """Extract the subject's name; flag relational references (T021)."""
    m = _NAME_BEFORE_BORN.search(text)
    if m:
        candidate = m.group("name").strip()
        # Drop a leading stopword if one slipped in ("The Bristol" → "Bristol")
        words = candidate.split()
        while words and words[0] in _STOPWORDS:
            words = words[1:]
        cleaned = " ".join(words)
        if cleaned:
            return cleaned, None

    # No proper name before "was born" — check for relational references
    rel = _RELATIONAL.search(text)
    if rel:
        phrase = f"{rel.group('rel')} {rel.group('who')}"
        return "", ClarificationRequest(
            field_name="name",
            reason=(
                f"Extracted relational reference '{phrase}' instead of a proper "
                "name. Please provide the child's actual full name."
            ),
            format_guidance="Full name (1-80 characters), e.g., 'Jane Doe'",
            severity=Severity.BLOCKER,
        )

    # "born to <Parent>" — that name is the parent's, not the subject's
    born_to = _BORN_TO.search(text)
    if born_to:
        return "", ClarificationRequest(
            field_name="name",
            reason=(
                f"Name '{born_to.group('parent')}' appears after 'born to' and is "
                "likely the parent's name. Please provide the child's actual full name."
            ),
            format_guidance="Full name (1-80 characters), e.g., 'Jane Doe'",
            severity=Severity.BLOCKER,
        )

    return None, None


def _extract_date(text: str) -> Optional[date]:
    """Extract the date of birth in any supported format."""
    m = _DATE_MONTH_NAME.search(text)
    if m:
        month_key = m.group("mon").rstrip(".").lower()
        month = _MONTHS.get(month_key)
        if month:
            return _safe_date(int(m.group("year")), month, int(m.group("day")))

    m = _DATE_ISO.search(text)
    if m:
        return _safe_date(
            int(m.group("year")), int(m.group("mon")), int(m.group("day"))
        )

    m = _DATE_SLASH.search(text)
    if m:
        # US convention: MM/DD/YYYY
        return _safe_date(
            int(m.group("year")), int(m.group("mon")), int(m.group("day"))
        )

    return None


def _safe_date(year: int, month: int, day: int) -> Optional[date]:
    """Build a date, returning None for impossible values (e.g., Feb 30)."""
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _extract_time(text: str) -> Optional[str]:
    """Extract the birth time as HH:MM (24-hour), or None if absent."""
    m = _TIME_12H.search(text)
    if m:
        hour = int(m.group("hour"))
        minute = int(m.group("min"))
        ampm = m.group("ampm").upper().replace(".", "")
        if "PM" in ampm and hour != 12:
            hour += 12
        elif "AM" in ampm and hour == 12:
            hour = 0
        if hour <= 23 and minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    m = _TIME_24H.search(text)
    if m:
        hour = int(m.group("hour"))
        minute = int(m.group("min"))
        if hour <= 23 and minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    m = _TIME_WORD.search(text)
    if m:
        return "12:00" if m.group("word").lower() == "noon" else "00:00"

    return None


def _extract_location(text: str) -> Optional[str]:
    """Extract the birth location phrase (city, hospital, or address)."""
    m = _LOCATION.search(text)
    if m:
        loc = m.group("loc").strip()
        # Drop a leading stopword if one slipped in
        words = loc.split()
        while words and words[0] in _STOPWORDS:
            words = words[1:]
        cleaned = " ".join(words).strip()
        return cleaned or None
    return None
