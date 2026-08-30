"""JSON renderer for Gematria reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..renderer.chart_writer import atomic_write
from .calculations import compute_all
from .data_types import GematriaRecord, System
from .interpretations import get_core_interpretation, get_famous_pairs


def render_json(
    record: GematriaRecord,
    initials: str,
    output_dir: str | Path = ".",
) -> str:
    """Generate a JSON gematria report.

    Returns the path to the written file as a string.
    """
    result = compute_all(record)
    out = Path(output_dir)

    def _word_to_dict(wd) -> dict[str, Any]:
        return {
            "word": wd.word,
            "total": wd.total,
            "reduced": wd.reduced,
            "vowel_total": wd.vowel_total,
            "consonant_total": wd.consonant_total,
            "letter_values": [{"letter": ch, "value": v} for ch, v in wd.letter_values],
        }

    def _system_to_dict(sys_obj: System, sr) -> dict[str, Any]:
        interp = get_core_interpretation(sr.reduced)
        famous = get_famous_pairs(sr.reduced)

        data: dict[str, Any] = {
            "system": sys_obj.value,
            "total": sr.total,
            "reduced": sr.reduced,
            "initials_value": sr.initials_value if hasattr(sr, 'initials_value') else 0,
            "words": [_word_to_dict(wd) for wd in sr.words],
            "interpretation": {
                "title": interp.get("title", ""),
                "summary": interp.get("summary", ""),
                "strengths": interp.get("strengths", []),
                "challenges": interp.get("challenges", []),
            },
        }

        if famous:
            data["famous_pairs"] = [{"number": n, "description": d} for n, d in famous[:10]]

        return data

    systems_order = [System.SIMPLE, System.ORDINAL, System.REVERSE]
    systems_data = {}
    for sys_obj in systems_order:
        if sys_obj in result.results:
            systems_data[sys_obj.value] = _system_to_dict(sys_obj, result.results[sys_obj])

    data: dict[str, Any] = {
        "subject": {
            "name": result.name,
            "initials": result.initials,
        },
        "systems_computed": [s.value for s in result.results.keys()],
        "systems": systems_data,
        "meta": {
            "version": "1.0",
            "description": "Gematria analysis using English letter-to-number systems",
        },
    }

    path = out / f"{initials}_gematria.json"
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    atomic_write(str(path), content)
    return str(path)
