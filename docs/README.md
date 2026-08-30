# Divination Skill

A deterministic Python CLI tool that generates complete natal chart packages from birth data in multiple input formats.

## Overview

The Natal Chart Skill accepts structured (JSON, YAML, CSV) or natural-language input, validates and clarifies the data, resolves locations to geographic coordinates deterministically, calls the Astrologer MCP API for chart computation, and produces three output files per chart:

- **SVG wheel** — rendered astrological chart
- **HTML analysis** — full interpretation page with planet tables, house cusps, aspects, elements/qualities
- **JSON record** — complete API request/response for reproducibility

## Installation

No external dependencies required. The skill uses Python 3 standard library only:

```bash
python3 -m src.skill.main --input <file> [--format json|yaml|csv|natural-language]
```

### Prerequisites

- Python 3.9+ (for `zoneinfo` module)
- `ASTROLOGER_API_KEY` environment variable set to your RapidAPI key, or use `--response <file>` with a saved API response for offline rendering

## Usage

### Structured Input (JSON)

```bash
python3 -m src.skill.main --input /path/to/birth.json --format json
```

Example input (`example-birth.json`):

```json
{
  "name": "Jane Doe",
  "date_of_birth": "2024-03-15",
  "time_of_birth": "14:30",
  "location": {
    "city": "Chicago",
    "nation": "US"
  },
  "timezone": "America/Chicago"
}
```

### Structured Input (YAML)

```bash
python3 -m src.skill.main --input /path/to/birth.yaml --format yaml
```

Example input (`example-birth.yaml`):

```yaml
name: "Jane Doe"
date_of_birth: "2024-03-15"
time_of_birth: "14:30"
location:
  city: "Chicago"
  nation: "US"
timezone: "America/Chicago"
```

### Structured Input (CSV)

```bash
python3 -m src.skill.main --input /path/to/birth.csv --format csv
```

Example CSV row:

```csv
name,date_of_birth,time_of_birth,location_city,location_nation,timezone
Jane Doe,2024-03-15,14:30,Chicago,US,America/Chicago
```

### Natural Language Input

```bash
python3 -m src.skill.main --input /path/to/description.txt --format natural-language
```

Example input (`description.txt`):

```
My daughter was born on August 26, 2026 at 10:02 PM in Chicago.
```

### Dry Run (Validation Only)

```bash
python3 -m src.skill.main --input /path/to/birth.json --dry-run
```

Validates input, resolves coordinates, checks timezone, but does not call the API or generate chart files.

### Offline Rendering

```bash
python3 -m src.skill.main --input /path/to/birth.json --response /path/to/saved_api_response.json
```

Uses a pre-saved API response instead of making a network call.

## Output Files

Given birth data for "Bristol Ann Klok-Loomis", the skill produces:

| File | Description |
|------|-------------|
| `bakl_chart.svg` | SVG chart wheel (verbatim from API) |
| `bakl_chart.html` | Full HTML analysis page |
| `bakl_api_call.json` | API request/response record |

Filenames use **subject initials only** — no full names appear in filenames, ensuring PII protection.

## PII Handling Policy

This skill is designed with privacy as a first-class concern:

- **Names appear only in file content** (HTML body, JSON data), never in filenames or git-tracked configuration
- **Filenames use initials** — e.g., "Bristol Ann Klok-Loomis" → `bakl_chart.svg`
- **Example/mock data uses synthetic names** — all sample inputs in `docs/sample-inputs/` use randomized values (e.g., "Jane Doe") with fictional birth dates
- **Generated chart files are excluded from git** — the `.gitignore` excludes `*.svg`, `*.html`, and `api_call.json` to prevent accidental PII commits

## Repository Structure

```text
.
├── src/skill/                    # Skill source code
│   ├── main.py                   # Entry point (CLI)
│   ├── data_types.py             # BirthRecord, GeocodeResult, etc.
│   ├── parser/                   # Input parsers (structured + NL)
│   │   ├── structured.py         # JSON/YAML/CSV parser
│   │   └── natural_language.py   # Regex-based NL extractor
│   ├── validator/                # Validation modules
│   │   ├── fields.py             # Required field checks
│   │   ├── ranges.py             # Plausibility checks
│   │   └── tz_mismatch.py        # Timezone validation
│   ├── geocoder/                 # Address resolution
│   │   └── lookup.py             # Deterministic CSV-based resolver
│   └── renderer/                 # Output generation
│       ├── naming.py             # Initials-based filename generation
│       ├── charts.py             # SVG/HTML/JSON rendering
│       ├── chart_writer.py       # Atomic file writes
│       └── templates/            # HTML template files
├── data/                         # Bundled data
│   └── city_coordinates.csv      # Geocoder lookup table
├── docs/                         # Documentation
│   ├── sample-inputs/            # Synthetic mock data (PII-safe)
│   │   ├── example-birth.json
│   │   └── example-birth.yaml
│   └── README.md                 # This file
├── specs/                        # Feature specifications
│   └── 001-natal-chart-skill/
│       ├── spec.md               # Feature specification
│       ├── plan.md               # Implementation plan
│       ├── tasks.md              # Task list
│       ├── data-model.md         # Entity definitions
│       ├── research.md           # Technical decisions
│       ├── quickstart.md         # Validation scenarios
│       └── contracts/            # Input format contracts
├── tests/                        # Test suite
│   └── gematria/                 # Existing gematria tests
├── generate_chart.py             # Legacy chart generation (backward compat)
├── generate_charts.py            # Legacy multi-chart generation
├── generate_relation.py          # Legacy synastry generation
└── .gitignore                    # Excludes generated outputs and PII
```

## Validation Scenarios

See `specs/001-natal-chart-skill/quickstart.md` for 10 comprehensive validation scenarios covering:

1. Structured JSON input → full chart generation
2. YAML input → identical output to JSON
3. CSV input → single record chart
4. Natural language input → field extraction
5. Missing birth time → graceful warning
6. Invalid input → rejection without chart files
7. Deterministic coordinate resolution (10-run consistency)
8. PII absence in filenames and git-tracked files
9. Timezone mismatch detection
10. Ambiguous city disambiguation

## Constitution Compliance

This skill adheres to the Astrology Charting Project Constitution:

- **Principle I (Deterministic Computation)**: All outputs are fully reproducible from identical input; no randomness anywhere in the pipeline
- **Principle II (Standardized Output Contract)**: Naming convention `bakl_chart.svg/html/json`; API response stored in `api_call.json`
- **Principle III (Structured Data Pipeline)**: Three-stage flow: Input → Computation (MCP API) → Rendering (deterministic script)
- **Principle IV (Template-Based HTML Generation)**: Python f-string templates with explicit variable names; sign-keyed lookup tables for interpretation text
