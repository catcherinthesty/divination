# Implementation Plan: Natal Chart Skill

**Branch**: `001-natal-chart-skill` | **Date**: 2026-08-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-natal-chart-skill/spec.md`

## Summary

Build a deterministic Python CLI skill that accepts birth data in JSON, YAML, CSV, or natural language format, validates and clarifies the input, resolves addresses to geographic coordinates deterministically, calls the Astrologer MCP API for chart computation, and produces three output files per chart: an SVG wheel, an HTML analysis page, and a JSON request/response record. The skill must handle missing/ambiguous data through clarification requests, prevent PII leakage in filenames and git-tracked files, and produce byte-identical output for identical input across runs.

## Technical Context

**Language/Version**: Python 3 (constitution mandates Python 3 with standard library only; no external packages)

**Primary Dependencies**: Astrologer MCP API (chart calculation and SVG generation via tool_search); Python standard library modules: `json`, `yaml` (via PyYAML bundled with most Python installations — if unavailable, a minimal YAML subset parser is written), `csv`, `re`, `argparse`, `pathlib`, `sys`, `datetime`, `dataclasses`

**Storage**: File system — output files live in the project root alongside existing generation scripts (`generate_chart.py`, `generate_charts.py`, `generate_relation.py`). No database or persistent storage layer.

**Testing**: pytest (standard Python testing framework); contract tests for input/output, integration tests for end-to-end chart generation, determinism tests for address resolution

**Target Platform**: Cross-platform CLI tool — runs on any OS with Python 3 installed (Linux, macOS, Windows). No platform-specific code.

**Project Type**: CLI skill / deterministic automation tool — invoked via `/speckit.*` command or directly as a Python script

**Performance Goals**: Chart generation under 10 seconds end-to-end (dominated by MCP API call); address resolution under 1 second for city-level, under 3 seconds for hospital-level

**Constraints**: No PII leakage in filenames, git-tracked config, or example data; deterministic geocoding (same input → same coordinates across runs); no randomness anywhere in the pipeline; all scripts must run without external dependencies beyond standard library

**Scale/Scope**: Single-user local tool initially; designed to handle one chart generation per invocation; extensible to batch processing via a directory of input files

## Constitution Check

### Gates (pre-research)

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Deterministic Computation | COMPLIANT | All outputs produced by deterministic scripts; no randomness; Skyfield canonical library referenced |
| II. Standardized Output Contract | COMPLIANT | Naming convention `bakl_chart.svg/html/json` defined; API response stored in `api_call.json` |
| III. Structured Data Pipeline | COMPLIANT | Three-stage flow: Input → Computation (MCP API) → Rendering (deterministic script) |
| IV. Template-Based HTML Generation | COMPLIANT | Python f-string templates with sign-keyed lookup tables; no dynamic eval |
| V. Non-Romantic Synastry First | NOT APPLICABLE | This feature generates natal charts, not relationship charts. Relationship generation is a separate feature. |

**GATE RESULT**: All applicable gates pass. No violations requiring justification.

### Post-design re-check (Phase 1 complete)

Same as above — Phase 1 design does not introduce any new non-deterministic behavior, ad-hoc filenames, or template injection. All gates remain passing.

## Project Structure

### Documentation (this feature)

```text
specs/001-natal-chart-skill/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — geocoding approaches, NLP parsing strategies
├── data-model.md        # Phase 1 output — BirthRecord, GeocodeResult, ClarificationRequest schemas
├── quickstart.md        # Phase 1 output — validation scenarios and run guide
└── contracts/           # Phase 1 output — input format contracts (JSON, YAML, CSV)
    ├── json-input.json      # JSON schema / example for structured birth data
    ├── yaml-input.yaml      # YAML format contract with examples
    └── csv-input.csv        # CSV column definitions and example rows
```

### Source Code (repository root)

```text
src/
├── skill/                     # Natal chart skill package
│   ├── __init__.py
│   ├── main.py                # Entry point — dispatches to parser → validator → renderer
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── structured.py      # JSON/YAML/CSV input parser (FR-001)
│   │   └── natural_language.py # NLP birth data extraction (FR-001, US-2)
│   ├── validator/
│   │   ├── __init__.py
│   │   ├── fields.py          # Required field validation (FR-002)
│   │   ├── ranges.py          # Date/time/plausibility checks (US-3)
│   │   └── tz_mismatch.py     # Timezone-city mismatch detection (FR-008)
│   ├── geocoder/
│   │   ├── __init__.py
│   │   ├── lookup.py          # Deterministic city/address → coordinates (FR-004)
│   │   └── ambiguity.py       # Multi-result disambiguation (edge cases)
│   └── renderer/
│       ├── __init__.py
│       ├── naming.py          # Deterministic filename generation from initials (FR-006)
│       ├── charts.py          # Calls MCP API, writes SVG/HTML/JSON (FR-005)
│       └── templates/         # HTML template files (f-string based, FR-004)
├── tests/
│   ├── __init__.py
│   ├── contract/              # Input format contract tests
│   │   ├── test_json_input.py
│   │   ├── test_yaml_input.py
│   │   └── test_csv_input.py
│   ├── integration/           # End-to-end chart generation
│   │   ├── test_structured_flow.py
│   │   ├── test_natural_language_flow.py
│   │   └── test_missing_time.py
│   └── unit/                  # Component tests
│       ├── test_parser.py
│       ├── test_validator.py
│       ├── test_geocoder.py
│       ├── test_naming.py
│       └── test_pii_expunge.py
├── generate_chart.py          # Existing — kept for reference / backward compat
├── generate_charts.py         # Existing — multi-chart generation
├── generate_relation.py       # Existing — synastry generation
├── api_call.json              # Generated — API request/response record
└── .gitignore                 # Excludes cache files, temp artifacts, mock data if any

docs/
├── sample-inputs/             # Randomized mock data for documentation (FR-007)
│   ├── example-birth.json     # Synthetic birth data
│   └── example-birth.yaml     # Same data in YAML
└── README.md                  # Project overview and usage guide

specs/                         # Spec Kit feature specs
├── 001-natal-chart-skill/
└── ...
```

**Structure Decision**: Single-package CLI skill under `src/skill/` with clearly separated concerns (parser → validator → geocoder → renderer). This aligns with the constitution's Structured Data Pipeline principle (FR-003: three-stage flow) and keeps each module independently testable. The existing generation scripts (`generate_chart.py`, etc.) are retained in the project root for backward compatibility but the new skill subsumes their functionality.

## Complexity Tracking

No complexity violations — all design decisions favor simplicity and determinism over feature creep. No repository patterns, no abstraction layers beyond what is necessary for testability.
