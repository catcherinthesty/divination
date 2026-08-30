"""Unit tests for Gematria calculations."""

from __future__ import annotations

import pytest

from src.skill.gematria.calculations import (
    compute_all,
    compute_system,
    reduce_number,
)
from src.skill.gematria.data_types import GematriaRecord, System


class TestSimpleSystem:
    """Tests for Simple (Pythagorean) system."""

    def test_aria_simple(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_system(record, System.SIMPLE)
        assert result.total == 20  # A(1)+R(9)+I(9)+A(1)
        assert result.reduced == 2  # 20 → 2+0=2

    def test_ordinal_bristol(self):
        record = GematriaRecord(full_name="Bristol")
        result = compute_system(record, System.ORDINAL)
        assert result.total == 95  # B(2)+R(18)+I(9)+S(19)+T(20)+O(15)+L(12)
        assert result.reduced == 5  # 9+5=14→1+4=5

    def test_reverse_aria(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_system(record, System.REVERSE)
        assert result.total == 79  # A(26)+R(9)+I(18)+A(26)
        assert result.reduced == 7  # 7+9=16→1+6=7


class TestVowelConsonantSplits:
    """Tests for vowel/consonant totals."""

    def test_vowels_aria_simple(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_system(record, System.SIMPLE)
        # A(1)+I(9)+A(1) = 11 vowels
        assert result.words[0].vowel_total == 11

    def test_consonants_aria_simple(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_system(record, System.SIMPLE)
        # R(9) = 9 consonants
        assert result.words[0].consonant_total == 9

    def test_vowels_ordinal_bristol(self):
        record = GematriaRecord(full_name="Bristol")
        result = compute_system(record, System.ORDINAL)
        # I(9)+O(15) = 24 vowels
        assert result.words[0].vowel_total == 24

    def test_consonants_ordinal_bristol(self):
        record = GematriaRecord(full_name="Bristol")
        result = compute_system(record, System.ORDINAL)
        # B(2)+R(18)+S(19)+T(20)+L(12) = 71 consonants
        assert result.words[0].consonant_total == 71


class TestWordBreakdowns:
    """Tests for multi-word name handling."""

    def test_multi_word_simple(self):
        record = GematriaRecord(full_name="Jane Doe")
        result = compute_system(record, System.SIMPLE)
        assert len(result.words) == 2
        # Jane: J(1)+A(1)+N(5)+E(5) = 12 → 3
        jane_word = result.words[0]
        assert jane_word.word == "Jane"
        assert jane_word.total == 12
        assert jane_word.reduced == 3

    def test_multi_word_ordinal(self):
        record = GematriaRecord(full_name="John Doe")
        result = compute_system(record, System.ORDINAL)
        assert len(result.words) == 2
        # John: J(10)+O(15)+H(8)+N(14) = 47 → 11
        john_word = result.words[0]
        assert john_word.total == 47
        assert john_word.reduced == 11

    def test_total_is_sum_of_words(self):
        record = GematriaRecord(full_name="Jane Doe")
        result = compute_system(record, System.SIMPLE)
        word_totals = sum(w.total for w in result.words)
        assert result.total == word_totals


class TestInitialsValue:
    """Tests for initials gematria values."""

    def test_aria_initials_simple(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_system(record, System.SIMPLE)
        # Initials: A → A(1) = 1
        assert result.initials_value == 1

    def test_bristol_initials_simple(self):
        record = GematriaRecord(full_name="Bristol")
        result = compute_system(record, System.SIMPLE)
        # Initials: B → B(2) = 2
        assert result.initials_value == 2


class TestComputeAll:
    """Tests for compute_all function."""

    def test_all_three_systems(self):
        record = GematriaRecord(full_name="Test")
        result = compute_all(record)
        assert len(result.results) == 3
        assert System.SIMPLE in result.results
        assert System.ORDINAL in result.results
        assert System.REVERSE in result.results

    def test_custom_systems(self):
        record = GematriaRecord(
            full_name="Test",
            systems=[System.SIMPLE, System.ORDINAL],
        )
        result = compute_all(record)
        assert len(result.results) == 2
        assert System.REVERSE not in result.results

    def test_result_has_initials(self):
        record = GematriaRecord(full_name="Aria")
        result = compute_all(record)
        assert result.initials == "ARI"

    def test_deterministic(self):
        """Same input always produces same output."""
        record = GematriaRecord(full_name="Aria")
        result1 = compute_all(record)
        result2 = compute_all(record)
        for sys_obj in System:
            if sys_obj in result1.results and sys_obj in result2.results:
                assert result1.results[sys_obj].total == result2.results[sys_obj].total
                assert result1.results[sys_obj].reduced == result2.results[sys_obj].reduced
