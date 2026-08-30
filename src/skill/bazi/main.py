"""Entry point for the Ba Zi (Four Pillars of Destiny) Skill CLI.

Usage:
    python3 -m src.skill.bazi.main --input <file> [--format json|yaml|csv|natural-language]
                                    [--output-dir DIR] --gender male|female [--dry-run]

Pipeline:
    parse → validate → compute four pillars (year/month/day/hour) → render SVG/HTML/JSON/MD

No external API calls — pure arithmetic on dates and times using the Chinese sexagenary cycle.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

from .data_types import BaziRecord, Gender
from .renderer_html import render_html
from .renderer_json import render_json
from .renderer_md import render_markdown


def generate_initials(name: str) -> str:
    """Generate deterministic initials from a full name."""
    parts = name.strip().split()
    initials = [p[0].upper() for p in parts if p]
    return "".join(initials[:3])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bazi-skill",
        description="Generate a Ba Zi (Four Pillars of Destiny) report from birth data.",
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
        "--gender",
        required=True,
        choices=["male", "female"],
        help="Gender of the subject (required for luck pillar calculation).",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=-1,
        help="Birth hour (0-23). Default -1 = unknown (uses noon approximation).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate input and show computed pillars, then exit without rendering.",
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


def _parse_input(args) -> tuple[BaziRecord, str]:
    """Parse input file into a BaziRecord."""
    fmt = args.format or _detect_format(args.input)
    text = Path(args.input).read_text(encoding="utf-8").strip()

    record: Optional[BaziRecord] = None

    if fmt in ("json", "yaml", "csv"):
        record = _parse_structured(text, fmt)
    else:
        record = _parse_natural_language(text)

    if record is None:
        print("Error: Could not parse input. Ensure you provide a name and date of birth.")
        sys.exit(1)

    return record, fmt


def _parse_structured(text: str, fmt: str) -> Optional[BaziRecord]:
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

    return BaziRecord(name=name, date_of_birth=dob)


def _parse_natural_language(text: str) -> Optional[BaziRecord]:
    """Parse natural language input.

    Looks for patterns like:
    - "Name: John Doe" or just a name at the start
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
        else:
            # First non-empty line without a keyword is likely the name
            if not name:
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

    if not name or not dob_str:
        return None

    dob = _parse_date(dob_str)
    if dob is None:
        print(f"Error: Could not parse date '{dob_str}'.")
        return None

    return BaziRecord(name=name, date_of_birth=dob)


def _parse_date(s: str) -> Optional[date]:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        parts = s.strip().split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def _validate(record: BaziRecord) -> list[str]:
    """Validate the Ba Zi record."""
    errors = []

    if not record.name.strip():
        errors.append("Name is required.")

    if record.date_of_birth > date.today():
        errors.append("Date of birth cannot be in the future.")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # --- Parse input ---
    record, fmt = _parse_input(args)
    dob_str = record.date_of_birth.isoformat() if record.date_of_birth else "(missing)"
    print(f"Parsed '{record.name}' ({fmt}) — DOB {dob_str}")

    # --- Validate ---
    errors = _validate(record)
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    gender = Gender(args.gender)
    record.hour = args.hour
    record.gender = gender

    if args.dry_run:
        # Just compute and display pillars
        from .calculations import compute_all

        result = compute_all(record)

        print("\n=== Four Pillars ===")
        for pillar in [result.year_pillar, result.month_pillar, result.day_pillar, result.hour_pillar]:
            sb = pillar.stem_branch
            print(f"  {pillar.label}: Stem={sb.stem_index}, Branch={sb.branch_index} — Hidden: {pillar.hidden_stems or '—'}")

        print(f"\nDay Master: {result.day_master_yin_yang} {result.day_master_element}")
        print(f"Element counts: {result.element_counts}")

        if result.luck_pillars:
            print("\n=== Luck Pillars ===")
            for lp in result.luck_pillars[:4]:
                print(f"  Ages {lp.start_age}-{lp.start_age + 9}: {lp.stem_branch.stem_index}/{lp.stem_branch.branch_index} ({lp.year_range})")

        return 0

    # --- Render all output formats ---
    html_path = render_html(record, gender=gender, output_dir=args.output_dir)
    json_path = render_json(record, gender=gender, output_dir=args.output_dir)
    md_path = render_markdown(record, gender=gender, output_dir=args.output_dir)

    from .calculations import compute_all
    from .renderer import render_bazi_wheel

    result = compute_all(record)
    initials = generate_initials(record.name)

    svg_content = render_bazi_wheel(result, width=700, height=850)
    svg_path = Path(args.output_dir) / f"{initials}_bazi.svg"
    svg_path.write_text(svg_content, encoding="utf-8")

    print(f"\nBa Zi report for '{record.name}':")
    print(f"  SVG:   {svg_path}")
    print(f"  HTML:  {html_path}")
    print(f"  JSON:  {json_path}")
    print(f"  MD:    {md_path}")

    return 0


def generate_initials(name: str) -> str:
    """Generate deterministic initials from a full name."""
    parts = name.strip().split()
    initials = [p[0].upper() for p in parts if p]
    return "".join(initials[:3])


if __name__ == "__main__":
    sys.exit(main())
