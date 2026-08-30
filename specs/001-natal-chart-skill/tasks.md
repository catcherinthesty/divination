---

description: "Task list for Natal Chart Skill implementation"

---

# Tasks: Natal Chart Skill

**Input**: Design documents from `/specs/001-natal-chart-skill/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, etc.)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `src/skill/`, `tests/`, `data/`, `docs/sample-inputs/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md: `src/skill/parser/`, `src/skill/validator/`, `src/skill/geocoder/`, `src/skill/renderer/templates/`, `tests/unit/`, `tests/integration/`, `data/`, `docs/sample-inputs/`
- [X] T002 Create `src/skill/__init__.py` with package version and public exports
- [X] T003 Create `src/skill/main.py` entry point with argparse for `--input` (file path) and `--format` (json|yaml|csv|natural-language) flags
- [X] T004 [P] Create `.gitignore` excluding API response cache files, temp artifacts, `.venv/`, and generated chart output files (*.svg, *.html, api_call.json)
- [X] T005 [P] Create `docs/sample-inputs/example-birth.json` with randomized synthetic birth data (name "Jane Doe", fictional date 2024-03-15, city "Springfield") for documentation
- [X] T006 [P] Create `docs/sample-inputs/example-birth.yaml` with same synthetic data in YAML format

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create `data/city_coordinates.csv` bundled geocoder lookup table with columns: name, latitude, longitude, nation, type (city/hospital/landmark). Populate with at least 50 major US cities and known hospital addresses from the project's existing chart data (Chicago, Kalamazoo)
- [X] T008 Create `src/skill/data_types.py` — dataclass definitions for BirthRecord, GeocodeResult, ClarificationRequest, ChartOutput per data-model.md entity specifications with field types, validation constraints, and state transition enum
- [X] T009 Create `src/skill/geocoder/lookup.py` — deterministic city/address-to-coordinates resolver that reads `data/city_coordinates.csv` at import time; implements case-insensitive exact match, partial-match fallback for ambiguous names (returns list of candidates), and validation of user-provided coordinates against valid ranges (−90 to 90, −180 to 180)
- [X] T010 Create `src/skill/renderer/naming.py` — deterministic filename generator from subject name initials (e.g., "Bristol Ann Klok-Loomis" → "bakl"); validates initials are alphabetic; used by all chart output tasks
- [X] T011 Create `src/skill/renderer/templates/chart.html` — HTML analysis page template using Python f-string interpolation with explicit variable names for every field: name, birth_dt, city, nation, tz, house_system, zodiac, diurnal, lunar_phase, key_cards (sun/moon/asc/mercury/venus/mars/phase/ruler), planet_table_rows, house_cusp_rows, aspect_rows, element_distribution, quality_distribution, interpretation_text; no dynamic eval or template injection
- [X] T012 Create `src/skill/validator/tz_mismatch.py` — timezone-city mismatch detector that checks if provided IANA timezone string matches the city's expected timezone from the geocoder lookup table; returns ClarificationRequest on mismatch

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Structured Input Chart Generation (Priority: P1) 🎯 MVP

**Goal**: Accept JSON, YAML, or CSV birth data input, validate it, resolve coordinates, call MCP API, and produce three output files (SVG, HTML, JSON).

**Independent Test**: Provide a valid JSON input block and verify that the skill produces `chart.svg`, `chart.html`, and `api_call.json` with correct content. No other features are required.

### Implementation for User Story 1

