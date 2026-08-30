# Quickstart — Divination Routing Validation Guide

## Prerequisites

- Python 3.9+ installed
- Existing sub-skills functional: gematria, bazi, numerology (each has its own `main.py` entry point)
- `ASTROLOGER_API_KEY` environment variable set if bazi requires chart generation via MCP API

## Validation Scenarios

### Scenario 1: Single Gematria Request — Structured Input (US-1, P1)

**Goal**: Verify that a single gematria request produces correct output files.

**Setup**: Create a JSON input file:
```bash
cat > /tmp/test-gematria.json << 'EOF'
{
  "divination_types": ["gematria"],
  "name": "John Smith"
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-gematria.json
```

**Expected Outcome**:
- `js_gematria.html` created with gematria calculations for "John Smith"
- `js_gematria.json` created with raw calculation data
- No cross-link nav in HTML (single divination, per SC-005)
- Exit code 0

**Verifies**: FR-001 (JSON input), FR-004 (single sub-skill execution), SC-001 (100% single-request success)

---

### Scenario 2: Single Gematria Request — Natural Language (US-1, P1)

**Goal**: Verify natural language parsing and routing to gematria.

**Setup**: Create a text file:
```bash
cat > /tmp/test-gematria-nl.txt << 'EOF'
Do gematria on the name John Smith.
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-gematria-nl.txt --format natural-language
```

**Expected Outcome**: Same output files as Scenario 1 (`js_gematria.html`, `js_gematria.json`).

**Verifies**: FR-001 (natural language input), routing matrix gematria keyword match

---

### Scenario 3: Multi-Divination Request with Cross-Links (US-2, P1)

**Goal**: Verify that multiple divinations produce separate output files with bidirectional cross-links.

**Setup**: Create a JSON input:
```bash
cat > /tmp/test-multi.json << 'EOF'
{
  "divination_types": ["gematria", "numerology"],
  "name": "Jane Doe",
  "date_of_birth": "1990-05-15",
  "gematria_systems": ["english"],
  "numerology_systems": ["pythagorean"]
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-multi.json
```

**Expected Outcome**:
- `jd_gematria.html` and `jd_gematria.json` created
- `jd_numerology.html` and `jd_numerology.json` created
- Both HTML files contain a `<nav class="cross-links">` with links to each other
- Exit code 0

**Verifies**: FR-004 (multiple divinations), FR-006 (cross-links present), SC-005 (cross-links when multiple requested)

---

### Scenario 4: Natural Language Multi-Divination (US-2, P1)

**Goal**: Verify routing from natural language to multiple sub-skills.

**Setup**:
```bash
cat > /tmp/test-multi-nl.txt << 'EOF'
Do gematria and numerology for Alice Chen, born 1985-03-22.
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-multi-nl.txt --format natural-language
```

**Expected Outcome**: Same output files as Scenario 3 (deterministic naming from "Alice Chen" → `ac_` prefix). Cross-links present between gematria and numerology HTML files.

**Verifies**: FR-001 (natural language), routing matrix matches both "gematria" and "numerology" keywords

---

### Scenario 5: Missing Required Field — Clarification (US-3, P1)

**Goal**: Verify that missing required data triggers clarification, not silent failure.

**Setup**: Create a JSON without name (required for gematria):
```bash
cat > /tmp/test-no-name.json << 'EOF'
{
  "divination_types": ["gematria"]
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-no-name.json
```

**Expected Outcome**: Exit code non-zero. Clarification request printed: "Name is required for gematria." No output files created.

**Verifies**: FR-003 (validation blocks execution), SC-003 (zero charts from bad data)

---

### Scenario 6: Unknown Divination Type — Clarification (Edge Case)

**Goal**: Verify that an unrecognized divination type triggers clarification with available options.

**Setup**:
```bash
cat > /tmp/test-unknown.json << 'EOF'
{
  "divination_types": ["tarot"]
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-unknown.json
```

**Expected Outcome**: Exit code non-zero. Clarification request lists available types: gematria, bazi, numerology. No output files created.

**Verifies**: Edge case handling — unknown type → clarification with options list

---

### Scenario 7: Partial Failure in Multi-Divination (US-2, P1)

**Goal**: Verify that if one sub-skill fails, others still produce output.

