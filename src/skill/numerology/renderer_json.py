"""JSON renderer for numerology reports.

Produces a machine-readable JSON file with all core numbers,
breakdowns, and interpretations for both systems.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .calculations import compute_all
from .data_types import NumerologyRecord
from .interpretations import get_interpretation


def _core_to_dict(core) -> dict[str, Any]:
    """Serialize a CoreNumbers to dict."""
    cats = [
        ("life_path", core.life_path, core.life_path_breakdown),
        ("expression", core.expression, core.expression_breakdown),
        ("soul_urge", core.soul_urge, core.soul_urge_breakdown),
        ("personality", core.personality, core.personality_breakdown),
        ("birthday", core.birthday, core.birthday_breakdown),
    ]
    numbers: dict[str, Any] = {}
    for cat, num, breakdown in cats:
        interp = get_interpretation(cat, num)
        numbers[cat] = {
            "number": num,
            "is_master": num in (11, 22, 33),
            "breakdown": breakdown,
            "interpretation": interp,
        }
    return numbers


def render_json(
    record: NumerologyRecord,
    initials: str = "",
    output_dir: str | Path = ".",
) -> str:
    """Generate a JSON numerology report.

    Returns the path to the written file as a string.
    """
    from ..renderer.naming import generate_initials

    if not initials:
        initials = generate_initials(record.full_name)

    pyth, chald = compute_all(record)

    data: dict[str, Any] = {
        "subject": {
            "name": record.full_name,
            "date_of_birth": record.date_of_birth.isoformat(),
        },
        "systems": {
            "pythagorean": _core_to_dict(pyth),
            "chaldean": _core_to_dict(chald),
        },
        "meta": {
            "generated_by": "numerology-skill",
            "master_numbers_note": "Master numbers (11, 22, 33) are not reduced to single digits.",
        },
    }

    out = Path(output_dir)
    path = out / f"{initials}_numerology.json"
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(content, encoding="utf-8")
    return str(path)