- [X] T013 [US1] Create `src/skill/parser/structured.py` — input parser supporting JSON, YAML subset, and CSV formats; includes inline `_parse_yaml_subset()` function handling key-value pairs, nested objects via indentation, quoted strings, comments, and blank lines (no external yaml dependency); maps parsed data to BirthRecord dataclass
- [X] T014 [US1] Create `src/skill/validator/fields.py` — required field validator checking name (non-empty, 1–80 chars, alphabetic + spaces/hyphens/apostrophes), date_of_birth (YYYY-MM-DD format, ≤ today, ≥ 150 years in past), location_description (non-empty); returns list of ClarificationRequest for missing or invalid fields
- [X] T015 [US1] Create `src/skill/validator/ranges.py` — plausibility validator checking time_of_birth parseable to 00:00–23:59 if present; latitude/longitude within valid ranges if provided directly; future date confirmation prompt
- [X] T016 [US1] Integrate parser → validator → geocoder → renderer pipeline in `src/skill/main.py`: read input file, parse to BirthRecord, validate fields and ranges, resolve coordinates via geocoder.lookup.resolve(), check timezone mismatch via tz_mismatch.check(), generate filenames via naming.generate_initials(), call Astrologer MCP API for chart computation, write SVG/HTML/JSON output files
- [X] T017 [US1] Wire HTML template rendering: pass validated BirthRecord fields and MCP API response (chart_data + svg_string) to `src/skill/renderer/templates/chart.html` via f-string interpolation; write rendered HTML to `{initials}_chart.html`; write SVG string directly to `{initials}_chart.svg`; construct api_call.json with input subject data, API URL/method, and full output response
- [X] T018 [US1] Create `src/skill/renderer/chart_writer.py` — deterministic file writer that handles atomic writes (write to temp file then rename) to prevent partial outputs; verifies file size > 0 after write

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. A valid JSON/YAML/CSV input produces all three output files with correct chart data.

---

## Phase 4: User Story 2 — Natural Language Input (Priority: P1)

**Goal**: Extract birth data from plain text using regex-based parsing, validate extracted fields, and produce identical output to structured input for the same data.

**Independent Test**: Provide a natural language description and verify that the skill extracts correct fields and produces valid output files matching the expected chart.

### Implementation for User Story 2

- [X] T019 [US2] Create `src/skill/parser/natural_language.py` — regex-based birth data extractor with named capture groups: name pattern (extracts person name from phrases like "my daughter was born", "born to"), date pattern (handles "August 26, 2026", "2026-08-26", "08/26/2026" formats), time pattern (optional, handles "10:02 PM", "22:02", "at noon"), location pattern (handles "in Chicago", "at Bronson Methodist Hospital"); returns BirthRecord with None for any field not found in text
- [X] T020 [US2] Integrate natural language parser into `src/skill/main.py`: add `--format natural-language` flag branch; parse input text → extract fields → pass to same validator pipeline as US1 (fields.py, ranges.py, tz_mismatch.py)
- [X] T021 [US2] Handle ambiguous name extraction in src/skill/parser/natural_language.py — if natural language produces a relational reference (e.g., "my daughter") instead of a proper name, generate ClarificationRequest asking for the actual name before proceeding

**Checkpoint**: User Stories 1 AND 2 should both work independently. Natural language input with standard phrasing produces identical output to equivalent structured input.

---

## Phase 5: User Story 3 — Input Validation and Clarification (Priority: P1)

**Goal**: Comprehensive validation that rejects invalid/incomplete input with specific clarification requests before any chart file is created.

**Independent Test**: Feed malformed or incomplete input and verify that the skill rejects it with specific clarification requests, never producing a chart from invalid data.

### Implementation for User Story 3

