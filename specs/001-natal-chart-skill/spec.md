# Feature Specification: Natal Chart Skill

**Feature Branch**: `001-natal-chart-skill`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "The project should be structured as a git repository appropriate to publish to github. All PII and secrets should be expunged from the data, and where examples are useful, we should create randomized mock data. The skill should expect either a structure block (JSON, YAML, CSV) or natural language providing the necessary information to create the chart. It should do a first pass check to ensure the information is correct. We should pre-determine an appropriate way to get the longitude and latitude from a city, hospital or address (preferred). It should be asking for clarification where data is unclear or insufficient. It should use deterministic tools to resolve addresses to a specific longitude and latitude. It should use deterministic tools to build all artifacts and structured records."

## User Scenarios & Testing

### User Story 1 — Generate a natal chart from structured input (Priority: P1)

A user wants to produce a complete natal chart package (SVG wheel, HTML analysis, JSON data record) for a person's birth data. They provide the information as a structured block — JSON, YAML, or CSV — containing name, birth date/time, and location. The skill validates the input, resolves any address to geographic coordinates, calls the charting API, and writes all output files with deterministic naming.

**Why this priority**: This is the core value proposition — without it, there is no product. All other features exist to support or enhance this flow.

**Independent Test**: Provide a valid JSON input block and verify that the skill produces `chart.svg`, `chart.html`, and `api_call.json` with correct content. No other features are required.

**Acceptance Scenarios**:

1. **Given** a complete structured input block with name, date, time, city, nation, **When** the skill is invoked, **Then** all three output files are created in the project root with deterministic names and correct chart data
2. **Given** a valid YAML input block, **When** the skill is invoked, **Then** the same output files are produced identically to the JSON case (same birth data produces identical results)
3. **Given** a CSV input block with required columns, **When** the skill is invoked, **Then** output files are produced correctly

---

### User Story 2 — Generate a natal chart from natural language (Priority: P1)

A user wants to produce a natal chart but provides information in plain text rather than structured format. For example: "My daughter was born on August 26, 2026 at 10:02 PM in Chicago." The skill extracts the necessary fields, validates them, resolves the address, and produces the same output files as User Story 1.

**Why this priority**: Natural language input is the most accessible entry point for non-technical users. It must produce identical output to structured input for the same data.

**Independent Test**: Provide a natural language description and verify that the skill extracts correct fields and produces valid output files matching the expected chart.

**Acceptance Scenarios**:

1. **Given** a natural language description containing name, date, time, and city, **When** the skill is invoked, **Then** the skill parses the fields correctly and produces valid chart files
2. **Given** a natural language description missing one required field (e.g., no time), **When** the skill is invoked, **Then** the skill asks for clarification before proceeding

---

### User Story 3 — Input validation and clarification (Priority: P1)

The skill must verify that all required birth data fields are present and sensible before attempting chart generation. If any field is missing, ambiguous, or implausible (e.g., a date in the future, a time outside valid range, an unrecognized city), the skill requests clarification rather than guessing.

**Why this priority**: Prevents silent failures and incorrect charts. A chart generated from bad data is worse than no chart at all.

**Independent Test**: Feed malformed or incomplete input and verify that the skill rejects it with specific clarification requests, never producing a chart from invalid data.

**Acceptance Scenarios**:

1. **Given** input with a future birth date, **When** the skill validates, **Then** it asks the user to confirm or correct the date
2. **Given** input with an ambiguous city name (e.g., "Springfield" — 34+ exist in the US), **When** the skill validates, **Then** it lists the possibilities and asks for disambiguation
3. **Given** input missing the birth time, **When** the skill validates, **Then** it notes that house positions will be approximate and asks whether to proceed or provide a time

---

### User Story 4 — Deterministic address-to-coordinates resolution (Priority: P2)

The skill must convert any location description (city name, hospital name with city, full street address) into precise geographic coordinates using deterministic tools. The same input always produces the same coordinates. No randomness or non-deterministic geocoding services are used.

**Why this priority**: Correct coordinates are essential for accurate chart calculation. However, this is a supporting concern — if the user already provides lat/lon directly, this step can be skipped.

**Independent Test**: Provide an address and verify that the skill resolves it to consistent coordinates across multiple runs. Verify that different addresses produce different coordinates.

**Acceptance Scenarios**:

1. **Given** a city name (e.g., "Chicago"), **When** the skill resolves the address, **Then** it produces specific lat/lon coordinates for that city
2. **Given** a full street address (e.g., "Bronson Methodist Hospital, Kalamazoo MI"), **When** the skill resolves the address, **Then** it produces coordinates for that specific location rather than the city center
3. **Given** an unrecognized or misspelled location, **When** the skill resolves, **Then** it asks for clarification rather than guessing

---

### User Story 5 — Repository structure and PII handling (Priority: P2)

