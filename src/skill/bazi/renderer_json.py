"""JSON renderer for Ba Zi reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .calculations import compute_all
from .data_types import (
    BaziRecord,
    Gender,
    STEM_CHAR,
    BRANCH_CHAR,
)
from .interpretations import analyze_element_balance, get_day_master_profile


def render_json(
    record: BaziRecord,
    gender: Gender,
    output_dir: str | Path = ".",
) -> str:
    """Generate a JSON Ba Zi report.

    Returns the path to the written file as a string.
    """
    from ..renderer.naming import generate_initials

    result = compute_all(record)
    initials = generate_initials(record.name)

    def _pillar_to_dict(pillar) -> dict[str, Any]:
        sb = pillar.stem_branch
        return {
            "label": pillar.label,
            "stem": {
                "index": sb.stem_index,
                "chinese": STEM_CHAR[sb.stem_index],
                "english": f"{sb.stem_index}",
                "element": result.element_counts.get("Wood", 0),  # Placeholder
            },
            "branch": {
                "index": sb.branch_index,
                "chinese": BRANCH_CHAR[sb.branch_index],
                "hidden_stems": pillar.hidden_stems,
            },
        }

    data: dict[str, Any] = {
        "subject": {
            "name": record.name,
            "date_of_birth": result.birth_date.isoformat(),
            "gender": gender.value,
            "hour": result.hour,
        },
        "day_master": {
            "element": result.day_master_element,
            "yin_yang": result.day_master_yin_yang,
            "profile": get_day_master_profile(result.day_master_yin_yang, result.day_master_element),
        },
        "pillars": {
            "year": _pillar_to_dict(result.year_pillar),
            "month": _pillar_to_dict(result.month_pillar),
            "day": _pillar_to_dict(result.day_pillar),
            "hour": _pillar_to_dict(result.hour_pillar),
        },
        "element_analysis": {
            "counts": result.element_counts,
            "balance": analyze_element_balance(result.element_counts),
        },
        "luck_pillars": [
            {
                "stem_branch": f"{lp.stem_branch.stem_index}/{lp.stem_branch.branch_index}",
                "start_age": lp.start_age,
                "year_range": lp.year_range,
            }
            for lp in result.luck_pillars
        ],
    }

    out = Path(output_dir)
    path = out / f"{initials}_bazi.json"
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(content, encoding="utf-8")
    return str(path)
