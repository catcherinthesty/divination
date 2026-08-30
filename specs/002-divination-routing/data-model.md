# Data Model — Divination Routing Skill

## Entity: DivinationRequest

The structured representation of a user's divination request. This is the canonical input that flows through the parser → router → validator pipeline before sub-skill execution.

### Fields

| Field | Type | Required | Validation | Source |
|-------|------|----------|------------|--------|
| `divination_types` | list of strings | Yes | Each string must be one of: `"gematria"`, `"bazi"`, `"numerology"`; max 3 types per request | FR-002, FR-004 |
| `name` | string | Conditionally | Required for gematria and numerology. Non-empty, 1–80 chars, alphabetic + spaces/hyphens/apostrophes. Not required for bazi (uses birth data). | FR-003, US-3 |
| `date_of_birth` | string (YYYY-MM-DD) | Conditionally | Required for bazi and numerology. Valid date ≤ today, ≥ 150 years in past. Not required for gematria. | FR-003, edge case |
| `time_of_birth` | string (HH:MM) or null | Optional | If present: 00:00–23:59. Null is acceptable for gematria; triggers house approximation warning for bazi. | FR-009 |
| `location_description` | string | Conditionally | Required for bazi. Non-empty; used for geocoding lookup. Not required for gematria or numerology. | FR-004 |
| `latitude` | float | Optional | If provided: −90.0 to 90.0. Only relevant for bazi. | Edge case |
| `longitude` | float | Optional | If provided: −180.0 to 180.0. Only relevant for bazi. | Edge case |
| `timezone` | string (IANA) | Optional | If provided: must be a valid IANA timezone identifier. Inferred from location for bazi if absent. | FR-008 |
| `gematria_systems` | list of strings | Optional | For gematria only. Supported values: `"english"`, `"hebrew"`, `"simple"`. Default: `["english"]`. | Assumption |
| `numerology_systems` | list of strings | Optional | For numerology only. Supported values: `"pythagorean"`, `"chaldean"`. Default: `["pythagorean"]`. | Assumption |
| `input_format` | enum: `{natural-language, json, yaml}` | Auto-detected | Determined from input source (file extension or CLI flag). Not user-provided. | FR-001 |

### Relationships

- DivinationRequest → RoutingDecision (one-to-one): the request is routed to one or more sub-skills based on `divination_types`.
- DivinationRequest → ClarificationRequest (one-to-many): validation may produce zero, one, or multiple clarification requests before sub-skill execution.
- DivinationRequest → list of SubSkillExecution (one-to-many): each requested divination type produces one execution result.

### State Transitions

```
Received → Parsed → Validating → Routing → Executing → Complete
                                       ↑              ↓
                                       └── Clarifying ←──┘
```

1. **Received**: Raw input text or structured data received from user.
2. **Parsed**: Input converted to DivinationRequest dict (or raises on parse failure).
3. **Validating**: Required fields checked per sub-skeleton; ClarificationRequests produced for missing/invalid data.
4. **Routing**: Intent matched to sub-skills via router.py keyword regex or structured type field.
5. **Executing**: Sub-skills called in sequence; each produces ChartOutput.
6. **Complete**: All outputs written with cross-links injected; OutputBundle returned.

### Validation Rules (from FR-003, US-3)

- `divination_types` must contain at least one valid type from the routing matrix. Unknown types trigger ClarificationRequest with list of available types.
- `name` is required if any requested type is gematria or numerology. Validated per existing BirthRecord rules (1–80 chars, alphabetic + spaces/hyphens/apostrophes).
- `date_of_birth` is required if any requested type is bazi or numerology. Validated: ≤ today, ≥ 150 years in past.
- `location_description` is required for bazi. Must resolve to coordinates via the shared geocoder lookup table.
- If multiple types share a field (e.g., gematria + numerology both need `name`), the field is validated once and distributed to both sub-skills.

---

## Entity: RoutingDecision

The output of the intent matching/routing layer. Maps a parsed DivinationRequest to one or more sub-skill invocations.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `matched_types` | list of strings | Sub-skills selected for execution (e.g., `["gematria", "numerology"]`) |
| `confidence` | enum: `{high, medium, low}` | high = structured type field match; medium = keyword regex matched unambiguously; low = ambiguous keywords requiring clarification |
| `input_data_by_type` | dict[str, dict] | Partitioned input data: each sub-skill gets only the fields it needs (e.g., gematria gets `{name}`, bazi gets `{date_of_birth, location_description, timezone}`) |
| `clarification_requests` | list of ClarificationRequest | If confidence is low or no match found, contains requests to disambiguate user intent |

### Relationships

- RoutingDecision ← DivinationRequest (one-to-one): each parsed request produces exactly one routing decision.
- RoutingDecision → SubSkillExecution (one-to-many): each matched type triggers one sub-skill execution.

---

## Entity: SubSkillExecution

The result of executing a single sub-skill within the routing pipeline. Produced by calling the sub-skill's `main()` function with partitioned input data.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `divination_type` | string | The sub-skill that was executed (`"gematria"`, `"bazi"`, or `"numerology"`) |
| `status` | enum: `{success, failed}` | Whether the sub-skill completed successfully or raised an error |
| `output_files` | list of strings | File paths produced by this sub-skill (e.g., `["js_gematria.html", "js_gematria.json"]`) |
| `error_message` | string or null | Error description if status is `failed`; None if successful |
| `execution_time_ms` | float | Time taken to execute the sub-skill (for performance monitoring) |

### Relationships

- SubSkillExecution ← RoutingDecision (one-to-one per matched type): each routing decision triggers one execution per matched type.
- SubSkillExecution → OutputBundle: all executions are collected into a single OutputBundle for cross-link injection.

---

## Entity: OutputBundle

The set of files produced for one divination invocation. This is the final output of the routing pipeline, containing results from all successfully executed sub-skills with cross-links injected.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `executions` | list of SubSkillExecution | All sub-skill execution results (success and failed) |
| `cross_links` | dict[str, list[str]] | Map from each output file path to the list of related file paths it should link to |
| `summary` | dict | Metadata: total types requested, total types succeeded, total files produced, total execution time |

### Relationships

- OutputBundle ← SubSkillExecution (one-to-many): collected from all successful executions in a single invocation.
- OutputBundle → filesystem: files are written atomically; cross-links are injected into HTML files before final write.

### Cross-Link Injection Process

1. After all sub-skills execute successfully, collect the list of output file paths.
2. For each HTML output file, inject a `<nav class="cross-links">` block after `<body>`.
3. The nav contains one `<a>` per related divination type (e.g., "Gematria Reading", "Numerology Reading").
4. Links use relative paths (e.g., `href="js_gematria.html"`).
5. If only one sub-skill succeeded, no cross-link nav is added (per spec SC-005).