**Setup**: Create input where gematria is valid but bazi has invalid birth data:
```bash
cat > /tmp/test-partial-fail.json << 'EOF'
{
  "divination_types": ["gematria", "bazi"],
  "name": "Test Child",
  "date_of_birth": "2030-01-01",
  "time_of_birth": "12:00",
  "location": {
    "city": "Chicago"
  }
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-partial-fail.json
```

**Expected Outcome**: Gematria output files produced (`tc_gematria.html`, `tc_gematria.json`). Bazi fails due to future birth date. Exit code 0 (partial success). Summary reports: 1 succeeded, 1 failed.

**Verifies**: FR-008 (partial failure handling), SC-006 (at least 80% of valid requests still produce output)

---

### Scenario 8: Deterministic Routing (US-4, P2)

**Goal**: Verify that the same input produces identical output across 10 runs.

**Setup**: Use any valid JSON input from Scenarios 1–3.

**Run**:
```bash
for i in $(seq 1 10); do
  python3 -m src.skill.divination.main --input /tmp/test-multi.json --output-dir /tmp/det-test-$i 2>&1 | tail -1
done
# Compare all output file hashes
sha256sum /tmp/det-test-*/js_gematria.html | cut -d' ' -f1 | sort -u | wc -l
sha256sum /tmp/det-test-*/js_gematria.json | cut -d' ' -f1 | sort -u | wc -l
```

**Expected Outcome**: Both commands return `1` — all 10 runs produce identical SHA-256 checksums for each output file.

**Verifies**: FR-007 (deterministic computation), SC-004 (95%+ routing accuracy on unambiguous phrasing)

---

### Scenario 9: Bazi with Birth Data Only (US-1, P1)

**Goal**: Verify bazi execution requires birth data but not a name field.

**Setup**:
```bash
cat > /tmp/test-bazi.json << 'EOF'
{
  "divination_types": ["bazi"],
  "date_of_birth": "2026-08-26",
  "time_of_birth": "22:02",
  "location": {
    "city": "Chicago"
  },
  "timezone": "America/Chicago"
}
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-bazi.json
```

**Expected Outcome**: Bazi output files created (naming convention uses birth data pillars, not initials). Exit code 0. No cross-link nav (single divination).

**Verifies**: FR-004 (sub-skill executes with its own field requirements), SC-001 (single-request success)

---

### Scenario 10: Ambiguous Natural Language — Clarification Requested (Edge Case)

**Goal**: Verify that ambiguous input triggers clarification instead of guessing.

**Setup**:
```bash
cat > /tmp/test-ambiguous.txt << 'EOF'
Tell me about my name.
EOF
```

**Run**:
```bash
python3 -m src.skill.divination.main --input /tmp/test-ambiguous.txt --format natural-language
```

**Expected Outcome**: Exit code non-zero. Clarification request: "Could not determine which divination type you want. Available types: gematria, bazi, numerology." No output files created.

**Verifies**: Edge case — ambiguous phrasing → clarification with options list (not guessing)

---

## Running All Scenarios

```bash
cd /home/jheinsen/Projects/divination
for scenario in 1 2 3 4 5 6 7 8 9 10; do
  echo "=== Scenario $scenario ==="
  # Each scenario has setup + run steps documented above
  # Exit code 0 = pass, non-zero = fail (or expected failure for validation scenarios)
done
```

## Quick Validation Commands

### Test routing matrix directly:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from skill.divination.router import match_intent
tests = [
    ('do gematria on John', ['gematria']),
    ('numerology and bazi for Alice', ['numerology', 'bazi']),
    ('tell me about my name', []),  # ambiguous → no match
]
for text, expected in tests:
    result = match_intent(text)
    status = '✓' if sorted(result.types) == sorted(expected) else '✗'
    print(f'{status} {text!r} → {result.types}')
"
```

### Test cross-link injection:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from skill.divination.linker import inject_cross_links

# Simulate two HTML files with cross-links
html1 = '<html><body>gematria content</body></html>'
html2 = '<html><body>numerology content</body></html>'

links1 = inject_cross_links(html1, ['js_numerology.html'])
links2 = inject_cross_links(html2, ['js_gematria.html'])

assert 'js_gematria.html' in links1, 'Cross-link missing in gematria HTML'
assert 'js_numerology.html' in links2, 'Cross-link missing in numerology HTML'
print('✓ Cross-link injection verified')
"
```
