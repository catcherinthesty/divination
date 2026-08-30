# Natal Chart Skill

Generate complete natal chart packages (SVG wheel, HTML analysis, JSON data record) from birth data in JSON, YAML, CSV, or natural language format.

**Description**: Deterministic natal chart generation with input validation, address geocoding, and multi-format support.

## When to Use

Use this skill when the user wants to:
- Generate an astrological natal chart from birth data
- Convert structured birth data (JSON/YAML/CSV) into chart files
- Parse a natural language birth description into a chart
- Validate birth data for completeness and correctness
- Resolve a location name or address to geographic coordinates

## Prerequisites

Before invoking, ensure:

1. `ASTROLOGER_API_KEY` environment variable is set (RapidAPI key), OR use `--response <file>` with a saved API response for offline rendering
2. The birth data contains at minimum: **name**, **date of birth**, and **location**
3. For accurate house positions, include the **time of birth**

## Usage

### Structured Input (JSON)

```bash
python3 -m src.skill.main --input <file.json> --format json [--dry-run] [--response <saved_api.json>]
```

Example JSON input:

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
python3 -m src.skill.main --input <file.yaml> --format yaml [--dry-run]
```

Example YAML input:

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
python3 -m src.skill.main --input <file.csv> --format csv [--dry-run]
```

Example CSV input:

```csv
name,date_of_birth,time_of_birth,location_city,location_nation,timezone
Jane Doe,2024-03-15,14:30,Chicago,US,America/Chicago
```

### Natural Language Input

```bash
python3 -m src.skill.main --input <file.txt> --format natural-language [--dry-run]
```

Example text input:

```
Bristol Ann Klok-Loomis was born on August 26, 2026 at 10:02 PM in Chicago.
```

### Dry Run (Validation Only)

```bash
python3 -m src.skill.main --input <file> [--format json|yaml|csv|natural-language] --dry-run
```

Validates input, resolves coordinates, checks timezone — no API call or chart files produced.

## Output Files

For a subject named "Jane Doe" (initials: `jd`), the skill produces three files in the output directory:

| File | Description |
|------|-------------|
| `jd_chart.svg` | SVG astrological chart wheel |
| `jd_chart.html` | Full HTML analysis page with planet tables, house cusps, aspects, interpretation |
| `jd_api_call.json` | Complete API request/response record for reproducibility |

**Naming convention**: `{initials}_chart.{svg|html}` and `{initials}_api_call.json` — initials are derived deterministically from the subject's full name (e.g., "Bristol Ann Klok-Loomis" → `bakl`).

## Workflow Checklist

Follow this sequence for reliable chart generation:

- [ ] **Step 1**: Validate input format — ensure birth data is complete (name, date, location)
- [ ] **Step 2**: Run `--dry-run` to verify coordinate resolution and timezone inference
- [ ] **Step 3**: If dry-run passes, generate chart files (omit `--dry-run`)
- [ ] **Step 4**: Verify output files exist and are non-empty
- [ ] **Step 5**: Confirm SVG renders as valid XML (optional: `python3 -c "import xml.etree.ElementTree as ET; ET.parse('chart.svg')"` )

## Progressive Disclosure

The skill loads external resources on demand — do not read all files upfront. Only load these when needed:

- **`data/city_coordinates.csv`** — Load only when geocoding a location string. Contains 60+ city/hospital entries with coordinates and timezones.
- **`specs/001-natal-chart-skill/spec.md`** — Read only when the user asks about feature requirements or acceptance criteria.
- **`specs/001-natal-chart-skill/data-model.md`** — Read only when debugging field validation errors or entity schemas.
- **`src/skill/renderer/templates/chart.html`** — Read only when modifying HTML output format or interpretation text.

## Gotchas

- **Missing birth time**: Houses cannot be accurately calculated without a birth time. The skill defaults to midnight and issues a warning, but house positions will be approximate.
- **Ambiguous city names**: "Springfield" matches 5 entries (IL, MA, MO, OH, NE). The skill blocks chart generation until the user disambiguates. Similarly, "Paris" matches both US and France.
- **Timezone mismatches**: If the user provides a timezone that doesn't match the city's expected timezone (e.g., Chicago with `America/New_York`), the skill flags the mismatch and asks for confirmation.
- **Natural language names**: Phrases like "my daughter" or "born to [Parent Name]" extract as relational references, not proper names. The skill blocks until a real name is provided.
- **API key required**: Without `ASTROLOGER_API_KEY` set, chart generation fails unless `--response <file>` points to a saved API response.
- **YAML subset only**: The built-in YAML parser handles key-value pairs, nested objects, and quoted strings — it does not support YAML anchors, aliases, or multi-line strings. Use JSON for complex documents.
- **Deterministic output**: Same input always produces byte-identical SVG and HTML files across runs. No randomness anywhere in the pipeline.

## Validation Rules

| Field | Required | Format | Constraints |
|-------|----------|--------|-------------|
| `name` | Yes | String, 1–80 chars | Alphabetic + spaces/hyphens/apostrophes only |
| `date_of_birth` | Yes | YYYY-MM-DD | Must be ≤ today; ≥ 150 years in the past triggers confirmation |
| `time_of_birth` | No | HH:MM (24-hour) | 00:00–23:59; null defaults to midnight with warning |
| `location` | Yes | City name, hospital, or address | Must resolve to coordinates in lookup table |
| `latitude` / `longitude` | No (auto-resolved) | Decimal degrees | If provided: lat −90 to 90, lon −180 to 180 |
| `timezone` | No (auto-inferred) | IANA identifier | Must match city's expected timezone or user confirms mismatch |

## Data Model Reference

For schema details, field types, and state transitions, read:

```bash
cat specs/001-natal-chart-skill/data-model.md
```

Key entities: `BirthRecord`, `GeocodeResult`, `ClarificationRequest`, `ChartOutput`.

## Contract Files

Input format contracts are in:

```bash
cat specs/001-natal-chart-skill/contracts/json-input.json   # JSON schema + examples
cat specs/001-natal-chart-skill/contracts/yaml-input.yaml    # YAML examples
cat specs/001-natal-chart-skill/contracts/csv-input.csv      # CSV column definitions
```

## PII Policy

- Names appear **only in file content** (HTML body, JSON data), never in filenames
- Filenames use deterministic initials from the subject's name
- Example/mock data uses synthetic names ("Jane Doe") with fictional dates
- Generated chart files should be added to `.gitignore` before publishing to shared repositories

## Constitution Compliance

This skill adheres to the Astrology Charting Project Constitution:
- **Principle I (Deterministic Computation)**: All outputs reproducible from identical input; no randomness
- **Principle II (Standardized Output Contract)**: Naming convention `{initials}_chart.svg/html/json`
- **Principle III (Structured Data Pipeline)**: Three-stage flow — Input → Computation (MCP API) → Rendering
- **Principle IV (Template-Based HTML Generation)**: Python f-string templates with sign-keyed lookup tables
