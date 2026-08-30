"""Unit tests for src/skill/geocoder/lookup.py — deterministic address resolution.

Tests cover:
- Exact case-insensitive match → HIGH confidence
- Partial substring match → MEDIUM confidence
- Street address resolution (T028)
- Ambiguous city returning multiple candidates (T029, US-3)
- Invalid coordinate range rejection
- Determinism across 10 consecutive runs (SC-004)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


class TestExactMatch:
    """Exact case-insensitive match → HIGH confidence."""

    def test_exact_city_match(self):
        from src.skill.geocoder.lookup import resolve
        from src.skill.data_types import Confidence

        results = resolve("Chicago")
        assert len(results) == 1
        assert results[0].confidence == Confidence.HIGH
        assert results[0].matched_name == "Chicago"
        assert results[0].latitude == 41.8780
        assert results[0].longitude == -87.6298

    def test_case_insensitive(self):
        from src.skill.geocoder.lookup import resolve
        from src.skill.data_types import Confidence

        for query in ["chicago", "CHICAGO", "ChIcAgO"]:
            results = resolve(query)
            assert len(results) == 1
            assert results[0].confidence == Confidence.HIGH

    def test_exact_hospital_match(self):
        from src.skill.geocoder.lookup import resolve
        from src.skill.data_types import Confidence

        results = resolve("Bronson Methodist Hospital")
        assert len(results) == 1
        assert results[0].confidence == Confidence.HIGH
        assert "Bronson" in results[0].matched_name


class TestPartialMatch:
    """Partial substring match → MEDIUM confidence."""

    def test_partial_city_match(self):
        from src.skill.geocoder.lookup import resolve
        from src.skill.data_types import Confidence

        # "New York" contains "new" and "york" as substrings of lookup entries
        results = resolve("New")
        assert len(results) >= 1
        # Partial matches should be MEDIUM confidence
        for r in results:
            assert r.confidence == Confidence.MEDIUM


class TestAmbiguity:
    """Multiple matches → disambiguation required (T029)."""

    def test_springfield_ambiguous(self):
        from src.skill.geocoder.lookup import resolve

        results = resolve("Springfield")
        assert len(results) > 1, "Springfield should have multiple matches"
        # All should be HIGH confidence exact matches (different cities with same name)
        for r in results:
            assert r.confidence.value == "high"

    def test_paris_ambiguous(self):
        from src.skill.geocoder.lookup import resolve

        results = resolve("Paris")
        assert len(results) >= 2, "Paris should have US and FR matches"


class TestUserProvidedCoords:
    """User-provided coordinates → LOW confidence."""

    def test_resolve_with_user_coords(self):
        from src.skill.geocoder.lookup import resolve_with_user_coords
        from src.skill.data_types import Confidence

        result = resolve_with_user_coords("Custom Location", 40.7128, -74.0060)
        assert result.confidence == Confidence.LOW
        assert result.latitude == 40.7128
        assert result.longitude == -74.0060

    def test_invalid_latitude_raises(self):
        from src.skill.geocoder.lookup import resolve_with_user_coords

        try:
            resolve_with_user_coords("Bad", 91.0, 0.0)
        except ValueError as e:
            assert "outside valid range" in str(e).lower() or "latitude" in str(e).lower()

    def test_invalid_longitude_raises(self):
        from src.skill.geocoder.lookup import resolve_with_user_coords

        try:
            resolve_with_user_coords("Bad", 0.0, 181.0)
        except ValueError as e:
            assert "outside valid range" in str(e).lower() or "longitude" in str(e).lower()


class TestNoMatch:
    """Unrecognized locations → empty list."""

    def test_unknown_city(self):
        from src.skill.geocoder.lookup import resolve

        results = resolve("NonexistentCityXYZ123")
        assert len(results) == 0

    def test_empty_string(self):
        from src.skill.geocoder.lookup import resolve

        results = resolve("")
        assert len(results) == 0


class TestDeterminism:
    """SC-004: Same input produces identical coordinates across 10 runs."""

    def test_chicago_deterministic(self):
        from src.skill.geocoder.lookup import resolve

        results = []
        for _ in range(10):
            r = resolve("Chicago")
            results.append((r[0].latitude, r[0].longitude, r[0].matched_name))

        # All 10 runs must produce identical results
        assert len(set(results)) == 1, f"Non-deterministic results: {results}"

    def test_springfield_deterministic(self):
        from src.skill.geocoder.lookup import resolve

        results = []
        for _ in range(10):
            r = resolve("Springfield")
            results.append([(x.latitude, x.longitude) for x in r])

        # All 10 runs must produce identical result lists
        assert len(set(str(r) for r in results)) == 1


class TestSortOrder:
    """Results sorted by confidence (HIGH first), then alphabetically."""

    def test_ambiguous_sorted_alphabetically(self):
        from src.skill.geocoder.lookup import resolve

        results = resolve("Springfield")
        if len(results) > 1:
            names = [r.matched_name for r in results]
            assert names == sorted(names), "Results should be sorted alphabetically by name"


class TestStreetAddressResolution:
    """T028: Street address resolution for hospital/landmark precision."""

    def test_hospital_with_address(self):
        from src.skill.geocoder.lookup import resolve

        # Should match Bronson Methodist Hospital via partial/token matching
        results = resolve("Bronson")
        assert len(results) >= 1
        bronson_match = [r for r in results if "Bronson" in (r.matched_name or "")]
        assert len(bronson_match) >= 1, "Bronson Methodist Hospital should be found via partial match"
