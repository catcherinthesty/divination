"""Unit tests for Gematria data types."""

from __future__ import annotations

import pytest

from src.skill.gematria.data_types import (
    GematriaRecord,
    GematriaResult,
    GematriaState,
    System,
    reduce_number,
)


class TestReduceNumber:
    """Tests for the reduce_number function."""

    def test_single_digit(self):
        assert reduce_number(5) == 5

    def test_two_digit(self):
        assert reduce_number(23) == 5  # 2+3=5

    def test_three_digit(self):
        assert reduce_number(199) == 1  # 1+9+9=19, 1+9=10, 1+0=1

    def test_master_11(self):
        assert reduce_number(11) == 11

    def test_master_22(self):
        assert reduce_number(22) == 22

    def test_master_33(self):
        assert reduce_number(33) == 33

    def test_reduce_to_master_11(self):
        assert reduce_number(29) == 11  # 2+9=11

    def test_reduce_via_non_master(self):
        assert reduce_number(46) == 1  # 4+6=10, 1+0=1

    def test_reduce_to_4(self):
        assert reduce_number(58) == 4  # 5+8=13, 1+3=4

    def test_large_number(self):
        assert reduce_number(999) == 9  # 9+9+9=27, 2+7=9


class TestGematriaRecord:
    """Tests for GematriaRecord dataclass."""

    def test_creation_minimal(self):
        record = GematriaRecord(full_name="Aria")
        assert record.full_name == "Aria"
        assert record.systems == [System.SIMPLE, System.ORDINAL, System.REVERSE]
        assert record.state == GematriaState.DRAFT

    def test_creation_with_systems(self):
        record = GematriaRecord(
            full_name="Test",
            systems=[System.SIMPLE],
        )
        assert len(record.systems) == 1
        assert System.SIMPLE in record.systems

    def test_validation_empty_name(self):
        record = GematriaRecord(full_name="")
        errors = record.validate()
        assert "Name is required." in errors

    def test_validation_whitespace_only(self):
        record = GematriaRecord(full_name="   ")
        errors = record.validate()
        assert "Name is required." in errors

    def test_validation_name_too_long(self):
        long_name = "A" * 101
        record = GematriaRecord(full_name=long_name)
        errors = record.validate()
        assert any("too long" in err for err in errors)

    def test_validation_valid_name(self):
        record = GematriaRecord(full_name="John Doe")
        errors = record.validate()
        assert errors == []


class TestGematriaResult:
    """Tests for GematriaResult dataclass."""

    def test_initials_multi_word(self):
        result = GematriaResult(name="Jane Doe")
        assert result.initials == "JD"

    def test_initials_single_word_short(self):
        result = GematriaResult(name="Aria")
        assert result.initials == "ARI"

    def test_initials_single_word_long(self):
        result = GematriaResult(name="Bristol")
        # First 3 letters: BRI
        assert result.initials == "BRI"

    def test_initials_with_hyphen(self):
        result = GematriaResult(name="Mary-Jane Watson")
        assert result.initials == "MW"

    def test_no_systems_empty_results(self):
        result = GematriaResult(name="Test")
        assert len(result.results) == 0

    def test_add_system_result(self):
        from src.skill.gematria.data_types import SystemResult

        result = GematriaResult(name="Aria")
        sr = SystemResult(system=System.SIMPLE, total=20, reduced=2)
        result.results[System.SIMPLE] = sr
        assert System.SIMPLE in result.results
        assert result.results[System.SIMPLE].total == 20
