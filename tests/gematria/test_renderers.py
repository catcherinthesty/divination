"""Unit tests for Gematria renderers (SVG, HTML, JSON, Markdown)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.skill.gematria.calculations import compute_all
from src.skill.gematria.data_types import GematriaRecord
from src.skill.gematria.renderer import render_gematria_wheel
from src.skill.gematria.renderer_html import render_html
from src.skill.gematria.renderer_json import render_json
from src.skill.gematria.renderer_md import render_markdown


@pytest.fixture()
def sample_record():
    """Create a GematriaRecord for testing."""
    return GematriaRecord(full_name="Aria")


@pytest.fixture()
def computed_result(sample_record):
    """Pre-compute gematria results for testing."""
    return compute_all(sample_record)


class TestSVGRenderer:
    """Tests for the SVG wheel renderer."""

    def test_svg_produces_valid_string(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        assert isinstance(svg, str)
        assert len(svg) > 0

    def test_svg_has_namespace(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_svg_has_title_with_name(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        assert "Gematria — Aria" in svg

    def test_svg_contains_all_three_systems(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        assert "Simple" in svg
        assert "Ordinal" in svg
        assert "Reverse" in svg

    def test_svg_contains_total_values(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        # Aria Simple total = 20
        assert ">20</text>" in svg or "20" in svg
        # Aria Ordinal total = 29
        assert ">29</text>" in svg or "29" in svg
        # Aria Reverse total = 79
        assert ">79</text>" in svg or "79" in svg

    def test_svg_contains_reduced_values(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        # Reduced values: Simple=2, Ordinal=11, Reverse=7
        assert ">2</text>" in svg
        assert ">11</text>" in svg
        assert ">7</text>" in svg

    def test_svg_is_deterministic(self, computed_result):
        """Same input produces identical SVG."""
        svg1 = render_gematria_wheel(computed_result)
        svg2 = render_gematria_wheel(computed_result)
        assert svg1 == svg2

    def test_svg_has_word_breakdowns(self, computed_result):
        svg = render_gematria_wheel(computed_result)
        assert "Aria" in svg


class TestHTMLRenderer:
    """Tests for the HTML renderer."""

    def test_html_produces_valid_string(self, sample_record, tmp_path):
        path = render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        assert isinstance(path, str)
        html_file = Path(path)
        assert html_file.exists()

    def test_html_contains_doctype(self, sample_record, tmp_path):
        render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        html_content = (tmp_path / "ARI_gematria.html").read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_content

    def test_html_contains_name(self, sample_record, tmp_path):
        render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        html_content = (tmp_path / "ARI_gematria.html").read_text(encoding="utf-8")
        assert "Aria" in html_content

    def test_html_contains_all_systems(self, sample_record, tmp_path):
        render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        html_content = (tmp_path / "ARI_gematria.html").read_text(encoding="utf-8")
        assert "Simple" in html_content
        assert "Ordinal" in html_content
        assert "Reverse" in html_content

    def test_html_contains_interpretation(self, sample_record, tmp_path):
        render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        html_content = (tmp_path / "ARI_gematria.html").read_text(encoding="utf-8")
        # Simple reduced=2: Balance & Partnership
        assert "Balance" in html_content or "Partnership" in html_content

    def test_html_contains_word_tables(self, sample_record, tmp_path):
        render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        html_content = (tmp_path / "ARI_gematria.html").read_text(encoding="utf-8")
        assert "<table" in html_content
        assert "Aria" in html_content


class TestJSONRenderer:
    """Tests for the JSON renderer."""

    def test_json_produces_valid_file(self, sample_record, tmp_path):
        path = render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_file = Path(path)
        assert json_file.exists()

    def test_json_is_valid_json(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        assert isinstance(data, dict)

    def test_json_contains_subject(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        assert "subject" in data
        assert data["subject"]["name"] == "Aria"

    def test_json_contains_all_systems(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        assert "systems" in data
        systems = data["systems"]
        assert "simple" in systems
        assert "ordinal" in systems
        assert "reverse" in systems

    def test_json_contains_word_data(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        simple_system = data["systems"]["simple"]
        assert "words" in simple_system
        assert len(simple_system["words"]) > 0

    def test_json_contains_interpretation(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        simple_system = data["systems"]["simple"]
        assert "interpretation" in simple_system
        assert "title" in simple_system["interpretation"]

    def test_json_contains_famous_pairs(self, sample_record, tmp_path):
        render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        json_content = (tmp_path / "ARI_gematria.json").read_text(encoding="utf-8")
        data = json.loads(json_content)
        simple_system = data["systems"]["simple"]
        # Reduced=2 for Simple system has famous pairs
        assert "famous_pairs" in simple_system


class TestMarkdownRenderer:
    """Tests for the Markdown renderer."""

    def test_md_produces_valid_file(self, sample_record, tmp_path):
        path = render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_file = Path(path)
        assert md_file.exists()

    def test_md_has_title(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "# Gematria Report: Aria" in md_content

    def test_md_has_overview_table(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "## Overview" in md_content
        assert "| System | Total | Reduced | Initials Value |" in md_content

    def test_md_has_all_systems(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "Simple" in md_content
        assert "Ordinal" in md_content
        assert "Reverse" in md_content

    def test_md_has_interpretations(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "### Interpretation:" in md_content

    def test_md_has_word_breakdown(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "### Word Breakdown" in md_content
        assert "| Word | Total | Reduced | Vowels | Consonants |" in md_content

    def test_md_has_summary(self, sample_record, tmp_path):
        render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        md_content = (tmp_path / "ARI_gematria.md").read_text(encoding="utf-8")
        assert "## Summary" in md_content
        assert "**Name:** Aria" in md_content


class TestRendererDeterminism:
    """Tests that renderers produce deterministic output."""

    def test_svg_deterministic(self, computed_result):
        svg1 = render_gematria_wheel(computed_result)
        svg2 = render_gematria_wheel(computed_result)
        assert svg1 == svg2

    def test_html_deterministic(self, sample_record, tmp_path):
        path1 = render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        content1 = Path(path1).read_text(encoding="utf-8")
        # Re-render to same location
        path2 = render_html(sample_record, initials="ARI", output_dir=str(tmp_path))
        content2 = Path(path2).read_text(encoding="utf-8")
        assert content1 == content2

    def test_json_deterministic(self, sample_record, tmp_path):
        path1 = render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        content1 = Path(path1).read_text(encoding="utf-8")
        data1 = json.loads(content1)
        # Re-render to same location
        path2 = render_json(sample_record, initials="ARI", output_dir=str(tmp_path))
        content2 = Path(path2).read_text(encoding="utf-8")
        data2 = json.loads(content2)
        assert data1 == data2

    def test_md_deterministic(self, sample_record, tmp_path):
        path1 = render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        content1 = Path(path1).read_text(encoding="utf-8")
        # Re-render to same location
        path2 = render_markdown(sample_record, initials="ARI", output_dir=str(tmp_path))
        content2 = Path(path2).read_text(encoding="utf-8")
        assert content1 == content2
