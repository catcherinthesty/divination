# Quickstart — Natal Chart Skill Validation Guide

## Prerequisites

- Python 3.9+ installed (for `zoneinfo` module)
- The Astrologer MCP server is available and responding to tool calls
- Git repository initialized in the project root

## Validation Scenarios

### Scenario 1: Structured JSON Input — Full Chart Generation (US-1, P1)

**Goal**: Verify that a valid JSON input produces all three output files.

**Setup**: Create a temporary JSON file with known birth data:
```bash
cat > /tmp/test-birth.json << 'EOF'
{
  "name": "Test Child",
  "date_of_birth": "2026-08-26",
  "time_of_birth": "22:02",
  "location": {
    "city": "Chicago",
    "nation": "US"
  },
  "timezone": "America/Chicago"
}
EOF
```

**Run**: Invoke the skill with this input (command TBD based on implementation):
```bash
python3 -m src.skill.main --input /tmp/test-birth.json
```

**Expected Outcome**:
- Three files created in project root: `tc_chart.svg`, `tc_chart.html`, `api_call.json`
- `tc_chart.svg` is valid XML (check with `xmllint --noout tc_chart.svg`)
- `tc_chart.html` contains `<title>` with "Test Child" and all expected sections (key cards, planet table, house cusps, aspects, elements/qualities, interpretation)
- `api_call.json` contains the full API request/response with matching birth data

**Verifies**: FR-001 (JSON input), FR-005 (three output files), FR-006 (deterministic naming)

---

### Scenario 2: Structured YAML Input — Identical Output (US-1, P1)

**Goal**: Verify that the same birth data in YAML produces byte-identical output to JSON.

**Setup**: Create a YAML file with the same data as Scenario 1:
```bash
cat > /tmp/test-birth.yaml << 'EOF'
name: "Test Child"
date_of_birth: "2026-08-26"
time_of_birth: "22:02"
location:
  city: "Chicago"
  nation: "US"
timezone: "America/Chicago"
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth.yaml
```

**Expected Outcome**: The output files (`tc_chart.svg`, `tc_chart.html`) are byte-identical to Scenario 1's output. Only the JSON record differs in its `input` field (YAML vs JSON source).

**Verifies**: FR-001 (YAML input), determinism across input formats

---

### Scenario 3: Structured CSV Input — Single Record (US-1, P1)

**Goal**: Verify that a single-row CSV produces a valid chart.

**Setup**: Create a CSV file with one data row (see `contracts/csv-input.csv` for column format):
```bash
cat > /tmp/test-birth.csv << 'EOF'
name,date_of_birth,time_of_birth,location_city,location_nation,timezone
Test Child,2026-08-26,22:02,Chicago,US,America/Chicago
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth.csv
```

**Expected Outcome**: Same output files as Scenario 1 (deterministic naming from name "Test Child" → initials).

**Verifies**: FR-001 (CSV input)

---

### Scenario 4: Natural Language Input — Field Extraction (US-2, P1)

**Goal**: Verify that natural language input is parsed correctly.

**Setup**: Create a text file with a birth description:
```bash
cat > /tmp/test-birth.txt << 'EOF'
My daughter was born on August 26, 2026 at 10:02 PM in Chicago.
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth.txt --format natural-language
```

**Expected Outcome**: The skill extracts name ("My daughter" → requires clarification for actual name), date ("August 26, 2026"), time ("10:02 PM"), and location ("Chicago"). If the name is ambiguous, the skill asks for clarification before proceeding.

**Verifies**: FR-001 (natural language input), US-2 acceptance scenarios

---

### Scenario 5: Missing Birth Time — Graceful Handling (US-3, P1)

**Goal**: Verify that missing time triggers a warning but does not block chart generation.

**Setup**: Use the JSON from Scenario 1 but omit `time_of_birth`:
```bash
cat > /tmp/test-birth-no-time.json << 'EOF'
{
  "name": "Test Child",
  "date_of_birth": "2026-08-26",
  "location": {
    "city": "Chicago",
    "nation": "US"
  }
}
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth-no-time.json
```

**Expected Outcome**: The skill prints a warning: "Birth time not provided — house positions will be approximate." It then asks the user whether to proceed with approximate houses or provide a time. If the user confirms, charts are generated with default (midnight) house cusps.

