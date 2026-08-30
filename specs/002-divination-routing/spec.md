# Feature Specification: Divination Routing Skill

**Feature Branch**: `002-divination-routing`

**Created**: 2026-08-29

**Status**: Draft

**Input**: User description: "A single divination skill that handles all divination types (gematria, bazi, numerology) via deterministic Python routing. Users can request multiple divinations in a single invocation and receive separate output files with cross-links between them."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Single Divination Request (Priority: P1)

A user wants to perform one divination (e.g., gematria on a name, or bazi for a birth date/time/location). They provide the necessary input data in natural language or structured format. The skill routes to the appropriate sub-skill, validates the input, executes the computation, and produces output files (HTML analysis, JSON data record) with deterministic naming.

**Why this priority**: This is the MVP — without it, there is no product. All other features exist to enhance or extend this flow. A single divination request delivers immediate value to the user.

**Independent Test**: Provide a gematria input (e.g., "Do gematria on 'John Smith'") and verify that the skill produces `js_gematria.html` and `js_gematria.json` with correct calculations. No other features are required.

**Acceptance Scenarios**:

1. **Given** a natural language request for one divination type with complete input data, **When** the skill is invoked, **Then** the appropriate sub-skill is routed to, validated, executed, and output files are produced
2. **Given** a structured input (JSON/YAML) specifying one divination type and its required fields, **When** the skill is invoked, **Then** the same output files are produced identically to the natural language case (same data produces identical results)
3. **Given** an incomplete request for a single divination (e.g., gematria without a name), **When** the skill validates input, **Then** it requests clarification before proceeding

---

### User Story 2 — Multiple Divination Request with Cross-Links (Priority: P1)

A user wants to perform multiple divinations in a single invocation (e.g., "Do gematria and numerology for 'Jane Doe', born 1990-05-15"). The skill routes to each relevant sub-skill, executes them in sequence or parallel, and produces separate output files for each divination. Each output file contains links to the related outputs (e.g., `jd_gematria.html` links to `jd_numerology.html`).

**Why this priority**: This is the core value proposition that differentiates this skill from individual sub-skills — the ability to chain multiple divinations and present them as a unified reading with cross-references.

**Independent Test**: Request gematria and numerology for the same subject in one invocation, verify two output files are created with bidirectional links between them.

**Acceptance Scenarios**:

1. **Given** a natural language request for multiple divination types with complete input data, **When** the skill is invoked, **Then** separate output files are produced for each divination type, each containing hyperlinks to the others
2. **Given** a structured input specifying multiple divinations (e.g., JSON array of requests), **When** the skill is invoked, **Then** the same cross-linked output files are produced identically to the natural language case
3. **Given** one sub-skill fails during multi-divination execution, **When** the skill handles the error, **Then** it continues executing remaining divinations and reports which ones succeeded/failed

---

### User Story 3 — Input Validation and Clarification (Priority: P1)

The skill must verify that all required input data is present and sensible before attempting any divination. If any field is missing, ambiguous, or implausible, the skill requests clarification rather than guessing. For multi-divination requests, validation occurs for each sub-skill independently.

**Why this priority**: Prevents silent failures and incorrect readings. A divination generated from bad data is worse than no reading at all.

**Independent Test**: Feed malformed or incomplete input to multiple sub-skills and verify that the skill rejects it with specific clarification requests, never producing output files from invalid data.

**Acceptance Scenarios**:

1. **Given** a gematria request without a name, **When** the skill validates, **Then** it asks for the name before proceeding
2. **Given** a bazi request with an ambiguous location (e.g., "Springfield" — 5+ matches), **When** the skill validates, **Then** it lists the possibilities and asks for disambiguation
3. **Given** a numerology request with a birth date in the future, **When** the skill validates, **Then** it asks the user to confirm or correct the date

---

### User Story 4 — Deterministic Routing and Reproducibility (Priority: P2)

The skill must use deterministic Python routing to select sub-skills based on user intent. The same input always produces the same output files with identical content. No randomness, no non-deterministic API calls during computation or rendering.

**Why this priority**: Correct routing is essential for accurate divination. A gematria request routed to numerology would be incorrect and misleading. Determinism ensures reproducibility — a user can re-run the same request and get the same reading.