- [ ] T022 [US3] Enhance `src/skill/validator/fields.py` — add ambiguous city detection: after parsing location_description, query geocoder.lookup.resolve() and if it returns multiple candidates (e.g., "Springfield" → 34 matches), generate ClarificationRequest with severity=blocker listing all candidate cities from the lookup table
- [ ] T023 [US3] Enhance `src/skill/validator/ranges.py` — add future date handling: if date_of_birth > today, generate ClarificationRequest with severity=blocker asking user to confirm or correct; add 150-year-old confirmation for historical dates
- [ ] T024 [US3] Implement clarification loop in `src/skill/main.py`: after validation produces ClarificationRequests, present all of them together to the user (in terminal output), collect responses, merge corrections back into BirthRecord, re-validate until no blockers remain; never proceed to chart generation with unresolved blockers
- [ ] T025 [US3] Handle missing time_of_birth in src/skill/main.py and src/skill/validator/ranges.py — if time is None after parsing/validation, generate ClarificationRequest with severity=warning explaining that house positions will be approximate (default midnight), ask whether to proceed or provide a time; if user proceeds, set time to 00:00 and continueer parsing/validation, generate ClarificationRequest with severity=warning explaining that house positions will be approximate (default midnight), ask whether to proceed or provide a time; if user proceeds, set time to 00:00 and continue
- [ ] T026 [US3] Handle contradictory timezone input in src/skill/main.py — if natural language or structured input provides both a city and an explicit timezone that does not match the city's expected timezone (per tz_mismatch.py), generate ClarificationRequest asking user to confirm which is correct before proceedingstructured input provides both a city and an explicit timezone that doesn't match the city's expected timezone (per tz_mismatch.py), generate ClarificationRequest asking user to confirm which is correct before proceeding

**Checkpoint**: All invalid or incomplete inputs are rejected with specific clarification requests. Zero charts produced from bad data. Missing time triggers warning but allows graceful continuation.

---

## Phase 6: User Story 4 — Deterministic Address Resolution (Priority: P2)

**Goal**: Convert any location description to precise geographic coordinates using deterministic tools, producing identical results for identical inputs across runs.

**Independent Test**: Provide an address and verify that the skill resolves it to consistent coordinates across multiple runs. Verify that different addresses produce different coordinates.

### Implementation for User Story 4

- [X] T027 [US4] Expand `data/city_coordinates.csv` — add hospital-level entries for known locations from project data (Bronson Methodist Hospital, Kalamazoo MI), plus additional major US hospitals and landmarks to support US-4 acceptance scenarios. Updated Springfield entries to include state disambiguation ("Springfield, IL", "Springfield, MA", etc.)
- [ ] T028 [US4] Enhance `src/skill/geocoder/lookup.py` — add address-to-coordinates resolution for full street addresses (not just city names); implement confidence scoring: high = exact match, medium = partial/case-insensitive match, low = user-provided coordinates; return matched_name from lookup table when applicable
- [ ] T029 [US4] Enhance ambiguity handling in `src/skill/geocoder/lookup.py`: when multiple entries match with similar confidence (e.g., "Paris" — France vs. Texas), return list of top candidates sorted by confidence; trigger ClarificationRequest per US-3

**Checkpoint**: Address-to-coordinate resolution produces identical coordinates for the same input across 10 consecutive runs (determinism verified). Different addresses produce different coordinates.

---

## Phase 7: User Story 5 — Repository Structure and PII Handling (Priority: P2)

**Goal**: Organize project as a git repository ready for GitHub publication with PII expungement from filenames, git-tracked configuration, and example data using randomized synthetic values.

**Independent Test**: Inspect generated files and git history — no real names, addresses, or personal details should appear outside the user's own controlled output files. Mock data samples should use clearly synthetic values.

### Implementation for User Story 5

- [X] T030 [US5] Verify `src/skill/renderer/naming.py` produces initials-based filenames only (never full names); add unit test logic: generate filenames for "Bristol Ann Klok-Loomis" → "bakl_chart.svg", not "bristol_klok_loomis_chart.svg"
- [X] T031 [US5] Create `docs/README.md` — project overview documenting the skill's purpose, usage examples with synthetic mock data, git repository structure, PII handling policy (names only in file content, never in filenames or tracked config), and instructions for adding generated chart files to .gitignore before publishing
- [X] T032 [US5] Verify `docs/sample-inputs/` contains only randomized synthetic data: check that example-birth.json uses "Jane Doe" with fictional date 2024-03-15, not real personal information; add a second synthetic example (example-birth-2.json with "Alice M. Chen")
- [X] T033 [US5] Add `.gitignore` entries for generated chart output files (*.svg, *.html, api_call.json) as documented in README.md — these are user-controlled outputs that should not be committed to shared repositories

