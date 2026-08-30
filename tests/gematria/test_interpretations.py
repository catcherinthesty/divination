"""Unit tests for Gematria interpretations."""

from __future__ import annotations

import pytest

from src.skill.gematria.data_types import System
from src.skill.gematria.interpretations import (
    CORE,
    FAMOUS_PAIRS,
    SYSTEM_NOTES,
    format_interpretation,
    get_core_interpretation,
    get_famous_pairs,
    get_system_note,
)


class TestCoreInterpretations:
    """Tests for core number interpretations."""

    def test_all_digits_covered(self):
        """All reduced values 1-9 should have interpretations."""
        for i in range(1, 10):
            interp = get_core_interpretation(i)
            assert "title" in interp
            assert "summary" in interp
            assert len(interp["title"]) > 0

    def test_master_numbers_covered(self):
        """Master numbers 11, 22, 33 should have interpretations."""
        for master in (11, 22, 33):
            interp = get_core_interpretation(master)
            assert "title" in interp
            title = interp.get("title", "")
            summary = interp.get("summary", "")
            assert "Master" in title or "master" in summary.lower()

    def test_unknown_number_falls_back(self):
        """Unknown number should reduce and look up."""
        # 108 → 1+0+8 = 9
        interp = get_core_interpretation(108)
        expected = get_core_interpretation(9)
        assert interp["title"] == expected["title"]

    def test_zero_returns_fallback(self):
        """Zero should return a fallback interpretation."""
        interp = get_core_interpretation(0)
        assert "title" in interp
        assert "summary" in interp


class TestFamousPairs:
    """Tests for famous pairs data."""

    def test_all_digits_have_pairs(self):
        """All reduced values 1-9 should have famous pairs."""
        for i in range(1, 10):
            pairs = get_famous_pairs(i)
            assert len(pairs) > 0

    def test_master_numbers_have_pairs(self):
        """Master numbers should also have famous pairs (via their reduced value)."""
        # 11 → 2, 22 → 4, 33 → 6 — get pairs for the master number itself
        # which falls back to its reduced value
        for master in (11, 22, 33):
            pairs = get_famous_pairs(master)
            assert len(pairs) > 0

    def test_famous_pair_values_are_ints(self):
        """Famous pair values should be integers."""
        pairs = get_famous_pairs(1)
        for val, desc in pairs:
            assert isinstance(val, int)
            assert isinstance(desc, str)


class TestSystemNotes:
    """Tests for system-specific notes."""

    def test_all_systems_have_notes(self):
        """All three systems should have descriptive notes."""
        for sys_obj in (System.SIMPLE, System.ORDINAL, System.REVERSE):
            note = get_system_note(sys_obj)
            assert "name" in note
            assert "description" in note

    def test_simple_system_description(self):
        note = get_system_note(System.SIMPLE)
        assert "Pythagorean" in note["name"] or "simple" in note["name"].lower()

    def test_ordinal_system_description(self):
        note = get_system_note(System.ORDINAL)
        assert "Ordinal" in note["name"]


class TestFormatInterpretation:
    """Tests for the format_interpretation function."""

    def test_returns_string(self):
        result = format_interpretation(1)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_includes_title_and_number(self):
        result = format_interpretation(7)
        interp = get_core_interpretation(7)
        assert interp["title"] in result
        assert "7" in result

    def test_includes_system_name(self):
        result = format_interpretation(3, system_name="Simple")
        assert "Simple" in result

    def test_master_number_formatting(self):
        result = format_interpretation(11)
        interp = get_core_interpretation(11)
        assert interp["title"] in result
