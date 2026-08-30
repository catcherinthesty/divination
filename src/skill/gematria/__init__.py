"""Gematria skill — deterministic letter-to-number analysis.

Computes gematria values for names and words using three English systems:
  - Simple (Pythagorean): cyclic A=1…I=9, J=1…R=9, S=1…Z=8
  - Full Ordinal:          straight A=1 … Z=26
  - Reverse Ordinal:       reverse A=26 … Z=1

Each system produces a total name value, a reduced single-digit (or master)
value, word-by-word breakdowns, and vowel / consonant splits.

No external API calls — pure arithmetic on letter values.
"""
