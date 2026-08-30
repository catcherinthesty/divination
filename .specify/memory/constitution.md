<!-- SYNC IMPACT REPORT — v0.0.0 → v1.0.0
Version change: 0.0.0 (empty scaffold) → 1.0.0
Added principles: I. Deterministic Computation, II. Standardized Output Contract, III. Structured Data Pipeline, IV. Template-Based HTML Generation, V. Non-Romantic Synastry First
Added sections: Technology Stack, Quality Gates
Removed sections: none (was empty scaffold)
Deferred items: none — all template placeholders resolved
-->
# Astrology Charting Project Constitution

## Core Principles

### I. Deterministic Computation
All astrological calculations MUST use deterministic, reproducible methods. Skyfield is the canonical astronomical library; all planetary positions must be traceable to its ephemeris. No randomness or non-deterministic approximations are permitted in chart calculations. Every output file (SVG, HTML, JSON) must be fully reproducible from the same birth data input — running the same script twice with identical inputs MUST produce byte-identical outputs.

### II. Standardized Output Contract
Every chart generation pipeline produces a predictable set of files following strict naming conventions: `bakl_chart.svg`, `bakl_chart.html` for Bristol; `arh_chart.svg`, `arh_chart.html` for Aria. Relationship charts use the prefix pattern `<p1_initials>_<p2_initials>_relation.{svg,html}`. All JSON responses are stored in `api_call.json` with input, URL, and output fields. File formats are fixed: SVG for the chart wheel, HTML for the analysis page, JSON for raw data. No ad-hoc filenames or format variations.

### III. Structured Data Pipeline
The pipeline follows a strict three-stage flow: (1) Input — structured birth data as JSON with name, date/time, location, timezone; (2) Computation — MCP API call returns `chart_data` + SVG string; (3) Rendering — deterministic script consumes the response and produces output files. Each stage's output is the next stage's input. No manual intervention between stages. Scripts read from a single known response file path and write to known project paths.

### IV. Template-Based HTML Generation
All HTML analysis pages are generated from templates, not hand-written. Templates use Python f-string interpolation with explicit variable names — no dynamic eval or template injection. Every template section (planet table, house cusps, aspects, elements, interpretation) maps one-to-one to fields in the API response. Interpretation text uses lookup tables keyed by sign name, ensuring consistent tone and terminology across all charts.

### V. Non-Romantic Synastry First
Relationship charts are designed for family and non-romantic bonds. The synastry HTML emphasizes house overlays, shared elemental/quality distributions, and interpretive text focused on kinship dynamics (parent-child, sibling, guardian) rather than romantic compatibility. Score descriptions and aspect interpretations are framed in family-appropriate language.

## Technology Stack

Python 3 is the sole scripting language. All scripts must run without external dependencies beyond the standard library — MCP tool calls handle all network communication. SVG generation is delegated to the Astrologer MCP API; local scripts only consume and embed the SVG string. HTML output uses embedded CSS (no external stylesheets). JSON is the universal data interchange format for both input and intermediate storage.

## Quality Gates

Every generated chart MUST pass these checks before acceptance:
- SVG file renders without errors in a browser (valid XML, correct dimensions)
- HTML file contains all expected sections: key cards, planet table, house cusps, aspects, elements/qualities, interpretation
- Planet positions match the API response exactly (no truncation or rounding errors beyond display precision)
- Aspect orbs are sorted by tightness in the output table
- Interpretation text uses correct sign names and house numbers — no typos like "Fifthth" or "Eleventhth"

## Governance

This constitution defines the non-negotiable rules for all chart generation in this project. Any deviation requires amending the relevant principle. The `generate_chart.py` / `generate_charts.py` scripts are the authoritative implementation of these principles; if a script's behavior conflicts with a principle, the principle takes precedence and the script must be corrected.

**Version**: 1.0.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-08-27
