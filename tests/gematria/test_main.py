"""Unit tests for Gematria CLI (main.py)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.skill.gematria.main import (
    _detect_format,
    _parse_input,
    _parse_natural_language,
    _parse_structured,
    _validate,
    main,
)
from src.skill.gematria.data_types import GematriaRecord


class TestFormatDetection:
    """Tests for format auto-detection."""

    def test_json_extension(self):
        assert _detect_format("data/test.json") == "json"

    def test_yaml_extension(self):
        assert _detect_format("data/test.yaml") == "yaml"

    def test_yml_extension(self):
        assert _detect_format("data/test.yml") == "yaml"

    def test_csv_extension(self):
        assert _detect_format("data/test.csv") == "csv"

    def test_txt_extension(self):
        assert _detect_format("data/test.txt") == "natural-language"

    def test_unknown_extension_defaults_to_nl(self):
        assert _detect_format("data/test.xyz") == "natural-language"


class TestStructuredParsing:
    """Tests for structured input parsing."""

    def test_parse_json_simple(self):
        text = json.dumps({"name": "Aria"})
        record = _parse_structured(text, "json")
        assert record is not None
        assert record.full_name == "Aria"

    def test_parse_json_full_name_key(self):
        text = json.dumps({"full_name": "Bristol Ann Klok-Loomis"})
        record = _parse_structured(text, "json")
        assert record is not None
        assert record.full_name == "Bristol Ann Klok-Loomis"

    def test_parse_yaml(self):
        text = "name: Aria\nfull_name: Aria Rose\n"
        record = _parse_structured(text, "yaml")
        assert record is not None
        assert record.full_name == "Aria"

    def test_parse_csv(self):
        text = "name,date_of_birth\nAria,1995-03-15\n"
        record = _parse_structured(text, "csv")
        assert record is not None
        assert record.full_name == "Aria"

    def test_parse_csv_full_name(self):
        text = "full_name,date_of_birth\nBristol Ann Klok-Loomis,1988-07-22\n"
        record = _parse_structured(text, "csv")
        assert record is not None
        assert record.full_name == "Bristol Ann Klok-Loomis"

    def test_parse_json_missing_name(self):
        text = json.dumps({"date": "1995-03-15"})
        record = _parse_structured(text, "json")
        assert record is None

    def test_parse_csv_too_few_lines(self):
        text = "name"
        record = _parse_structured(text, "csv")
        assert record is None


class TestNaturalLanguageParsing:
    """Tests for natural language input parsing."""

    def test_name_field(self):
        text = "Name: Aria Rose"
        record = _parse_natural_language(text)
        assert record is not None
        assert record.full_name == "Aria Rose"

    def test_full_name_field(self):
        text = "Full name: Bristol Ann Klok-Loomis"
        record = _parse_natural_language(text)
        assert record is not None
        assert record.full_name == "Bristol Ann Klok-Loomis"

    def test_my_name_is_pattern(self):
        text = "My name is Aria and I was born in 1995."
        record = _parse_natural_language(text)
        assert record is not None
        assert record.full_name == "Aria"

    def test_first_line_as_name(self):
        text = "Jane Doe\nSome other text here"
        record = _parse_natural_language(text)
        assert record is not None
        assert record.full_name == "Jane Doe"

    def test_empty_text(self):
        record = _parse_natural_language("")
        assert record is None


class TestValidation:
    """Tests for input validation."""

    def test_valid_name(self):
        record = GematriaRecord(full_name="Aria")
        errors = _validate(record)
        assert errors == []

    def test_empty_name(self):
        record = GematriaRecord(full_name="")
        errors = _validate(record)
        assert "Name is required." in errors

    def test_whitespace_name(self):
        record = GematriaRecord(full_name="   ")
        errors = _validate(record)
        assert "Name is required." in errors

    def test_long_name(self):
        long_name = "A" * 101
        record = GematriaRecord(full_name=long_name)
        errors = _validate(record)
        assert any("too long" in err for err in errors)


class TestCLI:
    """Tests for the CLI entry point."""

    def test_dry_run_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json.dumps({"name": "Aria"}))
            f.flush()
            result = main(["--input", f.name, "--dry-run"])
        Path(f.name).unlink()
        assert result == 0

    def test_dry_run_csv(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name\nAria\n")
            f.flush()
            result = main(["--input", f.name, "--dry-run"])
        Path(f.name).unlink()
        assert result == 0

    def test_dry_run_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("name: Aria\n")
            f.flush()
            result = main(["--input", f.name, "--dry-run"])
        Path(f.name).unlink()
        assert result == 0

    def test_dry_run_natural_language(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Name: Aria\n")
            f.flush()
            result = main(["--input", f.name, "--dry-run"])
        Path(f.name).unlink()
        assert result == 0

    def test_full_render_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.json"
            input_file.write_text(json.dumps({"name": "Aria"}))
            result = main(["--input", str(input_file), "--output-dir", tmpdir])
            assert result == 0
            # Check all output files were created
            assert (Path(tmpdir) / "ARI_gematria.svg").exists()
            assert (Path(tmpdir) / "ARI_gematria.html").exists()
            assert (Path(tmpdir) / "ARI_gematria.json").exists()
            assert (Path(tmpdir) / "ARI_gematria.md").exists()

    def test_full_render_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.csv"
            input_file.write_text("name\nBristol\n")
            result = main(["--input", str(input_file), "--output-dir", tmpdir])
            assert result == 0
            # Check output files were created with correct initials
            assert (Path(tmpdir) / "BRI_gematria.svg").exists()

    def test_invalid_input_returns_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = Path(tmpdir) / "test.json"
            input_file.write_text(json.dumps({"invalid": "data"}))
            with pytest.raises(SystemExit) as exc_info:
                main(["--input", str(input_file), "--dry-run"])
            assert exc_info.value.code == 1

    def test_missing_input_file(self):
        with pytest.raises(FileNotFoundError):
            main(["--input", "/nonexistent/file.json", "--dry-run"])
