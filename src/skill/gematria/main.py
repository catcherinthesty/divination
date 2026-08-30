"""Entry point for the Gematria Skill CLI.

Usage:
    python3 -m src.skill.gematria.main --input <file> [--format json|yaml|csv|natural-language]
                                        [--output-dir DIR] [--dry-run]

Pipeline:
    parse → validate → compute (Simple + Ordinal + Reverse) → render SVG/HTML/JSON/MD

No external API calls — pure arithmetic on letter values.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

from .calculations import compute_all
from .data_types import GematriaRecord, GematriaState, System
from .renderer import render_gematria_wheel


def _gematria_initials(name: str) -> str:
    """Generate 3-4 letter uppercase initials from a name for filenames.

    Uses the first 3-4 alphabetic characters of each word in the name.
    Single-word names get their first 3 letters (e.g., "Aria" → "ARI", "Bristol" → "BRI").
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
        prog="gematria-skill",
        description="Generate a gematria report from a name.",
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


def _parse_input(args) -> tuple[GematriaRecord, str]:
    """Parse input file into a GematriaRecord."""
    fmt = args.format or _detect_format(args.input)
    text = Path(args.input).read_text(encoding="utf-8").strip()

    record: Optional[GematriaRecord] = None

    if fmt in ("json", "yaml", "csv"):
        record = _parse_structured(text, fmt)
    else:
        record = _parse_natural_language(text)

    if record is None:
        print("Error: Could not parse input. Ensure you provide a name.")
        sys.exit(1)

    return record, fmt


def _parse_structured(text: str, fmt: str) -> Optional[GematriaRecord]:
    """Parse structured input (JSON/YAML/CSV)."""
    if fmt == "json":
        data = json.loads(text)
        name = data.get("name") or data.get("full_name", "")
    elif fmt == "yaml":
        # Minimal YAML parser (no dependency)
        data: dict[str, str] = {}
        for line in text.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                key, _, val = line.partition(":")
                data[key.strip()] = val.strip()
        name = data.get("name") or data.get("full_name", "")
    elif fmt == "csv":
        # Simple CSV: header line + one data line
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) < 2:
            return None
        headers = [h.strip() for h in lines[0].split(",")]
        values = [v.strip() for v in lines[1].split(",")]
        data = dict(zip(headers, values))
        name = data.get("name") or data.get("full_name", "")
    else:
        return None

    if not name:
        return None

    return GematriaRecord(full_name=name)


def _parse_natural_language(text: str) -> Optional[GematriaRecord]:
    """Parse natural language input.

    Looks for patterns like:
    - "Name: John Doe" or just a name at the start
    - "My name is Aria"
    """
    lines = text.splitlines()
    name = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check for explicit fields
        if line_stripped.lower().startswith(("name:", "full name:", "person:")):
            name = line_stripped.split(":", 1)[1].strip()
        # Handle "My name is X" pattern
        elif re.match(r"(?:my\s+)?name\s+(?:is|are)\b", line_stripped, re.IGNORECASE):
            raw_name = re.sub(
                r"(?:my\s+)?name\s+(?:is|are)\s*", "", line_stripped, flags=re.IGNORECASE
            ).strip()
            # Clean up: stop at common non-name words
            name_words = []
            skip_words = {"and", "i", "was", "the", "a", "an", "in", "on", "at", "to", "for", "of", "my", "with"}
            for word in raw_name.split():
                if word.lower() not in skip_words:
                    name_words.append(word)
                else:
                    break
            if name_words:
                name = " ".join(name_words)
        # First non-empty line without a keyword is likely the name
        elif not name and len(line_stripped) < 50:
            # Only accept if it looks like a name (starts with capital letter, no punctuation at end)
            if re.match(r"^[A-Z][a-zA-Z'-]+(?:\s+[a-zA-Z'-]+)*$", line_stripped):
                name = line_stripped

    # If no explicit name found, try regex on full text
    if not name:
        m = re.search(r"(?:my\s+)?name\s+(?:is|are)\s+([A-Z][a-zA-Z'-]+(?:\s+[a-zA-Z'-]+)*)", text, re.IGNORECASE)
        if m:
            raw_name = m.group(1)
            # Clean up name: stop at common non-name words
            name_words = []
            skip_words = {"and", "i", "was", "the", "a", "an", "in", "on", "at", "to", "for", "of", "my", "with"}
            for word in raw_name.split():
                if word.lower() not in skip_words:
                    name_words.append(word)
                else:
                    break
            if name_words:
                name = " ".join(name_words)

    if not name:
        return None

    return GematriaRecord(full_name=name)


def _validate(record: GematriaRecord) -> list[str]:
    """Validate the gematria record."""
    errors = []

    if not record.full_name.strip():
        errors.append("Name is required.")

    if len(record.full_name.strip()) > 100:
        errors.append(f"Name too long ({len(record.full_name)} chars, max 100).")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # --- Parse input ---
    record, fmt = _parse_input(args)
    print(f"Parsed '{record.full_name}' ({fmt})")

    # --- Validate ---
    errors = _validate(record)
    if errors:
        print("Validation errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    record.state = GematriaState.COMPUTED

    if args.dry_run:
        # Just compute and display results
        result = compute_all(record)

        system_labels = {
            System.SIMPLE: "Simple (Pythagorean)",
            System.ORDINAL: "Full Ordinal",
            System.REVERSE: "Reverse Ordinal",
        }

        for sys_obj in [System.SIMPLE, System.ORDINAL, System.REVERSE]:
            if sys_obj not in result.results:
                continue
            sr = result.results[sys_obj]
            label = system_labels.get(sys_obj, sys_obj.value)
            print(f"\n=== {label} ===")
            print(f"  Total:      {sr.total}")
            print(f"  Reduced:    {sr.reduced}")
            print(f"  Initials:   {sr.initials_value}")
            for wd in sr.words:
                print(f"  '{wd.word}': {wd.total} → {wd.reduced} (V:{wd.vowel_total}, C:{wd.consonant_total})")

        return 0

    # --- Render all output formats ---
    record.state = GematriaState.READY_FOR_RENDERING
    out_dir = args.output_dir

    result = compute_all(record)
    initials = _gematria_initials(result.name)

    # Generate SVG chart
    svg_content = render_gematria_wheel(result, width=900, height=600)
    svg_path = Path(out_dir) / f"{initials}_gematria.svg"
    svg_path.write_text(svg_content, encoding="utf-8")

    # Generate HTML report
    from .renderer_html import render_html
    html_path = render_html(record, initials=initials, output_dir=out_dir)

    # Generate JSON report
    from .renderer_json import render_json
    json_path = render_json(record, initials=initials, output_dir=out_dir)

    # Generate Markdown report
    from .renderer_md import render_markdown
    md_path = render_markdown(record, initials=initials, output_dir=out_dir)

    print(f"\nGematria report for '{result.name}':")
    print(f"  SVG:   {svg_path}")
    print(f"  HTML:  {html_path}")
    print(f"  JSON:  {json_path}")
    print(f"  MD:    {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
