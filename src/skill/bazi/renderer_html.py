"""HTML renderer for Ba Zi reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .calculations import compute_all
from .data_types import BaziRecord, Gender
from .interpretations import (
    DAY_MASTER_PROFILES,
    PILLAR_MEANINGS,
    analyze_element_balance,
    get_day_master_profile,
    get_element_description,
)


def _elem_badge(elem: str) -> str:
    """HTML badge for an element."""
    colors = {"Wood": "#27ae60", "Fire": "#e74c3c", "Earth": "#d35400", "Metal": "#95a5a6", "Water": "#2980b9"}
    color = colors.get(elem, "#7f8c8d")
    return f'<span class="elem-badge" style="background:{color}">{elem}</span>'


def render_html(
    record: BaziRecord,
    gender: Gender,
    output_dir: str | Path = ".",
) -> str:
    """Generate a full HTML Ba Zi report.

    Returns the path to the written file as a string.
    """
    from ..renderer.chart_writer import atomic_write
    from ..renderer.naming import generate_initials
    from .renderer import render_bazi_wheel

    result = compute_all(record)
    initials = generate_initials(record.name)

    # Build SVG wheel inline
    svg_content = render_bazi_wheel(result, width=700, height=850)

    # Element balance
    balance = analyze_element_balance(result.element_counts)

    # Day master profile
    dm_profile = get_day_master_profile(result.day_master_yin_yang, result.day_master_element)

    def _pillar_card(pillar: Any) -> str:
        sb = pillar.stem_branch
        from .data_types import STEMS_EN, BRANCHES_EN, STEMS_ELEMENT, BRANCHES_YIN_YANG
        stem_en = STEMS_EN[sb.stem_index]
        branch_en = BRANCHES_EN[sb.branch_index]
        stem_elem = STEMS_ELEMENT[sb.stem_index]
        branch_yy = BRANCHES_YIN_YANG[sb.branch_index]

        meaning = PILLAR_MEANINGS.get(pillar.label, {})

        return f"""<div class="pillar-card">
  <h3>{pillar.label}</h3>
  <div class="pillar-values">
    <span class="stem">{stem_en.split('(')[0].strip()}</span>
    <span class="branch">{branch_en.split('(')[0].strip()}</span>
  </div>
  <p class="pillar-detail">{stem_elem} / {branch_yy}</p>
  <p class="hidden-stems">Hidden stems: {pillar.hidden_stems or '—'}</p>
  <p class="pillar-meaning"><strong>Area:</strong> {meaning.get('area', '')}</p>
</div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ba Zi Report — {record.name}</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #2c3e50; background: #fafbfc; }}
  h1 {{ text-align: center; color: #2c3e50; border-bottom: 2px solid #e74c3c; padding-bottom: 0.5rem; }}
  h2 {{ color: #34495e; margin-top: 2rem; border-left: 4px solid #e74c3c; padding-left: 1rem; }}
  .subtitle {{ text-align: center; color: #7f8c8d; font-size: 1.1rem; margin-bottom: 2rem; }}
  .wheel-container {{ text-align: center; margin: 2rem 0; }}
  .wheel-container svg {{ max-width: 100%; height: auto; }}
  .pillars-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin: 2rem 0; }}
  @media (max-width: 700px) {{ .pillars-grid {{ grid-template-columns: 1fr 1fr; }} }}
  .pillar-card {{ background: #fff; border-radius: 8px; padding: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; }}
  .pillar-card h3 {{ margin-top: 0; color: #e74c3c; }}
  .pillar-values {{ display: flex; justify-content: center; gap: 1rem; font-size: 2rem; font-weight: bold; margin: 1rem 0; }}
  .stem {{ color: #c0392b; }}
  .branch {{ color: #2980b9; }}
  .pillar-detail {{ color: #7f8c8d; font-size: 0.9rem; margin: 0.5rem 0; }}
  .hidden-stems {{ font-size: 0.8rem; color: #95a5a6; }}
  .pillar-meaning {{ font-size: 0.85rem; color: #555; text-align: left; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #ecf0f1; }}
  .elem-badges {{ display: flex; gap: 0.5rem; justify-content: center; margin: 1rem 0; }}
  .elem-badge {{ padding: 0.25rem 0.75rem; border-radius: 4px; color: #fff; font-size: 0.85rem; font-weight: bold; }}
  .dm-profile {{ background: #fff3e0; border-left: 4px solid #d35400; padding: 1.5rem; margin: 2rem 0; border-radius: 4px; }}
  .dm-profile h3 {{ margin-top: 0; color: #d35400; }}
  .luck-pillars {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin: 1rem 0; }}
  @media (max-width: 600px) {{ .luck-pillars {{ grid-template-columns: 1fr 1fr; }} }}
  .luck-card {{ background: #f8f9fa; padding: 0.75rem; border-radius: 4px; text-align: center; font-size: 0.85rem; }}
  .footer {{ text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ecf0f1; color: #95a5a6; font-size: 0.85rem; }}
</style>
</head>
<body>

<h1>Ba Zi — Four Pillars of Destiny</h1>
<p class="subtitle">{record.name} · Born {result.birth_date.isoformat()} · Gender: {gender.value}</p>

<div class="wheel-container">
{svg_content}
</div>

<h2>Day Master Profile</h2>
<div class="dm-profile">
  <h3>{dm_profile['title']}</h3>
  <p>{dm_profile['description']}</p>
  <p><strong>Strengths:</strong> {', '.join(dm_profile['strengths'])}</p>
  <p><strong>Challenges:</strong> {', '.join(dm_profile['challenges'])}</p>
</div>

<h2>The Four Pillars</h2>
<div class="pillars-grid">
{_pillar_card(result.year_pillar)}
{_pillar_card(result.month_pillar)}
{_pillar_card(result.day_pillar)}
{_pillar_card(result.hour_pillar)}
</div>

<h2>Element Balance</h2>
<div class="elem-badges">
{" ".join(f'<span class="elem-badge">{_elem_badge(k)}</span>: {v}' for k, v in result.element_counts.items())}
</div>
<p><strong>Dominant:</strong> {_elem_badge(balance['dominant_element'])} ({balance['dominant_percentage']}%)</p>
<p><strong>Weakest:</strong> {_elem_badge(balance['weakest_element'])} ({balance['weakest_percentage']}%)</p>
<p><strong>Balanced:</strong> {'Yes ✓' if balance['is_balanced'] else 'No — consider elemental remedies'}.</p>

<h2>Luck Pillars (大运)</h2>
<div class="luck-pillars">
  {" ".join(f'<div class="luck-card"><strong>Ages {lp.start_age}-{lp.start_age + 9}</strong><br>{lp.stem_branch.stem_index}/{lp.stem_branch.branch_index}<br>{lp.year_range}</div>' for lp in result.luck_pillars[:8])}
</div>

<div class="footer">
  <p>Generated by the Ba Zi Skill · Based on the Chinese Sexagenary Cycle</p>
  <p><em>Note: Month pillar calculations use solar term approximations. For precise results, consult a professional practitioner.</em></p>
</div>

</body>
</html>"""

    out = Path(output_dir)
    path = out / f"{initials}_bazi.html"
    atomic_write(path, html)
    return str(path)
