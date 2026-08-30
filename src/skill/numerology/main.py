"""Entry point for the Numerology Skill CLI.

Usage:
    python3 -m src.skill.numerology.main --input <file> [--format json|yaml|csv|natural-language]
                                          [--output-dir DIR] [--dry-run] [--yes]

Pipeline:
    parse → validate → compute (Pythagorean + Chaldean) → render SVG/HTML/JSON/MD

No external API calls — pure arithmetic on names and dates.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

from .calculations import compute_all
from .data_types import NumerologyRecord, NumerologyState
from .renderer import render_wheel
from .renderer_html import render_html
from .renderer_json import render_json
from .renderer_md import render_markdown


def _numerology_initials(name: str) -> str:
    """Generate 3-4 letter uppercase initials from a name for filenames.

    Uses the first 3-4 alphabetic characters of each word in the name.
    Single-word names get their first 3 letters (e.g., "Aria" → "ARIA", "Bristol" → "BRI").
    Multi-word names get first letter per word (e.g., "Jane Doe" → "JD").
    """
    parts = name.strip().split()
    chars: list[str] = []
    for part in parts:
        alpha = [c.lower() for c in part if c.isalpha()]
        if alpha:
            chars.append(alpha[0])

    result = "".join(chars).upper()
    # If single-word name, use first 3 letters of the word instead
    if len(parts) == 1 and len(result) < 3:
        alpha = [c for c in parts[0] if c.isalpha()]
        result = "".join(alpha[:3]).upper()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="numerology-skill",
        description="Generate a numerology report from name and birth date.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input file (JSON, YAML, CSV, or plain text).",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml", "csv", "natural-language"],
        default=None,
        help="Input format. Auto-detected from file extension if omitted.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory for the output files (default: current directory).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input and show computed numbers, then exit without rendering.",
    )
    return parser


def _detect_format(input_path: str) -> str:
    """Infer the input format from the file extension."""
    ext = input_path.rsplit(".", 1)[-1].lower() if "." in input_path else ""
    fmt_map = {
        "json": "json",
        "yaml": "yaml",
        "yml": "yaml",
        "csv": "csv",
        "txt": "natural-language",
    }
    return fmt_map.get(ext, "natural-language")


def _parse_input(args) -> tuple[NumerologyRecord, str]:
    """Parse input file into a NumerologyRecord."""
    fmt = args.format or _detect_format(args.input)
    text = Path(args.input).read_text(encoding="utf-8").strip()

    record: Optional[NumerologyRecord] = None

    if fmt in ("json", "yaml", "csv"):
        record = _parse_structured(text, fmt)
    else:
        record = _parse_natural_language(text)

    if record is None:
        print("Error: Could not parse input. Ensure you provide a name and date of birth.")
        sys.exit(1)

    return record, fmt


def _parse_structured(text: str, fmt: str) -> Optional[NumerologyRecord]:
    """Parse structured input (JSON/YAML/CSV)."""
    if fmt == "json":
        data = json.loads(text)
        name = data.get("name") or data.get("full_name", "")
        dob_str = data.get("date_of_birth") or data.get("dob", "")
    elif fmt == "yaml":
        # Minimal YAML parser (no dependency)
        data: dict[str, str] = {}
        for line in text.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                key, _, val = line.partition(":")
                data[key.strip()] = val.strip()
        name = data.get("name") or data.get("full_name", "")
        dob_str = data.get("date_of_birth") or data.get("dob", "")
    elif fmt == "csv":
        # Simple CSV: header line + one data line
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) < 2:
            return None
        headers = [h.strip() for h in lines[0].split(",")]
        values = [v.strip() for v in lines[1].split(",")]
        data = dict(zip(headers, values))
        name = data.get("name") or data.get("full_name", "")
        dob_str = data.get("date_of_birth") or data.get("dob", "")
    else:
        return None

    if not name or not dob_str:
        return None

    dob = _parse_date(dob_str)
    if dob is None:
        print(f"Error: Could not parse date '{dob_str}'. Use YYYY-MM-DD.")
        return None

    return NumerologyRecord(full_name=name, date_of_birth=dob)


def _parse_natural_language(text: str) -> Optional[NumerologyRecord]:
    """Parse natural language input.

    Looks for patterns like:
    - "Name: John Doe" or "My name is Aria" at the start
    - "DOB: 1990-01-15" or "born on January 15, 1990"
    """
    # Try to extract name (first line or after "Name:")
    lines = text.splitlines()
    name = ""
    dob_str = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for explicit fields
        if line_stripped.lower().startswith(("name:", "full name:", "person:")):
            name = line_stripped.split(":", 1)[1].strip()
        elif line_stripped.lower().startswith(("dob:", "date of birth:", "born:", "birth date:")):
            dob_str = line_stripped.split(":", 1)[1].strip()
        # Handle "My name is X" pattern
        elif re.match(r"(?:my\s+)?name\s+(?:is|are)\b", line_stripped, re.IGNORECASE):
            name = re.sub(r"(?:my\s+)?name\s+(?:is|are)\s*", "", line_stripped, flags=re.IGNORECASE).strip()
        # Handle "I am X" or "X was born" pattern at start of text
        elif not name and len(line_stripped) < 50 and re.match(r"[A-Z][a-zA-Z'-]+(?:\s+[a-zA-Z'-]+)*$", line_stripped):
            # Likely a single name or full name on its own line
            name = line_stripped

    # If no explicit DOB found, try to extract from full text
    if not dob_str:
        # Try ISO date format
        m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if m:
            dob_str = m.group(1)
        else:
            # Try "Month DD, YYYY" format
            m = re.search(
                r"(January|February|March|April|May|June|July|August|September|"
                r"October|November|December)\s+(\d{1,2}),?\s+(\d{4})",
                text,
                re.IGNORECASE,
            )
            if m:
                month_name = m.group(1)
                day = int(m.group(2))
                year = int(m.group(3))
                months = {
                    "january": 1, "february": 2, "march": 3, "april": 4,
                    "may": 5, "june": 6, "july": 7, "august": 8,
                    "september": 9, "october": 10, "november": 11, "december": 12,
                }
                month = months.get(month_name.lower())
                if month:
                    dob_str = f"{year}-{month:02d}-{day:02d}"

    # If name is still empty or looks like a full sentence, try to extract from first line
    if not name or " " in name and len(name) > 30:
        # Try "My name is X" pattern across the whole text
        m = re.search(r"(?:my\s+)?name\s+(?:is|are)\s+([A-Z][a-zA-Z'-]+(?:\s+[a-zA-Z'-]+)*)", text, re.IGNORECASE)
        if m:
            # Clean up name: stop at common non-name words
            raw_name = m.group(1)
            # Split and filter out non-name words
            name_words = []
            skip_words = {"and", "i", "was", "the", "a", "an", "in", "on", "at", "to", "for", "of", "my", "with"}
            for word in raw_name.split():
                if word.lower() not in skip_words:
                    name_words.append(word)
                else:
                    break  # Stop at first non-name word
            if name_words:
                name = " ".join(name_words)

    if not name or not dob_str:
        return None

    dob = _parse_date(dob_str)
    if dob is None:
        print(f"Error: Could not parse date '{dob_str}'.")
        return None

    return NumerologyRecord(full_name=name, date_of_birth=dob)


def _parse_date(s: str) -> Optional[date]:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        parts = s.strip().split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def _validate(record: NumerologyRecord) -> list[str]:
    """Validate the numerology record."""
    errors = []

    if not record.full_name.strip():
        errors.append("Name is required.")

    if record.date_of_birth > date.today():
        errors.append("Date of birth cannot be in the future.")

    if (date.today() - record.date_of_birth).days > 150 * 365:
        errors.append("Date of birth is more than 150 years ago.")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # --- Parse input ---
    record, fmt = _parse_input(args)
    dob_str = record.date_of_birth.isoformat() if record.date_of_birth else "(missing)"
    print(f"Parsed '{record.full_name}' ({fmt}) — DOB {dob_str}")

    # --- Validate ---
    errors = _validate(record)
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    record.state = NumerologyState.COMPUTED

    if args.dry_run:
        # Just compute and display numbers
        pyth, chald = compute_all(record)

        print("\n=== Pythagorean System ===")
        print(f"  Life Path:      {pyth.life_path}")
        print(f"  Expression:     {pyth.expression}")
        print(f"  Soul Urge:      {pyth.soul_urge}")
        print(f"  Personality:    {pyth.personality}")
        print(f"  Birthday:       {pyth.birthday}")

        print("\n=== Chaldean System ===")
        print(f"  Life Path:      {chald.life_path}")
        print(f"  Expression:     {chald.expression}")
        print(f"  Soul Urge:      {chald.soul_urge}")
        print(f"  Personality:    {chald.personality}")
        print(f"  Birthday:       {chald.birthday}")

        return 0

    # --- Render all output formats ---
    record.state = NumerologyState.READY_FOR_RENDERING
    out_dir = args.output_dir

    pyth, chald = compute_all(record)
    initials = _numerology_initials(record.full_name)

    # Generate SVG wheel
    svg_content = render_wheel(record.full_name, pyth, chald, width=600, height=750)
    svg_path = Path(out_dir) / f"{initials}_numerology.svg"
    svg_path.write_text(svg_content, encoding="utf-8")

    html_path = render_html(record, initials=initials, output_dir=out_dir)
    json_path = render_json(record, initials=initials, output_dir=out_dir)
    md_path = render_markdown(record, initials=initials, output_dir=out_dir)

    print(f"\nNumerology report for '{record.full_name}':")
    print(f"  SVG:   {svg_path}")
    print(f"  HTML:  {html_path}")
    print(f"  JSON:  {json_path}")
    print(f"  MD:    {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
