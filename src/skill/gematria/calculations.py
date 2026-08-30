"""Core gematria calculations — three English systems.

All computation is deterministic: same input → same output, no API calls.

Systems:
  - Simple (Pythagorean): A=1,B=2,…,I=9,J=1,…,R=9,S=1,…,Z=8  (cyclic 1-9)
  - Full Ordinal:         A=1,B=2,…,Z=26                      (straight alphabet)
  - Reverse Ordinal:      A=26,B=25,…,Z=1                     (reverse alphabet)

Each system computes:
  - Total name value (sum of all letter values)
  - Reduced value (recursive digit sum → 1-9 or master 11/22/33)
  - Word-by-word breakdowns
  - Vowel and consonant totals
  - Initials value
"""

from __future__ import annotations

from .data_types import (
    MASTER_NUMBERS,
    GematriaRecord,
    GematriaResult,
    System,
    SystemResult,
    WordBreakdown,
    reduce_number,
)

# ── Letter value mappings ────────────────────────────────────────────

SIMPLE: dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 6, "P": 7, "Q": 8, "R": 9,
    "S": 1, "T": 2, "U": 3, "V": 4, "W": 5, "X": 6, "Y": 7, "Z": 8,
}

ORDINAL: dict[str, int] = {chr(i + 65): i + 1 for i in range(26)}

REVERSE: dict[str, int] = {chr(i + 65): 27 - (i + 1) for i in range(26)}
# A=26, B=25, C=24, … Z=1

SYSTEM_MAP: dict[System, dict[str, int]] = {
    System.SIMPLE: SIMPLE,
    System.ORDINAL: ORDINAL,
    System.REVERSE: REVERSE,
}

VOWELS = set("AEIOU")


def _sum_word(word: str, values: dict[str, int]) -> tuple[int, list[tuple[str, int]], int, int]:
    """Compute total, letter-value pairs, vowel total, consonant total for a word.

    Returns (total, [(letter, value), …], vowel_total, consonant_total).
    """
    pairs: list[tuple[str, int]] = []
    vowel_total = 0
    consonant_total = 0

    for ch in word.upper():
        if ch in values:
            v = values[ch]
            pairs.append((ch, v))
            if ch in VOWELS:
                vowel_total += v
            else:
                consonant_total += v

    total = vowel_total + consonant_total
    return total, pairs, vowel_total, consonant_total


def _reduce_breakdown(total: int) -> tuple[int, str]:
    """Reduce a number and build a breakdown string.

    Returns (reduced_number, breakdown_string).
    """
    if total <= 9:
        return total, str(total)
    parts = [str(total)]
    current = total
    while current not in MASTER_NUMBERS and current > 9:
        current = sum(int(d) for d in str(current))
        parts.append(str(current))
    reduced = current if current in MASTER_NUMBERS else reduce_number(total)
    return reduced, " → ".join(parts)


def compute_system(record: GematriaRecord, system: System) -> SystemResult:
    """Compute all gematria values for one system.

    Processes each word in the name separately, then combines totals.
    Also computes initials value and vowel/consonant splits.
    """
    values = SYSTEM_MAP[system]
    name = record.full_name.strip()
    words = [w for w in name.split() if w]  # filter empty strings

    word_breakdowns: list[WordBreakdown] = []
    total_vowels = 0
    total_consonants = 0
    all_pairs: list[tuple[str, int]] = []

    for word in words:
        word_total, pairs, vowel_t, cons_t = _sum_word(word, values)
        reduced, rb = _reduce_breakdown(word_total)
        wb = WordBreakdown(
            word=word,
            total=word_total,
            reduced=reduced,
            vowel_total=vowel_t,
            consonant_total=cons_t,
            letter_values=pairs,
        )
        word_breakdowns.append(wb)
        total_vowels += vowel_t
        total_consonants += cons_t
        all_pairs.extend(pairs)

    grand_total = sum(w.total for w in word_breakdowns)
    reduced, rb = _reduce_breakdown(grand_total)

    # Build total breakdown string
    if all_pairs:
        expr_parts = [f"{ch}={v}" for ch, v in all_pairs if v > 0]
        total_breakdown = f"{name} = {' + '.join(expr_parts)} = {grand_total}{f' → {reduced}' if grand_total != reduced else ''}"
    else:
        total_breakdown = f"{name} = 0"

    # Initials value (sum of initials letter values)
    parts = name.split()
    initial_letters = []
    for p in parts[:3]:  # up to first 3 words
        alpha = [c for c in p if c.isalpha()]
        if alpha:
            initial_letters.append(alpha[0].upper())
    initials_total, _, _, _ = _sum_word("".join(initial_letters), values)

    return SystemResult(
        system=system,
        total=grand_total,
        reduced=reduced,
        words=word_breakdowns,
        initials_value=initials_total,
        total_breakdown=total_breakdown,
        reduced_breakdown=rb,
    )


def compute_all(record: GematriaRecord) -> GematriaResult:
    """Compute gematria for all requested systems.

    Returns a GematriaResult with SystemResult keyed by System enum.
    """
    result = GematriaResult(name=record.full_name.strip())
    for system in record.systems:
        result.results[system] = compute_system(record, system)
    return result
