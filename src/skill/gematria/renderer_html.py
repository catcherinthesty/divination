"""HTML renderer for Gematria reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..renderer.chart_writer import atomic_write
from .calculations import compute_all
from .data_types import GematriaRecord, System
from .interpretations import (
    CORE,
    FAMOUS_PAIRS,
    SYSTEM_NOTES,
    format_interpretation,
    get_core_interpretation,
)


def render_html(
    record: GematriaRecord,
    initials: str,
    output_dir: str | Path = ".",
) -> str:
    """Generate an HTML gematria report.

    Returns the path to the written file as a string.
    """
    result = compute_all(record)
    out = Path(output_dir)

    # Build system cards
    systems_order = [System.SIMPLE, System.ORDINAL, System.REVERSE]
    system_colors = {"simple": "#2980b9", "ordinal": "#27ae60", "reverse": "#e74c3c"}
    system_labels = {"simple": "Simple (Pythagorean)", "ordinal": "Full Ordinal", "reverse": "Reverse Ordinal"}

    cards_html = ""
    for sys_obj in systems_order:
        if sys_obj not in result.results:
            continue
        sr = result.results[sys_obj]
        color = system_colors.get(sys_obj.value, "#333")
        label = system_labels.get(sys_obj.value, sys_obj.value)

        # Word breakdown table
        word_rows = ""
        for wd in sr.words:
            word_rows += (
                f'<tr><td>{wd.word}</td><td>{wd.total}</td><td>{wd.reduced}</td>'
                f'<td style="color:#8e44ad">{wd.vowel_total}</td>'
                f'<td style="color:#6c3483">{wd.consonant_total}</td></tr>\n'
            )

        # Letter breakdown from words
        all_pairs = []
        for wd in sr.words:
            all_pairs.extend(wd.letter_values)
        letter_parts = [f"{ch}={v}" for ch, v in all_pairs if v > 0]

        total_breakdown = ""
        if hasattr(sr, 'total_breakdown') and sr.total_breakdown:
            total_breakdown = sr.total_breakdown

        # Interpretation
        interp = get_core_interpretation(sr.reduced)
        interp_html = f'<div class="interp"><strong>{interp.get("title", "")}</strong><br>{interp.get("summary", "")}'
        strengths = interp.get("strengths", [])
        challenges = interp.get("challenges", [])
        if strengths:
            interp_html += f'<br><em>Strengths:</em> {", ".join(str(s) for s in strengths)}'
        if challenges:
            interp_html += f'<br><em>Challenges:</em> {", ".join(str(c) for c in challenges)}'
        interp_html += '</div>'

        # Famous pairs
        famous = FAMOUS_PAIRS.get(sr.reduced, [])
        famous_html = ""
        if famous:
            famous_html = '<div class="famous-pairs"><strong>Famous Pairs:</strong><br>'
            for val, desc in famous[:6]:
                famous_html += f"{val} — {desc}<br>"
            famous_html += '</div>'

        cards_html += f"""<div class="card">
            <h3 style="color:{color}">{label}</h3>
            <div class="big-number" style="border-color:{color}">{sr.total}</div>
            <div class="reduced" style="color:{color}">{sr.reduced}</div>
            {interp_html}
            {famous_html}
            <table class="word-table">
                <thead><tr><th>Word</th><th>Total</th><th>Red.</th><th>Vowels</th><th>Cons.</th></tr></thead>
                <tbody>{word_rows}</tbody>
            </table>
        </div>"""

    # Comparison table
    comp_rows = ""
    for sys_obj in systems_order:
        if sys_obj not in result.results:
            continue
        sr = result.results[sys_obj]
        comp_rows += f'<tr><td>{system_labels.get(sys_obj.value, sys_obj.value)}</td>'
        comp_rows += f'<td class="num">{sr.total}</td><td class="num reduced-num">{sr.reduced}</td>'
        comp_rows += f'<td class="num">{sr.initials_value if hasattr(sr, "initials_value") else sr.initials_value}</td></tr>\n'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gematria — {result.name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #f8f9fa; color: #2c3e50; padding: 2rem; }}
  h1 {{ text-align: center; margin-bottom: 0.5rem; font-size: 1.8rem; }}
  .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 2rem; font-size: 0.95rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
  .card {{ background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border-top: 4px solid #333; }}
  .big-number {{ font-size: 3rem; font-weight: bold; text-align: center; padding: 1rem 0; border-bottom: 2px solid #eee; margin: 0.5rem 0; }}
  .reduced {{ font-size: 1.5rem; font-weight: bold; text-align: center; color: #e67e22; }}
  .interp {{ padding: 0.8rem 0; font-size: 0.9rem; line-height: 1.5; border-bottom: 1px solid #eee; margin-bottom: 0.8rem; }}
  .famous-pairs {{ font-size: 0.85rem; color: #666; padding: 0.5rem 0; }}
  .word-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-top: 0.5rem; }}
  .word-table th {{ text-align: left; padding: 0.4rem; border-bottom: 2px solid #eee; color: #999; font-weight: 600; }}
  .word-table td {{ padding: 0.3rem 0.4rem; border-bottom: 1px solid #f5f5f5; }}
  .comparison {{ background: #fff; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
  .comparison h3 {{ margin-bottom: 1rem; }}
  .comp-table {{ width: 100%; border-collapse: collapse; }}
  .comp-table th {{ text-align: left; padding: 0.6rem; border-bottom: 2px solid #eee; color: #999; }}
  .comp-table td {{ padding: 0.6rem; border-bottom: 1px solid #f5f5f5; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }}
  .reduced-num {{ color: #e67e22; font-size: 1.1rem; }}
</style>
</head>
<body>
<div class="container">
    <h1>Gematria Report — {result.name}</h1>
    <p class="subtitle">Three systems compared · {len(result.results)} system(s) computed</p>
    <div class="cards">{cards_html}</div>
    <div class="comparison">
        <h3>System Comparison</h3>
        <table class="comp-table">
            <thead><tr><th>System</th><th>Total</th><th>Reduced</th><th>Initials</th></tr></thead>
            <tbody>{comp_rows}</tbody>
        </table>
    </div>
</div>
</body>
</html>"""

    path = out / f"{initials}_gematria.html"
    atomic_write(str(path), html)
    return str(path)
