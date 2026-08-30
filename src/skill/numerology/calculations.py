"""Core numerology calculations — Pythagorean & Chaldean systems.

All computation is deterministic: same input → same output, no API calls.
"""

from __future__ import annotations

from .data_types import (
    MASTER_NUMBERS,
    CoreNumbers,
    NumerologyRecord,
    System,
    reduce_number,
)

# ── Pythagorean letter values ────────────────────────────────────────
PYTHAGOREAN = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

# ── Chaldean letter values ───────────────────────────────────────────
CHALDEAN = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5,
    "I": 1, "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8,
    "Q": 1, "R": 2, "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 5,
    "Y": 1, "Z": 7,
}

SYSTEM_MAP = {
    System.PYTHAGOREAN: PYTHAGOREAN,
    System.CHALDEAN: CHALDEAN,
}


def _sum_letters(name: str, values: dict[str, int]) -> tuple[int, list[tuple[str, int]]]:
    """Sum letter values for a name, returning (total, [(letter, value), ...])."""
    pairs: list[tuple[str, int]] = []
    total = 0
    for ch in name.upper():
        if ch in values:
            v = values[ch]
            total += v
            pairs.append((ch, v))
    return total, pairs


def _sum_date_parts(year: int) -> tuple[int, list[tuple[str, int]]]:
    """Reduce a birth date (DD MM YYYY) to Life Path number.

    Returns (reduced_number, [(label, digit_value), ...]).
    Uses the method: sum all digits of day+month+year, then reduce.
    """
    pairs: list[tuple[str, int]] = []
    total = 0
    for d in str(year):
        v = int(d)
        total += v
        pairs.append((f"{year}[{d}]", v))
    for d in str(year)[:4]:
        pass  # already counted above
    return total, pairs


def compute_life_path(dob: date) -> tuple[int, str]:
    """Compute Life Path number from birth date.

    Method: sum all digits of day + month + year, then reduce to single digit or master.
    Returns (number, breakdown_string).
    """
    # Sum all individual digits
    total = sum(int(d) for d in str(dob.year)) + \
            sum(int(d) for d in str(dob.month)) + \
            sum(int(d) for d in str(dob.day))

    original = total
    reduced = reduce_number(total)

    all_digits = ''.join([str(dob.year), str(dob.month), str(dob.day)])
    breakdown = f"{dob.year}+{dob.month}+{dob.day} = {sum(int(d) for d in all_digits)}"
    if original != reduced:
        breakdown += f" → {original} → {reduced}"

    return reduced, breakdown


def compute_expression(name: str, system: System) -> tuple[int, str]:
    """Compute Expression (Destiny) number from full birth name.

    Sum of all letter values in the full name at birth.
    Returns (number, breakdown_string).
    """
    values = SYSTEM_MAP[system]
    total, pairs = _sum_letters(name, values)
    reduced = reduce_number(total)

    if not pairs:
        return 0, f"{name} → 0"

    # Build readable breakdown
    expr_parts = [f"{ch}={v}" for ch, v in pairs if v > 0]
    breakdown = f"{name} = {' + '.join(expr_parts)} = {total}"
    if total != reduced:
        breakdown += f" → {reduced}"

    return reduced, breakdown


def compute_soul_urge(name: str, system: System) -> tuple[int, str]:
    """Compute Soul Urge (Heart's Desire) number from vowels in name.

    Returns (number, breakdown_string).
    """
    values = SYSTEM_MAP[system]
    vowels = set("AEIOU")

    pairs: list[tuple[str, int]] = []
    for ch in name.upper():
        if ch in vowels and ch in values:
            pairs.append((ch, values[ch]))

    total = sum(v for _, v in pairs)
    reduced = reduce_number(total) if total > 0 else 0

    expr_parts = [f"{ch}={v}" for ch, v in pairs]
    breakdown = f"Vowels({name}) = {' + '.join(expr_parts)} = {total}"
    if total != reduced:
        breakdown += f" → {reduced}"

    return reduced, breakdown


def compute_personality(name: str, system: System) -> tuple[int, str]:
    """Compute Personality number from consonants in name.

    Returns (number, breakdown_string).
    """
    values = SYSTEM_MAP[system]
    vowels = set("AEIOU")

    pairs: list[tuple[str, int]] = []
    for ch in name.upper():
        if ch not in vowels and ch in values:
            pairs.append((ch, values[ch]))

    total = sum(v for _, v in pairs)
    reduced = reduce_number(total) if total > 0 else 0

    expr_parts = [f"{ch}={v}" for ch, v in pairs]
    breakdown = f"Consonants({name}) = {' + '.join(expr_parts)} = {total}"
    if total != reduced:
        breakdown += f" → {reduced}"

    return reduced, breakdown


def compute_birthday_number(day: int) -> tuple[int, str]:
    """Compute Birthday number from day of month.

    Returns (number, breakdown_string).
    """
    reduced = reduce_number(day)
    breakdown = f"{day} → {reduced}" if day != reduced else str(day)
    return reduced, breakdown


def compute_all(record: NumerologyRecord) -> tuple[CoreNumbers, CoreNumbers]:
    """Compute all five core numbers for both systems.

    Returns (pythagorean_core, chaldean_core).
    """
    name = record.full_name.strip()
    dob = record.date_of_birth

    # Life Path is the same in both systems (date-based)
    lp_num, lp_break = compute_life_path(dob)

    results: dict[System, CoreNumbers] = {}

    for system in (System.PYTHAGOREAN, System.CHALDEAN):
        expr_num, expr_break = compute_expression(name, system)
        su_num, su_break = compute_soul_urge(name, system)
        pe_num, pe_break = compute_personality(name, system)
        bd_num, bd_break = compute_birthday_number(dob.day)

        results[system] = CoreNumbers(
            system=system,
            life_path=lp_num,
            expression=expr_num,
            soul_urge=su_num,
            personality=pe_num,
            birthday=bd_num,
            life_path_breakdown=lp_break,
            expression_breakdown=expr_break,
            soul_urge_breakdown=su_break,
            personality_breakdown=pe_break,
            birthday_breakdown=bd_break,
        )

    return results[System.PYTHAGOREAN], results[System.CHALDEAN]