The project is organized as a git repository ready for GitHub publication. All generated data files are free of personally identifiable information in their filenames and metadata. When example or mock data is needed (e.g., in documentation, tests, or sample inputs), it uses randomized synthetic names and birth data that could not be traced to any real person.

**Why this priority**: Privacy compliance is non-negotiable for a project handling birth data. A clean repository structure enables safe sharing and collaboration.

**Independent Test**: Inspect generated files and git history — no real names, addresses, or personal details should appear outside the user's own controlled output files. Mock data samples should use clearly synthetic values.

**Acceptance Scenarios**:

1. **Given** a chart is generated for "Bristol Ann Klok-Loomis", **When** the output files are examined, **Then** the full name appears only in the content of `chart.html` and `api_call.json`, never in filenames or git-tracked configuration
2. **Given** sample input files in the repository (e.g., for documentation), **When** they are examined, **Then** they use randomized mock names like "Jane Doe" with fictional birth dates

---

### Edge Cases

- Input provides a date but no time — houses cannot be accurately calculated; skill asks whether to proceed with approximate house positions or request a time
- Input provides a time zone that does not match the city (e.g., "Chicago" with timezone "America/New_York") — skill flags the mismatch and asks for confirmation
- Birth data falls on a daylight saving time transition day — skill uses the provided timezone string and lets the API handle DST resolution; if the timezone is ambiguous, it asks for clarification
- Address geocoding returns multiple results with similar confidence (e.g., "Paris" — France vs. Texas) — skill lists top candidates and asks for disambiguation
- User provides coordinates directly but they are outside valid ranges (latitude > 90, longitude > 180) — skill rejects and asks for correction
- Natural language input contains contradictory information (e.g., "born in London at noon" but timezone specified as UTC+5) — skill flags the contradiction

## Requirements

### Functional Requirements

- **FR-001**: System MUST accept birth data input in JSON, YAML, or CSV structured format, and in natural language free-text format
- **FR-002**: System MUST validate all required fields (name, birth date, birth time, location) before proceeding to chart generation
- **FR-003**: System MUST request clarification when any field is missing, ambiguous, or implausible, and MUST NOT generate a chart from unverified data
- **FR-004**: System MUST resolve location descriptions (city, hospital, full address) to geographic coordinates using deterministic tools, producing identical results for identical inputs across runs
- **FR-005**: System MUST produce three output files per chart: an SVG chart wheel, an HTML analysis page, and a JSON file containing the complete API request/response record
- **FR-006**: System MUST use deterministic naming conventions for all output files based on subject initials (e.g., `bakl_chart.svg`, `arh_chart.html`)
- **FR-007**: System MUST expunge PII from filenames, git-tracked configuration, and any shared or example data; mock data used in documentation or tests MUST use randomized synthetic values not traceable to real individuals
- **FR-008**: System MUST flag and resolve time zone mismatches between the provided city and the timezone string before chart generation
- **FR-009**: System MUST handle missing birth time gracefully by noting that house positions will be approximate and asking whether to proceed
- **FR-010**: All chart-building artifacts (SVG, HTML, JSON) MUST be produced by deterministic scripts with no randomness or non-deterministic dependencies

### Key Entities

- **BirthRecord**: The structured representation of a person's birth data. Attributes: full name, date of birth, time of birth (optional), location description (city/hospital/address), resolved latitude, resolved longitude, timezone string, nation code
- **ChartOutput**: The set of files produced for one chart. Attributes: SVG wheel file path, HTML analysis file path, JSON data record file path, subject name reference
- **GeocodeResult**: The output of address resolution. Attributes: resolved latitude (decimal degrees), resolved longitude (decimal degrees), source location string, confidence indicator
- **ClarificationRequest**: An interaction artifact produced when input is insufficient. Attributes: field name requiring clarification, reason for the request, suggested options or format guidance

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of charts generated from valid structured input produce all three output files (SVG, HTML, JSON) without manual intervention
- **SC-002**: Natural language input is parsed correctly for standard birth descriptions (name, date, time, city) in at least 90% of test cases with unambiguous phrasing
- **SC-003**: All invalid or incomplete inputs are rejected with specific clarification requests before any chart file is created — zero charts produced from bad data
- **SC-004**: Address-to-coordinate resolution produces identical coordinates for the same input across 10 consecutive runs (determinism verified)
- **SC-005**: Zero instances of real PII appear in git-tracked files, filenames, or example/mock data samples

## Assumptions

- The Astrologer MCP API is available and provides the chart calculation and SVG generation service; the skill delegates computation to it rather than implementing its own ephemeris
- Geographic coordinates for cities are obtainable through a deterministic geocoding source (e.g., a local lookup table or a deterministic API); hospital-level precision may require additional lookup data
- The project uses Python 3 with only standard library dependencies, as established in the project constitution
- Chart output files live in the project root alongside existing generation scripts (`generate_chart.py`, `generate_charts.py`, `generate_relation.py`)
- Git is used for version control and the repository will be pushed to GitHub; `.gitignore` will exclude API response cache files and temporary artifacts
