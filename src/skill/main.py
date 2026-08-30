"""Entry point for the Natal Chart Skill CLI.

Usage:
    python3 -m src.skill.main --input <file> [--format json|yaml|csv|natural-language]
                              [--output-dir DIR] [--response FILE] [--dry-run] [--yes]

Pipeline (FR-001..FR-011):
    parse → validate fields/ranges → geocode → timezone check →
    API call (Astrologer) → render SVG/HTML/JSON

The Astrologer API is called over HTTPS with the standard library only
(urllib). Credentials come from the ASTROLOGER_API_KEY environment
variable so no secret is ever committed to the repo. Pass --response
with a saved API response file to render offline (no network call).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Optional

from .data_types import BirthRecord, ClarificationRequest, RecordState, Severity
from .geocoder.lookup import resolve, resolve_with_user_coords
from .parser.structured import parse_input
from .renderer.charts import render_chart
from .validator.fields import validate_fields, validate_ambiguous_location, validate_time_warning
from .validator.ranges import validate_ranges
from .validator.tz_mismatch import check_timezone_mismatch, city_timezone

API_BASE = os.environ.get("ASTROLOGER_API_BASE", "https://astrologer.p.rapidapi.com")
API_PATH = "/api/v5/chart/birth-chart"
API_HOST_HEADER = os.environ.get("ASTROLOGER_API_HOST", "astrologer.p.rapidapi.com")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="natal-chart-skill",
        description="Generate a natal chart from structured or natural language birth data.",
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
        help="Directory for the three output files (default: current directory).",
    )
    parser.add_argument(
        "--response",
        default=None,
        help="Path to a saved Astrologer API response JSON; skips the network call.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and resolve coordinates, then exit without calling the API.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Auto-accept warnings (e.g., missing birth time) without prompting.",
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


def _parse_args(argv: list[str] | None) -> tuple[argparse.Namespace, str]:
    args = build_parser().parse_args(argv)
    fmt = args.format or _detect_format(args.input)
    return args, fmt


def _print_issues(issues: list[ClarificationRequest]) -> None:
    """Print all clarification requests to the terminal."""
    for issue in issues:
        tag = "BLOCKER" if issue.severity == Severity.BLOCKER else "WARNING"
        print(f"[{tag}] {issue.field_name}: {issue.reason}")
        if issue.suggested_options:
            print("  Options:")
            for opt in issue.suggested_options:
                print(f"    - {opt}")
        if issue.format_guidance:
            print(f"  Expected format: {issue.format_guidance}")


def _confirm_warning(issue: ClarificationRequest, auto_yes: bool) -> bool:
    """Ask the user to proceed despite a warning. Returns True to proceed."""
    if auto_yes or not sys.stdin.isatty():
        return True
    try:
        answer = input(f"Proceed anyway? [Y/n] ").strip().lower()
    except EOFError:
        return True
    return answer in ("", "y", "yes")


def _clarification_loop(
    issues: list[ClarificationRequest],
    record: BirthRecord,
    auto_yes: bool,
) -> tuple[list[ClarificationRequest], bool]:
    """Present blockers to the user, collect responses, re-validate until clear.

    Returns (remaining_issues, stopped_early).
    - For ambiguous locations: shows numbered options, user picks one.
    - For other blockers: asks for manual input.
    - Warnings are auto-accepted when --yes is set or non-interactive.
    Never proceeds with unresolved BLOCKERs.

    Also handles T026: contradictory timezone input — if the user confirms
    a mismatch, they choose between city-default and their explicit value.
    """
    max_rounds = 5
    for _ in range(max_rounds):
        blockers = [i for i in issues if i.severity == Severity.BLOCKER]
        warnings = [i for i in issues if i.severity == Severity.WARNING]

        # Auto-accept warnings (T025: missing time warning)
        if auto_yes and warnings:
            warnings.clear()

        if not blockers and not warnings:
            return [], False

        _print_issues(blockers + warnings)
        print()

        if blockers:
            resolved_any = False
            for issue in blockers:
                # Ambiguous location (T022) — show numbered options
                if issue.suggested_options and len(issue.suggested_options) > 1:
                    print(f"Field: {issue.field_name}")
                    print(f"  Reason: {issue.reason}")
                    for idx, opt in enumerate(issue.suggested_options, 1):
                        print(f"  {idx}. {opt}")
                    try:
                        choice = input("Select option (number): ").strip()
                        idx = int(choice) - 1
                        if 0 <= idx < len(issue.suggested_options):
                            chosen = issue.suggested_options[idx]
                            _apply_location_correction(record, chosen)
                            resolved_any = True
                            print(f"  → Selected: {chosen}")
                    except (ValueError, EOFError):
                        print("  Could not parse selection — re-prompting.")
                # Contradictory timezone (T026)
                elif issue.field_name == "timezone" and issue.suggested_options:
                    print(f"Field: {issue.field_name}")
                    print(f"  Reason: {issue.reason}")
                    opts = issue.suggested_options
                    print(f"  Options: [1] {opts[0]} (city default), [2] {opts[1]} (your input)")
                    try:
                        choice = input("Confirm timezone (1/2): ").strip()
                        if choice == "1":
                            record.timezone = opts[0]
                        else:
                            record.timezone = opts[1]
                        resolved_any = True
                    except EOFError:
                        print("  No input — stopping clarification.")
                        return issues, True
                else:
                    # General field blocker
                    print(f"Field: {issue.field_name}")
                    print(f"  Reason: {issue.reason}")
                    if issue.format_guidance:
                        print(f"  Expected format: {issue.format_guidance}")
                    try:
                        answer = input("Your correction: ").strip()
                        if not answer:
                            print("  Empty input — cannot resolve this blocker.")
                            continue
                        _apply_field_correction(record, issue.field_name, answer)
                        resolved_any = True
                    except EOFError:
                        print("  No input — stopping clarification.")
                        return issues, True
            if resolved_any:
                # Re-validate after corrections
                issues = validate_fields(record)
                issues.extend(validate_ranges(record))
                issues.extend(validate_ambiguous_location(record))
                geocode, geo_issues = _geocode(record)
                if geocode is not None:
                    issues.extend(_resolve_timezone(record, geocode))
                time_warning = validate_time_warning(record)
                if time_warning:
                    warnings.append(time_warning)
                continue  # present any remaining issues

            # No blockers were resolved in this round — stop
            if blockers:
                return issues, True

        # No blockers left — check warnings
        if warnings and not _all_warnings_accepted(warnings, auto_yes):
            print("Chart generation stopped — warnings were not accepted.")
            return issues, True

        return [], False

    print("Too many clarification rounds — stopping.")
    return issues, True


def _apply_location_correction(record: BirthRecord, location: str) -> None:
    """Update the record's location description and clear cached coords."""
    record.location_description = location
    record.latitude = None
    record.longitude = None