**Verifies**: FR-009 (missing time handling), US-3 acceptance scenario 3

---

### Scenario 6: Invalid Input — Rejection (US-3, P1)

**Goal**: Verify that invalid input is rejected without producing chart files.

**Setup**: Create a JSON with a future birth date:
```bash
cat > /tmp/test-birth-future.json << 'EOF'
{
  "name": "Test Child",
  "date_of_birth": "2030-01-01",
  "time_of_birth": "12:00",
  "location": {
    "city": "Chicago",
    "nation": "US"
  }
}
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth-future.json
```

**Expected Outcome**: The skill rejects the input with: "Birth date is in the future. Please confirm or correct." No chart files are created. The exit code is non-zero.

**Verifies**: FR-002 (validation), FR-003 (no chart from invalid data), US-3 acceptance scenario 1

---

### Scenario 7: Deterministic Coordinate Resolution (SC-004)

**Goal**: Verify that address resolution produces identical coordinates across 10 runs.

**Setup**: Use the same JSON input for all runs.

**Run**:
```bash
for i in $(seq 1 10); do
  python3 -m src.skill.main --input /tmp/test-birth.json --dry-run 2>&1 | grep "Resolved coordinates"
done
```

**Expected Outcome**: All 10 runs produce identical coordinate output (e.g., `latitude: 41.878, longitude: -87.7209`). No variation between runs.

**Verifies**: FR-004 (deterministic geocoding), SC-004 (identical coordinates across 10 runs)

---

### Scenario 8: PII in Filenames — Absence Verification (SC-005, FR-007)

**Goal**: Verify that no real names appear in filenames or git-tracked files.

**Setup**: Generate a chart for a subject with a distinctive name.

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth.json
ls -la *.svg *.html *.json | grep -v "test-birth"
git ls-files | grep -i "test\|child\|bristol\|aria" || echo "No PII in tracked files"
```

**Expected Outcome**: Filenames use initials only (e.g., `tc_chart.svg`). No file contains the subject's full name. Git-tracked configuration and example data contain no real names.

**Verifies**: FR-006 (initials-based naming), FR-007 (PII expungement), SC-005 (zero PII in tracked files)

---

### Scenario 9: Timezone Mismatch Detection (FR-008)

**Goal**: Verify that timezone-city mismatches are flagged.

**Setup**: Create a JSON with Chicago but Eastern timezone:
```bash
cat > /tmp/test-birth-tz-mismatch.json << 'EOF'
{
  "name": "Test Child",
  "date_of_birth": "2026-08-26",
  "time_of_birth": "22:02",
  "location": {
    "city": "Chicago",
    "nation": "US"
  },
  "timezone": "America/New_York"
}
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth-tz-mismatch.json
```

**Expected Outcome**: The skill prints: "Timezone mismatch: city 'Chicago' is in America/Chicago, but timezone specified as America/New_York. Please confirm which is correct." It does not proceed until the user confirms or corrects.

**Verifies**: FR-008 (timezone mismatch detection), edge case handling

---

### Scenario 10: Ambiguous City — Disambiguation (Edge Case)

**Goal**: Verify that ambiguous city names trigger disambiguation.

**Setup**: Create a JSON with "Springfield":
```bash
cat > /tmp/test-birth-springfield.json << 'EOF'
{
  "name": "Test Child",
  "date_of_birth": "2026-08-26",
  "time_of_birth": "12:00",
  "location": {
    "city": "Springfield",
    "nation": "US"
  }
}
EOF
```

**Run**:
```bash
python3 -m src.skill.main --input /tmp/test-birth-springfield.json
```

**Expected Outcome**: The skill lists all matching cities from the geocoder lookup table (e.g., "Springfield, IL", "Springfield, MA", "Springfield, MO", ...) and asks the user to specify which one. No chart is generated until disambiguation is resolved.

**Verifies**: FR-003 (clarification for ambiguous data), edge case handling

---

## Running All Scenarios

To run all scenarios in sequence:
```bash
cd /home/jheinsen/Projects/astrology
for scenario in 1 2 3 4 5 6 7 8 9 10; do
  echo "=== Scenario $scenario ==="
  python3 tests/integration/test_scenario_$scenario.py
done
```

Each test script follows the Given-When-Then pattern and exits with code 0 on pass, non-zero on fail. See `tests/integration/` for implementation.
