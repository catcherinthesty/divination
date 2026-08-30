"""Plausibility and range validator.

Checks date/time plausibility, coordinate ranges, and other sanity checks.
Returns a list of ClarificationRequest for implausible values (US-3).
"""

from __future__ import annotations

from ..data_types import BirthRecord, ClarificationRequest, Severity


def validate_ranges(record: BirthRecord) -> list[ClarificationRequest]:
    """Validate plausibility of all fields on a BirthRecord.

    Returns a list of ClarificationRequest objects (empty if all plausible).
    Includes date range checks (future date, 150-year threshold),
    time-of-birth format and bounds, and coordinate bounds.
    """
    issues: list[ClarificationRequest] = []

    # Date range validation (future date + 150-year check)
    issues.extend(record.validate_date())

    # Time range validation
    issues.extend(record.validate_time())

    # Coordinate range validation
    issues.extend(record.validate_coordinates())

    return issues
