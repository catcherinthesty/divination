# Implementation Plan: Divination Routing Skill

**Branch**: `002-divination-routing` | **Date**: 2026-08-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-divination-routing/spec.md`

## Summary

Build a deterministic Python CLI skill that routes divination requests (gematria, bazi, numerology) to their respective sub-skills. Users provide input in natural language or structured format (JSON/YAML), the skill validates and clarifies the data, routes to one or more sub-skills, executes each independently, and produces separate output files with cross-links between them when multiple divinations are requested.

## Technical Context

**Language/Version**: Python 3.9+ (constitution mandates Python 3; zoneinfo required for natal chart skill compatibility)

**Primary Dependencies**: None beyond Python standard library. The three existing sub-skills (`src/skill/gematria/`, `src/skill/bazi/`, `src/skill/numerology/`) are imported as callable modules via their `main()` entry points. No new external packages required.

**Storage**: File system — output files written to a configurable directory (default: current working directory). No database or persistent storage layer. Input data is consumed from stdin, CLI args, or file paths.

**Testing**: pytest for unit tests (routing logic, intent matching, validation), integration tests (end-to-end single and multi-divination invocations), determinism tests (same input → identical output across 10 runs). Contract tests validate input/output schemas.

**Target Platform**: Cross-platform CLI tool — runs on any OS with Python 3 installed (Linux, macOS, Windows). No platform-specific code.

**Project Type**: CLI routing skill / deterministic automation tool — invoked via `python3 -m src.skill.divination.main` or as a subcommand of the existing `src.skill.main.py`.

**Performance Goals**: Multi-divination execution under 5 seconds end-to-end (dominated by gematria/numerology computation; bazi is lightweight). Routing and validation under 100ms. HTML rendering with cross-links under 200ms per output file.

**Constraints**: No randomness anywhere in the pipeline; deterministic intent matching; sub-skill outputs must be independent files (never merged into a single artifact); cross-links use relative hyperlinks within HTML; no external API calls during computation or routing; all scripts run without external dependencies beyond standard library.

**Scale/Scope**: Single-user local tool initially; designed to handle one invocation per command line, with 1-3 sub-skills per invocation. Extensible to additional divination types via plugin registration (future scope).

## Constitution Check

### Gates (pre-research)

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Deterministic Computation | COMPLIANT | Routing is keyword-based regex matching; sub-skills already deterministic; no randomness in output generation |
| II. Standardized Output Contract | NEEDS CLARIFICATION | Sub-skills use different naming conventions (gematria: `{initials}_gematria.html`, bazi: `{pillars}_bazi.html`, numerology: `{initials}_numerology.html`). Need a unified convention for multi-divination output filenames and cross-link paths. |
| III. Structured Data Pipeline | COMPLIANT | Three-stage flow maps cleanly: Input → Routing/Validation → Sub-skill Execution → Rendering. Each stage's output is the next stage's input. |
| IV. Template-Based HTML Generation | COMPLIANT | All sub-skills already use template-based HTML generation with f-string interpolation and lookup tables. No changes needed. |
| V. Non-Romantic Synastry First | NOT APPLICABLE | This feature handles divination (gematria, bazi, numerology), not astrology chart generation. Relationship synastry is outside scope. |

**GATE RESULT**: One gate flagged for clarification (II). Phase 0 research will resolve the naming convention decision. No violations requiring justification.

### Post-design re-check (Phase 1 complete)

After Phase 1 design, Constitution Check remains passing:
- **Principle I**: Routing uses deterministic keyword matching; sub-skill calls are pure function invocations with no side effects
- **Principle II**: Unified naming convention `{subject_initials}_{divination_type}.{ext}` resolves the gap — gematria gets `js_gematria.html`, bazi gets `john_pillars_bazi.html`, numerology gets `js_numerology.html`
- **Principle III**: Pipeline structure unchanged from pre-research assessment
- **Principle IV**: Sub-skill rendering unchanged; cross-links added via template extension, not new templates

## Project Structure

### Documentation (this feature)

```text
specs/002-divination-routing/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — routing strategy, naming convention, cross-link patterns
├── data-model.md        # Phase 1 output — DivinationRequest, RoutingDecision, SubSkillExecution, OutputBundle schemas
├── quickstart.md        # Phase 1 output — validation scenarios and run guide
└── contracts/           # Phase 1 output — input/output format contracts
    ├── json-request.json      # JSON schema for multi-divination request
    └── routing-matrix.md      # Intent keyword → sub-skill mapping reference