def _apply_field_correction(record: BirthRecord, field: str, value: str) -> None:
    """Apply a user-provided correction to a BirthRecord field."""
    if field == "name":
        record.name = value
    elif field == "date_of_birth":
        try:
            parts = value.strip().split("-")
            if len(parts) == 3:
                from datetime import date as _date
                record.date_of_birth = _date(
                    int(parts[0]), int(parts[1]), int(parts[2])
                )
        except (ValueError, IndexError):
            print(f"  Could not parse date '{value}'. Use YYYY-MM-DD.")
    elif field == "time_of_birth":
        record.time_of_birth = value.strip()
    elif field == "location_description":
        record.location_description = value
        record.latitude = None
        record.longitude = None


def _geocode(record: BirthRecord) -> tuple[Optional[Any], list[ClarificationRequest]]:
    """Resolve the record's location to coordinates (FR-004).

    Returns (GeocodeResult or None, issues).
    """
    issues: list[ClarificationRequest] = []

    if record.latitude is not None and record.longitude is not None:
        try:
            return resolve_with_user_coords(
                record.location_description, record.latitude, record.longitude
            ), issues
        except ValueError as exc:
            issues.append(ClarificationRequest(
                field_name="location",
                reason=str(exc),
                severity=Severity.BLOCKER,
            ))
            return None, issues

    results = resolve(record.location_description)
    if not results:
        issues.append(ClarificationRequest(
            field_name="location",
            reason=(
                f"Location '{record.location_description}' not found in the lookup "
                "table. Provide a known city/hospital name or explicit latitude/longitude."
            ),
            format_guidance="City name, hospital name, or add latitude/longitude fields",
            severity=Severity.BLOCKER,
        ))
    elif len(results) > 1:
        issues.append(ClarificationRequest(
            field_name="location",
            reason=(
                f"Location '{record.location_description}' is ambiguous "
                f"({len(results)} matches). Please specify which one."
            ),
            suggested_options=[r.matched_name for r in results],
            severity=Severity.BLOCKER,
        ))
    else:
        return results[0], issues

    return None, issues


def _resolve_timezone(record: BirthRecord, geocode: Optional[Any]) -> list[ClarificationRequest]:
    """Check for timezone-city mismatch; infer timezone when absent (FR-008)."""
    issues: list[ClarificationRequest] = []
    city_name = (
        geocode.matched_name if geocode and geocode.confidence.value != "low"
        else record.location_description
    )

    mismatch = check_timezone_mismatch(city_name, record.timezone)
    if mismatch:
        issues.append(mismatch)
        return issues

    if record.timezone is None:
        inferred = city_timezone(city_name)
        if inferred:
            record.timezone = inferred
            print(f"Inferred timezone from lookup table: {inferred}")

    return issues


