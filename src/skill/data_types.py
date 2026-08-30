"""Data type definitions for the Natal Chart Skill.

Defines the core entities: BirthRecord, GeocodeResult, ClarificationRequest,
and ChartOutput per data-model.md specifications.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class RecordState(Enum):
    """State transitions for a BirthRecord through the pipeline."""
    DRAFT = "draft"
    VALIDATING = "validating"
    CLARIFYING = "clarifying"
    VALID = "valid"
    READY_FOR_RENDERING = "ready_for_rendering"


class Confidence(Enum):
    """Geocoding confidence level."""
    HIGH = "high"      # exact match in lookup table
    MEDIUM = "medium"  # partial/case-insensitive match
    LOW = "low"        # user-provided coordinates


class Severity(Enum):
    """Clarification request severity."""
    BLOCKER = "blocker"  # chart cannot proceed without this field
    WARNING = "warning"  # chart can proceed but with reduced accuracy


@dataclass
class BirthRecord:
    """Structured representation of a person's birth data.

    The canonical input that flows through parser → validator → geocoder
    before reaching the renderer.
    """
    name: str
    date_of_birth: Optional[date] = None  # Required for chart gen; NL may leave None
    time_of_birth: Optional[str] = None  # "HH:MM" 24-hour format, or None
    location_description: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None  # IANA timezone string
    nation_code: Optional[str] = None  # ISO 3166-1 alpha-2
    state: RecordState = RecordState.DRAFT

    def validate_name(self) -> list[ClarificationRequest]:
        """Validate the name field per FR-002."""
        issues: list[ClarificationRequest] = []
        if not self.name or not self.name.strip():
            issues.append(ClarificationRequest(
                field_name="name",
                reason="Name is required.",
                format_guidance="Full name (1-80 characters)",
                severity=Severity.BLOCKER,
            ))
        elif len(self.name) > 80:
            issues.append(ClarificationRequest(
                field_name="name",
                reason=f"Name exceeds 80 characters ({len(self.name)}).",
                format_guidance="Full name (1-80 characters)",
                severity=Severity.BLOCKER,
            ))
        elif not re.match(r"^[A-Za-z][A-Za-z\s'\-]*$", self.name):
            issues.append(ClarificationRequest(
                field_name="name",
                reason="Name contains invalid characters. Only letters, spaces, hyphens, and apostrophes are allowed.",
                format_guidance="e.g., 'Jane Doe' or 'Mary O'Brien'",
                severity=Severity.BLOCKER,
            ))
        return issues

    def validate_date(self) -> list[ClarificationRequest]:
        """Validate the date of birth per FR-002."""
        issues: list[ClarificationRequest] = []
        if self.date_of_birth is None:
            issues.append(ClarificationRequest(
                field_name="date_of_birth",
                reason="Date of birth is required.",
                format_guidance="YYYY-MM-DD",
                severity=Severity.BLOCKER,
            ))
            return issues
        today = date.today()
        if self.date_of_birth > today:
            issues.append(ClarificationRequest(
                field_name="date_of_birth",
                reason=f"Date {self.date_of_birth.isoformat()} is in the future. Please confirm or correct.",
                format_guidance="YYYY-MM-DD",
                severity=Severity.BLOCKER,
            ))
        elif (today - self.date_of_birth).days > 150 * 365:
            issues.append(ClarificationRequest(
                field_name="date_of_birth",
                reason=f"Date {self.date_of_birth.isoformat()} is more than 150 years ago. Please confirm.",
                format_guidance="YYYY-MM-DD",
                severity=Severity.BLOCKER,
            ))
        return issues

    def validate_time(self) -> list[ClarificationRequest]:
        """Validate time of birth per FR-009."""
        issues: list[ClarificationRequest] = []
        if self.time_of_birth is not None:
            m = re.match(r"^(\d{1,2}):(\d{2})$", self.time_of_birth)
            if not m:
                issues.append(ClarificationRequest(
                    field_name="time_of_birth",
                    reason=f"Time '{self.time_of_birth}' is not in valid HH:MM format.",
                    format_guidance="HH:MM (24-hour, e.g., 22:02)",
                    severity=Severity.BLOCKER,
                ))
            else:
                hour = int(m.group(1))
                minute = int(m.group(2))
                if hour > 23 or minute > 59:
                    issues.append(ClarificationRequest(
                        field_name="time_of_birth",
                        reason=f"Time '{self.time_of_birth}' is outside valid range (00:00-23:59).",
                        format_guidance="HH:MM (24-hour, e.g., 22:02)",
                        severity=Severity.BLOCKER,
                    ))
        return issues

    def validate_location(self) -> list[ClarificationRequest]:
        """Validate location description per FR-002."""
        issues: list[ClarificationRequest] = []
        if not self.location_description or not self.location_description.strip():
            issues.append(ClarificationRequest(
                field_name="location_description",
                reason="Birth location is required.",
                format_guidance="City name, hospital name, or full address",
                severity=Severity.BLOCKER,
            ))
        return issues

    def validate_coordinates(self) -> list[ClarificationRequest]:
        """Validate user-provided coordinates if present."""
        issues: list[ClarificationRequest] = []
        if self.latitude is not None and not (-90.0 <= self.latitude <= 90.0):
            issues.append(ClarificationRequest(
                field_name="latitude",
                reason=f"Latitude {self.latitude} is outside valid range (-90 to 90).",
                format_guidance="Decimal degrees, -90.0 to 90.0",
                severity=Severity.BLOCKER,
            ))
        if self.longitude is not None and not (-180.0 <= self.longitude <= 180.0):
            issues.append(ClarificationRequest(
                field_name="longitude",
                reason=f"Longitude {self.longitude} is outside valid range (-180 to 180).",
                format_guidance="Decimal degrees, -180.0 to 180.0",
                severity=Severity.BLOCKER,
            ))
        return issues

    def all_issues(self) -> list[ClarificationRequest]:
        """Run all validations and return combined list of issues."""
        issues: list[ClarificationRequest] = []
        issues.extend(self.validate_name())
        issues.extend(self.validate_date())
        issues.extend(self.validate_time())
        issues.extend(self.validate_location())
        issues.extend(self.validate_coordinates())
        return issues


@dataclass
class GeocodeResult:
    """Output of address resolution.

    Produced by the geocoder module when a location description is resolved
    to coordinates.
    """
    latitude: float
    longitude: float
    source_location: str
    confidence: Confidence = Confidence.HIGH
    matched_name: Optional[str] = None


@dataclass
class ClarificationRequest:
    """Interaction artifact produced when input validation detects insufficient data."""
    field_name: str
    reason: str
    suggested_options: Optional[list[str]] = None
    format_guidance: Optional[str] = None
    severity: Severity = Severity.BLOCKER


@dataclass
class ChartOutput:
    """The set of files produced for one chart generation."""
    svg_path: str
    html_path: str
    json_path: str
    subject_name: str
    initials: str
