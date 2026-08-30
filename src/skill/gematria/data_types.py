"""Data types for the Gematria skill."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class System(Enum):
    """Gematria calculation system."""
    SIMPLE = "simple"           # Pythagorean: A=1…I=9, J=1…R=9, S=1…Z=8
    ORDINAL = "ordinal"         # Full ordinal: A=1 … Z=26
    REVERSE = "reverse"         # Reverse ordinal: A=26 … Z=1


class GematriaState(Enum):
    DRAFT = "draft"
    COMPUTED = "computed"
    READY_FOR_RENDERING = "ready_for_rendering"


# Master numbers — not reduced to single digit
MASTER_NUMBERS = {11, 22, 33}


def reduce_number(value: int) -> int:
    """Reduce a number to a single digit or master number (1-9, 11, 22, 33)."""
    if value in MASTER_NUMBERS:
        return value
    while value > 9 and value not in MASTER_NUMBERS:
        value = sum(int(d) for d in str(value))
    return value


@dataclass
class WordBreakdown:
    """Gematria values for a single word."""
    word: str
    total: int
    reduced: int
    vowel_total: int
    consonant_total: int
    letter_values: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class SystemResult:
    """All gematria values for one system applied to a name."""
    system: System
    total: int
    reduced: int
    words: list[WordBreakdown] = field(default_factory=list)
    initials_value: int = 0
    # Breakdown strings for display
    total_breakdown: str = ""
    reduced_breakdown: str = ""


@dataclass
class GematriaRecord:
    """Input data for gematria calculation."""
    full_name: str
    systems: list[System] = field(default_factory=lambda: [System.SIMPLE, System.ORDINAL, System.REVERSE])
    state: GematriaState = GematriaState.DRAFT

    def validate(self) -> list[str]:
        """Return list of validation error messages."""
        errors: list[str] = []
        if not self.full_name.strip():
            errors.append("Name is required.")
        elif len(self.full_name.strip()) > 100:
            errors.append(f"Name too long ({len(self.full_name)} chars, max 100).")
        return errors


@dataclass
class GematriaResult:
    """Complete gematria analysis for selected systems."""
    name: str
    results: dict[System, SystemResult] = field(default_factory=dict)
    initials: str = field(init=False)

    def __post_init__(self) -> None:
        parts = self.name.strip().split()
        if len(parts) >= 2:
            self.initials = (parts[0][0] + parts[-1][0]).upper()
        else:
            # Single-word name: use first 3 letters
            alpha = [c for c in parts[0] if c.isalpha()]
            self.initials = "".join(alpha[:3]).upper() if alpha else "XXX"