def _build_subject_payload(record: BirthRecord, geocode: Any) -> dict[str, Any]:
    """Build the Astrologer API subject block from a validated record."""
    hour, minute = 0, 0
    if record.time_of_birth:
        m = re.match(r"^(\d{1,2}):(\d{2})$", record.time_of_birth)
        if m:
            hour, minute = int(m.group(1)), int(m.group(2))

    city = geocode.matched_name or record.location_description
    return {
        "name": record.name,
        "year": record.date_of_birth.year,
        "month": record.date_of_birth.month,
        "day": record.date_of_birth.day,
        "hour": hour,
        "minute": minute,
        "city": city,
        "nation": record.nation_code or "",
        "latitude": geocode.latitude,
        "longitude": geocode.longitude,
        "timezone": record.timezone or "",
        "zodiac_type": "Tropical",
        "houses_system_identifier": "P",
    }


def call_api(subject: dict[str, Any]) -> dict[str, Any]:
    """POST the subject to the Astrologer birth-chart endpoint (stdlib only).

    Raises RuntimeError if no API key is configured or the request fails.
    """
    api_key = os.environ.get("ASTROLOGER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ASTROLOGER_API_KEY environment variable is not set. Set it to your "
            "RapidAPI key, or pass --response <file> with a saved API response."
        )

    url = f"{API_BASE}{API_PATH}"
    body = json.dumps({"subject": subject}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": API_HOST_HEADER,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # URLError, HTTPError, JSON decode
        raise RuntimeError(f"Astrologer API call failed: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    args, fmt = _parse_args(argv)

    # --- Parse (FR-001) ---
    issues: list[ClarificationRequest] = []  # NL parser may produce blockers

    if fmt == "natural-language":
        from .parser.natural_language import parse_natural_language

        text = Path(args.input).read_text(encoding="utf-8")
        record, nl_issues = parse_natural_language(text)
        issues.extend(nl_issues)  # T021: relational name / parent-name blockers
    else:
        record = parse_input(args.input, fmt)

    dob_str = record.date_of_birth.isoformat() if record.date_of_birth else "(not found)"
    print(f"Parsed {record.name!r} ({fmt}) — DOB {dob_str}")
    record.state = RecordState.VALIDATING

    # --- Validate (FR-002, FR-009) ---
    issues.extend(validate_fields(record))
    issues.extend(validate_ranges(record))
    issues.extend(validate_ambiguous_location(record))  # T022

    # --- Geocode (FR-004) ---
    geocode, geo_issues = _geocode(record)
    issues.extend(geo_issues)

    # --- Timezone (FR-008, T026) ---
    if geocode is not None:
        issues.extend(_resolve_timezone(record, geocode))

    # --- Missing time warning (FR-009, T025) ---
    time_warning = validate_time_warning(record)
    if time_warning:
        issues.append(time_warning)

    # --- Clarification loop (T024, T025, T026) ---
    remaining, stopped = _clarification_loop(issues, record, args.yes)
    if stopped or remaining:
        print("Chart generation stopped — resolve the issues above and re-run.")
        return 1

    # Re-resolve geocode after any location correction from the loop
    if geo_issues or geocode is None:
        geocode, geo_issues = _geocode(record)
        if geocode is not None:
            issues.extend(_resolve_timezone(record, geocode))

    if args.dry_run:
        if geocode is None:
            print("Could not resolve coordinates after clarification.")
            return 1
        print(
            f"Resolved coordinates: latitude: {geocode.latitude}, "
            f"longitude: {geocode.longitude} "
            f"(confidence: {geocode.confidence.value}, source: {geocode.source_location})"
        )
        return 0

    # --- API call (FR-005) ---
    if geocode is None:
        print("Error: location could not be resolved to coordinates. Aborting.")
        return 1
    subject = _build_subject_payload(record, geocode)
    if args.response:
        with open(args.response, encoding="utf-8") as f:
            response = json.load(f)
        print(f"Loaded saved API response from {args.response}")
    else:
        response = call_api(subject)

    chart_data = response.get("chart_data", {})
    svg_content = response.get("chart", "")
    if not chart_data or not svg_content:
        print("API response missing 'chart_data' or 'chart' (SVG).")
        return 1

    # --- Render (FR-005, FR-006, FR-010, FR-011) ---
    record.state = RecordState.READY_FOR_RENDERING
    output = render_chart(
        record,
        chart_data,
        svg_content,
        output_dir=args.output_dir,
        subject_payload=subject,
    )

    print(f"Chart for {output.subject_name} ({output.initials}):")
    print(f"  SVG:   {output.svg_path}")
    print(f"  HTML:  {output.html_path}")
    print(f"  JSON:  {output.json_path}")
    return 0


def _all_warnings_accepted(
    warnings: list[ClarificationRequest], auto_yes: bool
) -> bool:
    """Check each warning against the user (or --yes). True if all accepted."""
    for w in warnings:
        if not _confirm_warning(w, auto_yes):
            return False
    return True


if __name__ == "__main__":
    sys.exit(main())
