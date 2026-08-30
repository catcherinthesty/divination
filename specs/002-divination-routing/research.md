# Research — Divination Routing Skill

## Decision: Intent Matching / Routing Strategy

**Decision**: Use keyword-based regex matching with a priority-ordered routing matrix, supplemented by structured type field detection in JSON/YAML input. No LLM or probabilistic parser is used for intent matching.

**Rationale**: Determinism is non-negotiable (constitution Principle I). An LLM-based router would produce different results for the same input across calls. Keyword regex matching is fully deterministic, fast (< 1ms), and covers all standard divination request phrasings. The routing matrix defines a fixed priority order so that ambiguous keywords (e.g., "number" could trigger gematria or numerology) resolve consistently.

**Implementation**: `src/skill/divination/router.py` contains a `ROUTING_MATRIX` list of `(keywords_regex, target_subskill, confidence_weight)` tuples, sorted by specificity (most specific first). When natural language input is provided:
1. Apply each regex in order; the first match wins (highest priority)
2. If multiple sub-skills are requested (e.g., "do gematria and numerology"), apply all matching rules
3. If structured input has a `type` or `divination` field, use it directly (bypasses keyword matching)
4. If no match found, return ClarificationRequest with list of available types

**Alternatives considered**:
1. **LLM-based intent classification** — High accuracy on complex phrasing but non-deterministic; violates Principle I; requires MCP call overhead per parse.
2. **Full NLP pipeline (spaCy/transformers)** — Deterministic but adds external dependencies; overkill for a fixed vocabulary of 3 divination types.
3. **Exact keyword list (no regex)** — Simpler but misses common phrasings like "tell me the gematria value of" vs "do gematria on".

## Decision: Output Naming Convention

**Decision**: Use `{subject_initials}_{divination_type}.{ext}` as the unified naming convention for all sub-skill outputs. For example:
- Gematria: `js_gematria.html`, `js_gematria.json`
- Numerology: `jd_numerology.html`, `jd_numerology.json`
- Bazi: Uses computed pillar initials from birth data (e.g., `renwu_bazi.html`) since bazi's output is traditionally named by its pillars

**Rationale**: This convention satisfies constitution Principle II (Standardized Output Contract) while respecting each sub-skill's existing naming patterns. Initials are generated deterministically using the existing `src/skill/renderer/naming.py.generate_initials()` function. The divination type suffix makes it immediately clear which file contains which reading.

**Implementation**: The linker module (`src/skill/divination/linker.py`) constructs filenames by combining:
1. Subject initials (from name field, or bazi pillars from birth data)
2. Divination type slug (`gematria`, `bazi`, `numerology`)
3. Extension (`html`, `json`)

**Alternatives considered**:
1. **UUID-based filenames** — Fully anonymous but hard to correlate with subjects; defeats human-readable file organization.
2. **Subject full name in filename** — Violates PII expungement policy (constitution Principle II + spec FR-007).
3. **Sub-skill original naming convention** — Gematria uses initials, bazi uses pillars, numerology uses initials. Inconsistent for multi-divination output sets.

## Decision: Cross-Link Format

**Decision**: Use relative HTML hyperlinks (`<a href="js_gematria.html">Gematria Reading</a>`) embedded in the `<nav>` section of each output HTML file when multiple divinations are requested in the same invocation. No external metadata files or link manifests are created.

**Rationale**: Relative hyperlinks are universally supported by all browsers, require no additional infrastructure, and create a navigable reading package where each file is self-contained yet connected to its siblings. This approach matches constitution Principle IV (Template-Based HTML Generation) — the cross-link section is added via template extension, not dynamic eval.

**Implementation**: `src/skill/divination/linker.py` processes output HTML files after sub-skill execution:
1. Parse the HTML to find the `<body>` element
2. Insert a `<nav class="cross-links">` block after the opening `<body>` tag
3. For each related file in the OutputBundle, add an `<a>` link with descriptive text
4. Write the modified HTML back atomically

