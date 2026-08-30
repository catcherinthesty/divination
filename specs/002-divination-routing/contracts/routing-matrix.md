# Routing Matrix — Divination Intent Matching Reference

This document defines the deterministic keyword-to-sub-skill mapping used by `src/skill/divination/router.py`. Entries are evaluated in order (first match wins for ambiguous keywords).

## Gematria Keywords

| Pattern | Regex | Confidence | Notes |
|---------|-------|------------|-------|
| "gematria" | `\bgematria\b` | high | Primary keyword — always matches gematria |
| "hebrew number" | `\b(?:hebrew|hewbrish)\s+number(?:s)?\b` | medium | Common alternate phrasing |
| "name number" | `\bname\s+(?:number|value|sum)\b` | medium | Ambiguous — could be gematria or numerology; gematria takes priority |
| "letter value" | `\b(?:letter|alphabetic)\s+value\b` | low | Rare phrasing |

## Numerology Keywords

| Pattern | Regex | Confidence | Notes |
|---------|-------|------------|-------|
| "numerology" | `\bnumerology\b` | high | Primary keyword — always matches numerology |
| "life path" | `\blife\s+path\b` | medium | Common numerology phrasing |
| "birth number" | `\bbirth\s+(?:number|date)\b` | medium | Ambiguous — could be numerology or bazi; numerology takes priority |
| "name analysis" | `\b(?:name|naming)\s+analysis\b` | low | Rare phrasing, defaults to numerology |

## Bazi Keywords

| Pattern | Regex | Confidence | Notes |
|---------|-------|------------|-------|
| "bazi" | `\bbazi\b` | high | Primary keyword — always matches bazi |
| "four pillars" | `\bfour\s+pillars?\b` | medium | Common alternate phrasing |
| "Chinese astrology" | `\b(?:chinese|liu)\s+astrolog(y|ical)\b` | medium | Broad but consistently maps to bazi |
| "mingli" | `\bming.?li\b` | low | Less common romanization |

## Disambiguation Rules

1. **"name number"** → gematria (higher priority than numerology's "birth number")
2. **"birth date"** alone → no match (ambiguous; triggers clarification)
3. **Multiple keywords matching different types** → all matched types are executed (e.g., "gematria and life path" → both gematria and numerology)
4. **No keyword match** → ClarificationRequest with list of available types: gematria, bazi, numerology

## Structured Input Override

When input is JSON/YAML with a `divination_types` field, the routing matrix is bypassed entirely. The `divination_types` values are validated against the allowed set (`gematria`, `bazi`, `numerology`) and used directly.