**Independent Test**: Run the same multi-divination request 10 times and verify all output files are byte-identical across runs (sha256 checksums match).

**Acceptance Scenarios**:

1. **Given** a natural language request "do gematria on 'John Smith'", **When** the skill routes, **Then** it correctly invokes the gematria sub-skill (not numerology or bazi)
2. **Given** a structured input specifying multiple divinations, **When** the skill executes, **Then** each sub-skill is invoked with the correct input data and produces deterministic output
3. **Given** the same input provided twice, **When** the skill runs both times, **Then** all output files are byte-identical (same sha256 checksums)

---

### Edge Cases

- User requests a divination type that doesn't exist (e.g., "do tarot") — skill asks for clarification with a list of available types
- One sub-skill in a multi-divination chain fails (e.g., invalid birth data for bazi) — remaining sub-skills continue executing; output files are produced for successful ones, error reported for failed one
- Natural language input is ambiguous about which divination type(s) to use (e.g., "tell me about my name") — skill asks for clarification listing available options
- Input data required by one sub-skill is missing but not another (e.g., birth date provided but no birth time, needed for bazi houses but not gematria) — skill executes the divinations that have complete data and requests clarification only for the incomplete ones

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept divination requests in natural language free-text format and structured format (JSON, YAML)
- **FR-002**: System MUST route each request to the appropriate sub-skill (gematria, bazi, numerology) using deterministic intent matching based on user input keywords and structured type fields
- **FR-003**: System MUST validate all required input data for each requested divination before execution, requesting clarification for missing, ambiguous, or implausible data
- **FR-004**: System MUST support multiple divination requests in a single invocation, executing each sub-skill independently and producing separate output files per divination type
- **FR-005**: System MUST produce deterministic output files with deterministic naming conventions based on subject identifiers (e.g., initials for gematria/numerology, computed pillars for bazi)
- **FR-006**: System MUST include cross-links between output files when multiple divinations are requested in the same invocation (each HTML file contains hyperlinks to related files)
- **FR-007**: System MUST use deterministic computation methods — no randomness, no non-deterministic API calls during chart/divination generation
- **FR-008**: System MUST handle partial failures gracefully — if one sub-skill fails, remaining sub-skills continue executing and produce their output files

### Key Entities *(include if feature involves data)*

- **DivinationRequest**: The structured representation of a user's divination request. Attributes: list of requested divination types (gematria, bazi, numerology), input data per type (name, birth date/time/location as needed by each sub-skill), input format (natural language or structured)
- **RoutingDecision**: The output of the intent matching/routing layer. Attributes: matched divination type(s), confidence score, extracted input data fields, clarification requests if ambiguous
- **SubSkillExecution**: The result of executing a single sub-skill. Attributes: success/failure status, output file paths (HTML, JSON), error message if failed, execution time
- **OutputBundle**: The set of files produced for one invocation. Attributes: list of SubSkillExecution results, cross-link map (which files link to which), summary metadata

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of single-divination requests with complete valid input produce correct output files without manual intervention
- **SC-002**: Multiple divination requests (2-3 types) execute successfully in under 5 seconds end-to-end (excluding external API calls)
- **SC-003**: All invalid or incomplete inputs are rejected with specific clarification requests before any output file is created — zero charts produced from bad data
- **SC-004**: Deterministic routing correctly matches user intent to the appropriate sub-skill in at least 95% of test cases with unambiguous phrasing
- **SC-005**: Cross-links between output files are present and functional when multiple divinations are requested; absent when only one divination is requested
- **SC-006**: Partial failure handling succeeds — if one sub-skill fails, at least 80% of remaining valid requests still produce output files

## Assumptions

- The existing sub-skills (gematria, bazi, numerology) are stable and have deterministic APIs callable from Python
- The skill uses Python 3 with only standard library dependencies, as established in the project constitution
- Input data requirements for each sub-skill are defined by their existing contracts (e.g., gematria needs a name; bazi needs birth date/time/location)
- Output files live in a configurable output directory (default: current working directory)
- Cross-links are implemented as relative hyperlinks within HTML files, not as external metadata files