```

### Source Code (repository root)

```text
src/skill/
├── __init__.py                    # Package version and exports
├── main.py                        # Existing entry point — extended with divination routing subcommand
├── data_types.py                  # Shared data types (BirthRecord, ClarificationRequest, etc.)
├── gematria/                      # Existing — gematria sub-skill (unchanged)
│   ├── __init__.py
│   ├── main.py                    # CLI entry: main(argv) -> int (exit code 0 = success)
│   ├── calculations.py
│   ├── data_types.py
│   ├── interpretations.py
│   └── renderer.py
├── bazi/                          # Existing — bazi sub-skill (unchanged)
│   ├── __init__.py
│   ├── main.py                    # CLI entry: main(argv) -> int (exit code 0 = success)
│   ├── calculations.py
│   ├── data_types.py
│   ├── interpretations.py
│   └── renderer.py
├── numerology/                    # Existing — numerology sub-skill (unchanged)
│   ├── __init__.py
│   ├── main.py                    # CLI entry: main(argv) -> int (exit code 0 = success)
│   ├── calculations.py
│   ├── data_types.py
│   ├── interpretations.py
│   └── renderer.py
├── divination/                    # NEW — routing skill package
│   ├── __init__.py
│   ├── main.py                    # Entry point: parse input → route → execute → link outputs
│   ├── router.py                  # Intent matching: keyword regex + structured type field → sub-skill selector
│   ├── validator.py               # Input validation per divination type (delegates to sub-skill validators)
│   └── linker.py                  # Cross-link injection into HTML output files
├── parser/                        # Existing — shared input parsers
│   ├── structured.py              # JSON/YAML/CSV parser (from natal-chart-skill)
│   └── natural_language.py        # NL birth data parser (from natal-chart-skill)
├── geocoder/                      # Existing — shared geocoding (from natal-chart-skill)
│   └── lookup.py                  # Deterministic city/address → coordinates
└── validator/                     # Existing — shared validators (from natal-chart-skill)
    ├── fields.py
    ├── ranges.py
    └── tz_mismatch.py

tests/
├── __init__.py
├── unit/                          # Unit tests for routing and validation
│   ├── test_router.py             # Intent matching: keyword regex, structured type field
│   ├── test_validator.py          # Per-type input validation delegation
│   ├── test_linker.py             # Cross-link injection verification
│   └── test_naming.py             # Deterministic filename generation (from natal-chart-skill)
├── integration/                   # End-to-end tests
│   ├── test_single_divination.py  # One sub-skill, complete data → output files
│   ├── test_multi_divination.py   # Two+ sub-skills → cross-linked outputs
│   └── test_partial_failure.py    # One sub-skill fails → others still produce output
└── gematria/                      # Existing gematria tests (unchanged)
    ├── __init__.py
    ├── test_calculations.py
    ├── test_data_types.py
    ├── test_interpretations.py
    ├── test_main.py
    └── test_renderers.py

data/                              # Bundled data (from natal-chart-skill)
└── city_coordinates.csv           # Geocoder lookup table

docs/
├── sample-inputs/                 # Synthetic mock data (unchanged)
│   ├── example-birth.json
│   ├── example-birth.yaml
│   └── example-birth-2.json
└── README.md                      # Project overview (from natal-chart-skill)

specs/                             # Spec Kit feature specs
├── 001-natal-chart-skill/
└── 002-divination-routing/
```

**Structure Decision**: The routing skill lives as a new package under `src/skill/divination/` with three modules (`router.py`, `validator.py`, `linker.py`). It invokes existing sub-skills via subprocess calls to their CLI entry points (`python3 -m src.skill.<type>.main --input <temp_json> --output-dir <temp_dir>`), rather than importing them as libraries. This keeps the routing layer thin and testable while reusing proven sub-skill implementations without refactoring. The existing `src/skill/main.py` is extended with a `--divination` flag that delegates to the new package, avoiding the need for a separate CLI binary.

## Complexity Tracking

No complexity violations — all design decisions favor simplicity and reuse over feature creep. The routing layer is a thin shim (keyword matching + sub-skill delegation), not a new computation engine. No repository patterns, no abstraction layers beyond what is necessary for testability.
