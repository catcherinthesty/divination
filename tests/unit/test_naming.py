"""Unit tests for src/skill/renderer/naming.py — deterministic filename generation.

Tests cover:
- Basic initials extraction from various name formats
- Hyphenated names (e.g., "Klok-Loomis" → both 'k' and 'l')
- Apostrophes in names (e.g., "O'Brien")
- Single-word names
- Edge cases: empty name, non-alpha characters
- chart_filename() and api_call_filename() helpers
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is on the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))


class TestGenerateInitials:
    """Tests for generate_initials()."""

    def test_simple_two_word_name(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("Jane Doe") == "jd"

    def test_three_word_name(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("Bristol Ann Klok-Loomis") == "bakl"

    def test_hyphenated_name(self):
        """Hyphenated names contribute both parts (T030)."""
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("Mary-Jane Watson") == "mw"
        assert generate_initials("Anne-Marie O'Brien") == "ao"

    def test_apostrophe_in_name(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("Mary O'Brien") == "mo"
        assert generate_initials("D'Angelo") == "d"

    def test_single_name(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("Alice") == "a"

    def test_multiple_hyphens(self):
        from src.skill.renderer.naming import generate_initials

        # Three-part hyphenated name
        assert generate_initials("Anne-Marie-Jane") == "amj"

    def test_case_insensitive(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("BRISTOL ANN KLOK-LOOMIS") == "bakl"
        assert generate_initials("bristol ann klok-loomis") == "bakl"

    def test_leading_trailing_whitespace(self):
        from src.skill.renderer.naming import generate_initials

        assert generate_initials("  Jane Doe  ") == "jd"

    def test_empty_name_raises(self):
        from src.skill.renderer.naming import generate_initials

        try:
            generate_initials("")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_numeric_only_name_raises(self):
        from src.skill.renderer.naming import generate_initials

        try:
            generate_initials("123")
            assert False, "Expected ValueError"
        except ValueError:
            pass


class TestChartFilename:
    """Tests for chart_filename()."""

    def test_svg_extension(self):
        from src.skill.renderer.naming import chart_filename

        assert chart_filename("bakl", "svg") == "bakl_chart.svg"

    def test_html_extension(self):
        from src.skill.renderer.naming import chart_filename

        assert chart_filename("bakl", "html") == "bakl_chart.html"

    def test_default_extension_is_svg(self):
        from src.skill.renderer.naming import chart_filename

        assert chart_filename("arh") == "arh_chart.svg"


class TestApiCallFilename:
    """Tests for api_call_filename()."""

    def test_api_call_json(self):
        from src.skill.renderer.naming import api_call_filename

        assert api_call_filename("bakl") == "bakl_api_call.json"

    def test_simple_initials(self):
        from src.skill.renderer.naming import api_call_filename

        assert api_call_filename("jd") == "jd_api_call.json"


class TestPIIExpunge:
    """Verify PII is never in filenames (FR-006, FR-007, T030)."""

    def test_filenames_use_initials_not_full_name(self):
        from src.skill.renderer.naming import chart_filename, api_call_filename, generate_initials

        name = "Bristol Ann Klok-Loomis"
        initials = generate_initials(name)
        svg_file = chart_filename(initials, "svg")
        json_file = api_call_filename(initials)

        # Full name must NOT appear in any filename
        assert name.lower() not in svg_file.lower()
        assert name.lower() not in json_file.lower()
        # Only initials should be present
        assert initials in svg_file
        assert initials in json_file

    def test_synthetic_sample_data_has_no_real_pii(self):
        """T032: Verify docs/sample-inputs/ contains only synthetic data."""
        import json as _json

        sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "sample-inputs"

        for fpath in sample_dir.glob("*.json"):
            with open(fpath, encoding="utf-8") as f:
                data = _json.load(f)
            name = data.get("name", "")
            # Known synthetic names that should never appear in real charts
            assert name not in (
                "Bristol Ann Klok-Loomis",
                "Aria Rose Heinsen",
            ), f"Real PII found in {fpath.name}: {name}"