**Checkpoint**: Zero instances of real PII appear in git-tracked files, filenames, or example/mock data samples. Repository is structured for safe GitHub publication.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 Code cleanup in `src/skill/` — removed duplicate date validation call in fields.py (was calling record.validate_date() which also runs in ranges.py), fixed YAML parser bug where _parse_yaml_block returned int instead of tuple, cleaned up Springfield entries in city_coordinates.csv to include state disambiguation
- [X] T036 [P] Create `tests/unit/test_naming.py` — unit tests for deterministic filename generation from various name formats (single name, first+last, hyphenated, apostrophes), PII absence verification, chart_filename and api_call_filename helpers
- [X] T037 [P] Create `tests/unit/test_geocoder.py` — unit tests for geocoder lookup: exact match, case-insensitive match, ambiguous city returning multiple candidates, invalid coordinate range rejection, determinism across 10 runs, street address resolution
- [X] T038 [P] Verify determinism in `src/skill/` — ran same input 10 times for Chicago, Springfield, Bronson Methodist Hospital, and Los Angeles; all produce identical coordinates. SVG and HTML outputs from JSON, YAML, and CSV inputs are byte-identical (sha256 verified)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–7)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (different parsers, same validator/geocoder/renderer)
  - US3 depends on US1/US2 validation pipeline being established
  - US4 depends on foundational geocoder infrastructure (T012)
  - US5 is independent of user story functionality but should follow Setup
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories; MVP deliverable
- **User Story 2 (P1)**: Can start in parallel with US1 after Foundational — uses same validator/geocoder/renderer but different parser
- **User Story 3 (P1)**: Can start after US1 foundation is established — enhances validation and clarification logic used by US1/US2
- **User Story 4 (P2)**: Can start after Foundational geocoder (T012) — expands coordinate resolution capabilities
- **User Story 5 (P2)**: Independent of user story functionality — can run in parallel with any story; focuses on repository hygiene

### Within Each User Story

- Models/dataclasses before services
- Services before integration into main.py
- Core implementation before edge case handling
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1 tasks T004, T005, T006 can run in parallel (different files)
- Phase 2 tasks T010–T015 can run in parallel after T010 (lookup table) is created
- US1 and US2 implementation phases can proceed in parallel by different developers
- US4 and US5 can run in parallel with any other story
- Phase 8 tasks T041, T044, T045 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch model creation and parser implementation together:
Task: "Create structured input parser in src/skill/parser/structured.py"
Task: "Create required field validator in src/skill/validator/fields.py"
Task: "Create plausibility range validator in src/skill/validator/ranges.py"

# After models are ready, implement integration and rendering:
Task: "Integrate pipeline in src/skill/main.py"
Task: "Wire HTML template rendering"
Task: "Create deterministic chart file writer"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run quickstart.md scenario 1 — provide valid JSON input, verify three output files created correctly
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (scenario 1) → MVP delivered!
3. Add User Story 2 → Test independently (scenario 4) → Natural language support added
4. Add User Story 3 → Test independently (scenarios 5, 6) → Robust validation added
5. Add User Story 4 → Test independently (scenario 7) → Deterministic geocoding verified
6. Add User Story 5 → Test independently (scenario 8) → Repository ready for publication
7. Polish → Run all quickstart scenarios → Final verification

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (structured input pipeline)
   - Developer B: User Story 2 (natural language parser)
   - Developer C: User Story 5 (repository structure and PII handling)
3. After US1/US2 are established:
   - Developer A or B: User Story 3 (validation and clarification enhancements)
   - Developer C continues with US4 (deterministic geocoding expansion)
4. All stories complete → Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify quickstart.md scenarios pass before marking a story complete
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- No external Python dependencies — all code uses standard library only (per constitution Principle I)
- All chart-building artifacts must be deterministic: same input → byte-identical output across runs
