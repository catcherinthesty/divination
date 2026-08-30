# Data Model — Natal Chart Skill

## Entity: BirthRecord

The structured representation of a person's birth data. This is the canonical input that flows through the parser → validator → geocoder pipeline before reaching the renderer.

### Fields

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| `name` | string | Yes | Non-empty, 1–80 characters, alphabetic + spaces/hyphens/apostrophes only | FR-002 |
| `date_of_birth` | date (YYYY-MM-DD) | Yes | Must be on or before today; must not be more than 150 years in the past | US-3, edge case |
| `time_of_birth` | time (HH:MM ± AM/PM) or null | No | If present: 00:00–23:59; null is valid but triggers house approximation warning | FR-009, edge case |
| `location_description` | string | Yes | Non-empty; used for geocoding lookup | FR-004 |
| `latitude` | float | Auto-resolved | If provided directly: −90.0 to 90.0; otherwise resolved by geocoder | Edge case |
| `longitude` | float | Auto-resolved | If provided directly: −180.0 to 180.0; otherwise resolved by geocoder | Edge case |
| `timezone` | string (IANA) | No | If provided: must be in `zoneinfo.available_timezones()`; if absent, inferred from city lookup | FR-008 |
| `nation_code` | string (ISO 3166-1 alpha-2) | Auto-resolved | Two-letter country code; derived from geocoder lookup table | — |

### Relationships

- BirthRecord → GeocodeResult (one-to-one): the location_description field produces a single GeocodeResult via the geocoder.
- BirthRecord → ClarificationRequest (one-to-many): validation may produce zero, one, or multiple clarification requests before the record is ready for rendering.
- BirthRecord → ChartOutput (one-to-one): a validated BirthRecord produces exactly one ChartOutput set of files.

### State Transitions

```
Draft → Validating → Clarifying → Valid → ReadyForRendering
         ↑              ↓
         └─────── Rejected ─┘
```

1. **Draft**: Input received but not yet validated.
2. **Validating**: Fields checked for presence, format, and plausibility.
3. **Clarifying**: One or more fields require user input (missing time, ambiguous city, future date). The record loops here until clarified.
4. **Valid**: All fields present, plausible, and geocoded. Ready for API call.
5. **ReadyForRendering**: Chart files generated and written to disk.

### Validation Rules (from FR-002, FR-003)

- `name` must not be empty or contain special characters beyond spaces, hyphens, and apostrophes.
- `date_of_birth` must be ≤ today's date; values > 150 years in the past trigger a confirmation prompt.
- `time_of_birth`, if provided, must parse to a valid 24-hour time (00:00–23:59). Null is acceptable.
- `location_description` must be non-empty; if it matches multiple entries in the geocoder lookup table, disambiguation is required.
- If `latitude`/`longitude` are provided directly, they must be within valid ranges (−90 to 90, −180 to 180).

---

## Entity: GeocodeResult

The output of address resolution. Produced by the geocoder module when a location description is resolved to coordinates.

### Fields

| Field | Type | Source |
|-------|------|--------|
| `latitude` | float (decimal degrees) | From lookup table or user input |
| `longitude` | float (decimal degrees) | From lookup table or user input |
| `source_location` | string | The original location_description that was resolved |
| `confidence` | enum: `{high, medium, low}` | high = exact match in lookup table; medium = partial/case-insensitive match; low = user-provided coordinates |
| `matched_name` | string or null | The canonical name from the lookup table if a match was found (null for user-provided coordinates) |

### Relationships

- GeocodeResult ← BirthRecord (one-to-one): each validated birth record has exactly one geocode result.
- Ambiguity: when multiple lookup entries match (e.g., "Springfield"), the geocoder returns a list of candidates instead of a single result, triggering a ClarificationRequest.

### Determinism Guarantee

The same `source_location` string always produces the same `(latitude, longitude)` pair across runs. The lookup table is bundled with the skill and never modified at runtime. No network calls are made during resolution.

---

## Entity: ClarificationRequest

An interaction artifact produced when input validation detects insufficient or ambiguous data. This entity represents a single clarification prompt returned to the user.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `field_name` | string | The name of the field requiring clarification (e.g., "time_of_birth", "location_description") |
| `reason` | string | Human-readable explanation of why clarification is needed |
| `suggested_options` | list of strings or null | Possible values to choose from (e.g., list of Springfield cities); null if the user should provide free text |
| `format_guidance` | string or null | Expected format for user input (e.g., "YYYY-MM-DD", "HH:MM AM/PM") |
| `severity` | enum: `{blocker, warning}` | blocker = chart cannot proceed without this field; warning = chart can proceed but with reduced accuracy |

### Relationships

- ClarificationRequest → BirthRecord (many-to-one): a single birth record may generate multiple clarification requests simultaneously. The skill presents all of them together and waits for the user to respond to all before re-validating.
- ClarificationRequest is transient: it exists only during the validation cycle and is discarded once the user responds.

### Examples

1. **Missing time**: `field_name="time_of_birth"`, `reason="Birth time not provided — house positions will be approximate"`, `severity="warning"`
2. **Ambiguous city**: `field_name="location_description"`, `reason="34 cities named 'Springfield' in the US. Please specify state or full address."`, `suggested_options=["Springfield, IL", "Springfield, MA", ...]`, `severity="blocker"`
3. **Future date**: `field_name="date_of_birth"`, `reason="Date is in the future. Please confirm or correct."`, `format_guidance="YYYY-MM-DD"`, `severity="blocker"`

---

## Entity: ChartOutput

The set of files produced for one chart generation. This is the final output of the pipeline.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `svg_path` | string (absolute or relative) | Path to the SVG chart wheel file (e.g., `bakl_chart.svg`) |
| `html_path` | string (absolute or relative) | Path to the HTML analysis page (e.g., `bakl_chart.html`) |
| `json_path` | string (absolute or relative) | Path to the API request/response record (e.g., `api_call.json`) |
| `subject_name` | string | The subject's full name, stored only in file content (never in filename) |
| `initials` | string | Subject initials used for filenames (e.g., "bakl") |

### Relationships

- ChartOutput ← BirthRecord (one-to-one): each validated birth record produces exactly one ChartOutput.
- ChartOutput files contain the subject's name only in their content (HTML body, JSON data), never in the filename or any git-tracked configuration.

### File Content PII Policy

| File | Contains name? | In .gitignore? |
|------|----------------|----------------|
| `bakl_chart.svg` | No (uses initials in title) | No — but user should add to .gitignore if publishing |
| `bakl_chart.html` | Yes (in `<title>` and body) | No — same as above |
| `api_call.json` | Yes (full API response) | No — same as above |

The skill itself does not modify `.gitignore`. This is documented as a user responsibility in the README.
