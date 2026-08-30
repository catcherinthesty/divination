# Research — Natal Chart Skill

## Decision: Geocoding Approach

**Decision**: Use a bundled local lookup table (CSV file) for city-level resolution, supplemented by a deterministic address-to-coordinates mapping for known hospitals and landmarks. No external geocoding API calls are made at runtime.

**Rationale**: The constitution mandates deterministic computation — the same input must produce identical output across runs. External geocoding APIs introduce variability (rate limits, result ordering changes, API version updates). A local lookup table is fully deterministic, requires no network access during chart generation, and covers all use cases in the spec (city names, hospital names with city, known addresses).

**Implementation**: `src/skill/geocoder/lookup.py` reads a bundled CSV file (`data/city_coordinates.csv`) at import time. The CSV contains columns: `name`, `latitude`, `longitude`, `nation`, `type` (city/hospital/landmark). Lookup is case-insensitive with partial-match fallback (e.g., "chicago" matches "Chicago"). Ambiguous names (e.g., "Springfield") return multiple candidates for disambiguation.

**Alternatives considered**:
1. **External geocoding API (e.g., Nominatim/OSM)** — Deterministic but requires network access; results may vary between calls due to ranking changes; introduces a runtime dependency the constitution forbids.
2. **Python `geopy` library** — Wraps multiple geocoding backends, but adds an external dependency (violates constitution Principle I) and has non-deterministic behavior across API providers.
3. **Embedding full GeoNames dataset** — Comprehensive but adds ~50 MB to the package; overkill for the scope of birth chart generation where city-level precision is sufficient unless a specific hospital address is provided.

## Decision: Natural Language Parsing Strategy

**Decision**: Use regex-based extraction with named capture groups, not an LLM or probabilistic parser. Each birth data field (name, date, time, location) has a dedicated regex pattern trained on common English birth description phrasing.

**Rationale**: Determinism is non-negotiable. An LLM-based parser would produce different results for the same input across calls, violating Principle I. Regex extraction is fully deterministic, fast (< 10ms), and covers the vast majority of standard birth description patterns. The spec's NLP goal (SC-002: 90% parse accuracy on unambiguous phrasing) is achievable with well-crafted regexes.

**Implementation**: `src/skill/parser/natural_language.py` applies a sequence of named capture groups in order:
1. Name pattern: `"(?:born to|daughter of|son of|my [a-z]+ was born to)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*?)(?:\s+(?:was|on|in|at))"` — extracts person name
2. Date pattern: `"(?:born on|birth date|date of birth)[:\s]*(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|...)\s+\d{4}|\d{4}-\d{2}-\d{2})"` — extracts date in multiple formats
3. Time pattern: `"(?:at|time)[:\s]*(\d{1,2}:\d{2}\s*(?:AM|PM)?)?"` — optional time extraction
4. Location pattern: `"(?:in|at|born at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s+(?:hospital|clinic|center))?"` — extracts location

Each pattern returns a match object or None. Missing fields trigger clarification (US-3).

**Alternatives considered**:
1. **LLM-based extraction** — High accuracy on complex phrasing but non-deterministic; violates Principle I; requires MCP call overhead per parse.
2. **spaCy NER pipeline** — Deterministic but adds external dependency; overkill for structured birth data patterns.
3. **Rule-based grammar (PEG parser)** — More expressive than regex but significantly more complex to implement and maintain for this narrow domain.

## Decision: YAML Support Without External Dependencies

**Decision**: Implement a minimal YAML subset parser within the skill, supporting only the key-value formats needed for structured birth data input. Do not add PyYAML as a dependency.

**Rationale**: The constitution mandates Python 3 with standard library only (no external packages). `yaml` is not part of the standard library. A full YAML parser would be complex; however, the structured input format for this skill is simple enough that a subset parser covering key-value pairs, quoted strings, and nested objects suffices. This keeps the dependency footprint zero while supporting the YAML format required by FR-001.

**Implementation**: `src/skill/parser/structured.py` includes an inline `_parse_yaml_subset()` function that handles:
- Top-level key: value pairs (with optional quotes)
- Nested objects via indentation (2-space indent)
- Array values for simple lists
- Comments (`#`) and blank lines

This covers 100% of the YAML inputs expected from the skill's users. If a user needs to pass complex YAML with anchors/aliases, they should use JSON instead — the error message guides them.

**Alternatives considered**:
1. **PyYAML as dependency** — Would be simplest to implement but violates the constitution's no-external-dependencies constraint.
2. **Require only JSON and CSV** — Simpler than adding YAML support, but the spec explicitly requires YAML (FR-001).

## Decision: Timezone Resolution Strategy

**Decision**: Use Python's built-in `zoneinfo` module (Python 3.9+) for timezone handling. The skill accepts a timezone string from the user and validates it against IANA timezone database entries bundled with the OS. If no timezone is provided, the skill attempts to infer it from the city using the local lookup table.

**Rationale**: `zoneinfo` is part of the Python standard library (added in 3.9), requires no external dependencies, and provides deterministic timezone resolution. The IANA database is static on any given OS installation, ensuring reproducibility. This satisfies FR-008 (timezone mismatch detection) and handles DST transitions correctly via the `datetime` module's timezone-aware operations.

**Implementation**: 
- If user provides a timezone: validate against `zoneinfo.available_timezones()`; flag mismatches with the city name using a mapping in the lookup table.
- If no timezone provided: look up the city in the geocoder table to find its associated IANA timezone string.
- On DST transition days: use `datetime` with timezone-aware datetimes; the API handles the actual DST offset calculation.

**Alternatives considered**:
1. **`pytz` library** — External dependency; deprecated in favor of `zoneinfo`.
2. **Hardcoded timezone offsets** — Fragile, doesn't handle DST correctly, requires maintenance as timezone rules change.

## Decision: PII Expungement Approach

**Decision**: Names appear only in file content (HTML, JSON), never in filenames or git-tracked files. Filenames use subject initials derived from the parsed name. Git configuration (`git config user.name`, `user.email`) is documented as a user responsibility, not something the skill modifies. Mock data uses a deterministic random seed based on the feature name to generate consistent synthetic names across runs.

**Rationale**: The spec requires zero PII in filenames or git-tracked files (FR-007). Using initials for filenames achieves this while maintaining human-readable file organization. A deterministic seed ensures mock data is reproducible for documentation purposes without ever containing real personal information.

**Implementation**: `src/skill/renderer/naming.py` extracts initials from the parsed name (e.g., "Bristol Ann Klok-Loomis" → "bakl"). The naming function is pure and deterministic: same input always produces same output. Mock data in `docs/sample-inputs/` uses a fixed seed (`random.Random("natal-chart-skill-mock")`) to generate synthetic names like "Jane Doe" consistently.

**Alternatives considered**:
1. **UUID-based filenames** — Fully anonymous but hard to correlate with subjects; defeats the purpose of human-readable file organization.
2. **Hash-based filenames** — Anonymous and deterministic but opaque; requires a lookup table to map hash back to subject, adding complexity.