If only one divination is requested, no cross-link nav is added (per spec SC-005).

**Alternatives considered**:
1. **Central index page** — A single HTML file linking to all outputs. Adds complexity and a fourth output file that doesn't map to any sub-skill's native format.
2. **JSON link manifest** — Separate `_links.json` file per subject. Violates the "separate files per divination type" principle; adds an external dependency for navigation.
3. **Inline text references** — Just mention related readings in the interpretation text. Not machine-readable and inconsistent across sub-skills.

## Decision: Sub-Skill Invocation Pattern

**Decision**: Invoke sub-skills as subprocesses via `python3 -m src.skill.<type>.main` with constructed CLI arguments. Each sub-skill's `main(argv)` entry point accepts an argv list and returns an exit code (0 = success, non-zero = failure). The router writes validated input data to a temporary JSON file and passes it as `--input`, directing output to a per-sub-skill temp directory. After execution, the router collects output files and injects cross-links.

**Rationale**: All three existing sub-skills (`gematria`, `bazi`, `numerology`) use CLI-oriented `main(argv) -> int` entry points — not library-style callable functions with structured return values. Subprocess invocation avoids refactoring existing code while maintaining clean isolation between the routing layer and sub-skill implementations. Each sub-skill handles its own validation, computation, and file writing; the router only collects results and adds cross-links. This matches constitution Principle III (Structured Data Pipeline) — each stage's output is the next stage's input, with subprocess boundaries ensuring no shared mutable state.

**Implementation**:
```python
import subprocess, sys, tempfile, json, os

# Write input to temp file (sub-skills read from --input via JSON format)
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(subskill_input_dict, f)
    input_path = f.name

output_dir = tempfile.mkdtemp()
result = subprocess.run(
    [sys.executable, "-m", "src.skill.gematria.main",
     "--input", input_path,
     "--output-dir", output_dir],
    capture_output=True, text=True, timeout=30
)
# result.returncode == 0 means success; collect files from output_dir
```

**Alternatives considered**:
1. **Direct function call** (`from .gematria.main import main; main([...])`) — Would require refactoring each sub-skill to expose a library-style API instead of CLI-only. Adds risk of breaking existing direct usage and requires changing all three sub-skills before the routing skill can work.
2. **MCP tool calls** — Overkill for local module imports; adds network IPC overhead when subprocess calls are available.
3. **Shared CLI entry point** — One `python3 -m src.skill` command with subcommands. Works but requires the routing skill to parse and forward CLI args, duplicating argument handling logic across three sub-skills.

## Decision: Input Data Sharing Across Sub-Skills

**Decision**: Each divination type declares its required fields. The validator collects all required fields across requested sub-skills, validates them once, and distributes the relevant subset to each sub-skill. For example, if gematria (needs name) and bazi (needs birth date/time/location) are both requested, the input must contain name + birth data; gematria uses only the name field, bazi uses only the birth data fields.

**Rationale**: Avoids duplicate validation of shared fields (e.g., `name` is validated once even though it's used by both gematria and numerology). Matches constitution Principle III — one validation stage, multiple consumers. Also enables partial success: if birth time is missing (needed for bazi houses but not gematria), gematria can still execute while bazi requests clarification only for the time field.

**Implementation**: `src/skill/divination/validator.py` maintains a `REQUIRED_FIELDS` mapping per sub-skill type, merges them across all requested types, and produces a unified set of ClarificationRequests. Each ClarificationRequest is tagged with which sub-skill(s) require the field, enabling targeted clarification (e.g., "birth time missing — needed for bazi houses").

**Alternatives considered**:
1. **Per-sub-skill validation** — Validate independently for each sub-skill. Simpler code but duplicates effort and produces redundant ClarificationRequests when fields are shared.
2. **Schema-based validation with JSON Schema** — Adds external dependency (jsonschema not in stdlib) and complexity for a fixed set of 3 sub-skills.
