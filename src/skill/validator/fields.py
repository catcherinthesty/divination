"""Required field validator.

Checks that all required birth data fields are present and valid.
Returns a list of ClarificationRequest for missing or invalid fields (FR-002).
Also detects ambiguous locations that resolve to multiple candidates (US-3).
"""

from __future__ import annotations

from ..data_types import BirthRecord, ClarificationRequest, Severity
from ..geocoder.lookup import resolve


def validate_fields(record: BirthRecord) -> list[ClarificationRequest]:
    """Validate all required fields on a BirthRecord.

    Returns a list of ClarificationRequest objects (empty if valid).
    Blockers prevent chart generation; warnings allow it with caveats.
    """
    issues: list[ClarificationRequest] = []

    # Name validation
    issues.extend(record.validate_name())

    # Location validation (date/time/range checks are in ranges.py)
    issues.extend(record.validate_location())

    return issues


def validate_time_warning(record: BirthRecord) -> Optional[ClarificationRequest]:
    """Check if time is missing and generate a warning (not blocker).

    Per FR-009: missing time means house positions will be approximate.
    This is a warning, not a blocker — the user can choose to proceed.
    """
    from typing import Optional as _Opt  # avoid circular import at module level
    if record.time_of_birth is None:
        return ClarificationRequest(
            field_name="time_of_birth",
            reason=(
                "Birth time not provided — house positions will be approximate "
                "(defaulting to midnight). Please provide a time for accurate houses, "
                "or confirm to proceed with approximate positions."
            ),
            format_guidance="HH:MM (24-hour, e.g., 22:02)",
            severity=Severity.WARNING,
        )
    return None


def validate_ambiguous_location(record: BirthRecord) -> list[ClarificationRequest]:
    """Detect ambiguous location descriptions that resolve to multiple candidates.

    Queries the geocoder lookup table for the record's location_description.
    If more than one match is found, generates a ClarificationRequest with
    severity=BLOCKER listing all candidate cities.

    Returns an empty list if the location is unambiguous or not provided.
    """
    issues: list[ClarificationRequest] = []
    if not record.location_description or not record.location_description.strip():
        return issues  # Empty location handled by validate_fields

    results = resolve(record.location_description)
    if len(results) > 1:
        candidates = [r.matched_name or r.source_location for r in results]
        issues.append(ClarificationRequest(
            field_name="location",
            reason=(
                f"Location '{record.location_description}' is ambiguous "
                f"({len(results)} matches). Please specify which one."
            ),
            suggested_options=candidates,
            format_guidance="City name, hospital name, or add latitude/longitude fields",
            severity=Severity.BLOCKER,
        ))
    return issues
