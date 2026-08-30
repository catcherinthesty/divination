"""Data types for the Numerology skill."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class System(Enum):
    """Numerology calculation system."""
    PYTHAGOREAN = "pythagorean"
    CHALDEAN = "chaldean"


class NumerologyState(Enum):
    DRAFT = "draft"
    VALIDATING = "validating"
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
class NumerologyRecord:
    """Input data for numerology calculation."""
    full_name: str
    date_of_birth: date
    state: NumerologyState = NumerologyState.DRAFT

    def validate(self) -> list[str]:
        """Return list of validation error messages."""
        errors: list[str] = []
        if not self.full_name.strip():
            errors.append("Name is required.")
        elif len(self.full_name.strip()) > 100:
            errors.append(f"Name too long ({len(self.full_name)} chars, max 100).")
        if self.date_of_birth > date.today():
            errors.append("Date of birth cannot be in the future.")
        elif (date.today() - self.date_of_birth).days > 150 * 365:
            errors.append("Date of birth is more than 150 years ago.")
        return errors


@dataclass
class CoreNumbers:
    """All five core numerology numbers for one system."""
    system: System
    life_path: int
    expression: int
    soul_urge: int
    personality: int
    birthday: int
    # Breakdowns for display
    life_path_breakdown: str = ""
    expression_breakdown: str = ""
    soul_urge_breakdown: str = ""
    personality_breakdown: str = ""
    birthday_breakdown: str = ""


@dataclass
class NumerologyResult:
    """Complete numerology analysis for both systems."""
    name: str
    birth_date: date
    pythagorean: CoreNumbers
    chaldean: CoreNumbers
    initials: str = field(init=False)

    def __post_init__(self) -> None:
        parts = self.name.strip().split()
        if len(parts) >= 2:
            self.initials = (parts[0][0] + parts[-1][0]).upper()
        else:
            self.initials = self.name[:3].upper()
