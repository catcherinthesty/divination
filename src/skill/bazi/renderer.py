"""SVG Ba Zi wheel chart renderer.

Produces a deterministic four-pillars layout with element colors,
hidden stems, and luck pillar indicators.

Same record always produces byte-identical SVG (constitution Principle I).
"""

from __future__ import annotations

from typing import Any

from .data_types import BaziResult, Gender, Pillar, StemBranch
from .data_types import STEMS_ELEMENT, BRANCHES_ELEMENT


def render_bazi_wheel(result: BaziResult, width: int = 700, height: int = 850) -> str:
    """Render a Ba Zi four-pillars chart as an SVG string.

    Layout:
      - Four pillars arranged left-to-right: Year | Month | Day | Hour
      - Each pillar shows stem (top), branch (bottom), hidden stems
      - Element colors for each character
      - Luck pillar summary at bottom
    """
    ns = "http://www.w3.org/2000/svg"
    pillar_width = 140
    pillar_height = 500
    start_x = (width - pillar_width * 4) // 2
    top_y = 80

    # Element colors for background highlighting
    elem_colors = {
        "Wood": "#e8f5e9", "Fire": "#ffebee", "Earth": "#fff3e0",
        "Metal": "#eceff1", "Water": "#e3f2fd",
    }

    def _pillar_svg(pillar: Pillar, x: int, y: int) -> list[str]:
        """Render a single pillar as SVG elements."""
        sb = pillar.stem_branch
        primary_elem = STEMS_ELEMENT[sb.stem_index]
        bg_color = elem_colors.get(primary_elem, "#f5f5f5")

        elements: list[str] = []

        # Pillar box
        elements.append(
            f'<rect x="{x}" y="{y}" width="{pillar_width}" height="{pillar_height}" '
            f'fill="{bg_color}" stroke="#333" stroke-width="1.5" rx="8"/>'
        )

        # Pillar label
        elements.append(
            f'<text x="{x + pillar_width // 2}" y="{y - 10}" text-anchor="middle" '
            f'font-size="14" font-weight="bold" fill="#333" font-family="system-ui">'
            f'{pillar.label}</text>'
        )

        # Stem (top half) — Chinese character + English name
        stem_y = y + 120
        elements.append(
            f'<text x="{x + pillar_width // 2}" y="{stem_y}" text-anchor="middle" '
            f'font-size="48" font-weight="bold" fill="#c0392b" font-family="system-ui">'
            f'{sb.stem_index}</text>'
        )

        # Branch (bottom half)
        branch_y = y + 350
        elements.append(
            f'<text x="{x + pillar_width // 2}" y="{branch_y}" text-anchor="middle" '
            f'font-size="48" font-weight="bold" fill="#2980b9" font-family="system-ui">'
            f'{sb.branch_index}</text>'
        )

        # Hidden stems (small text at bottom)
        if pillar.hidden_stems:
            elements.append(
                f'<text x="{x + pillar_width // 2}" y="{y + pillar_height - 20}" '
                f'text-anchor="middle" font-size="10" fill="#666" font-family="system-ui">'
                f'Hidden: {pillar.hidden_stems}</text>'
            )

        # Element indicator
        elem_text = f"{STEMS_ELEMENT[sb.stem_index]} / {BRANCHES_ELEMENT[sb.branch_index]}"
        elements.append(
            f'<text x="{x + pillar_width // 2}" y="{y + pillar_height - 40}" '
            f'text-anchor="middle" font-size="11" fill="#555" font-family="system-ui">'
            f'{elem_text}</text>'
        )

        return elements

    svg_parts: list[str] = []

    # Background
    svg_parts.append(
        f'<svg xmlns="{ns}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )

    # Title
    svg_parts.append(
        f'<text x="{width // 2}" y="45" text-anchor="middle" font-size="22" '
        f'font-weight="bold" fill="#2c3e50" font-family="system-ui">'
        f'Ba Zi — {result.name}</text>'
    )

    # Subtitle with birth date and day master
    dm = f"{result.day_master_yin_yang} {result.day_master_element}"
    svg_parts.append(
        f'<text x="{width // 2}" y="70" text-anchor="middle" font-size="14" '
        f'fill="#7f8c8d" font-family="system-ui">'
        f'Born {result.birth_date.isoformat()} · Day Master: {dm}</text>'
    )

    # Draw four pillars
    pillars = [result.year_pillar, result.month_pillar, result.day_pillar, result.hour_pillar]
    for i, pillar in enumerate(pillars):
        x = start_x + i * (pillar_width + 20)
        svg_parts.extend(_pillar_svg(pillar, x, top_y))

    # Element balance summary
    elem_counts = result.element_counts
    total_elements = sum(elem_counts.values()) or 1

    svg_parts.append(
        f'<text x="{width // 2}" y="620" text-anchor="middle" font-size="16" '
        f'font-weight="bold" fill="#34495e" font-family="system-ui">'
        f'Element Distribution</text>'
    )

    elem_colors_svg = {
        "Wood": "#27ae60", "Fire": "#e74c3c", "Earth": "#d35400",
        "Metal": "#95a5a6", "Water": "#2980b9",
    }

    y_pos = 650
    for elem in ["Wood", "Fire", "Earth", "Metal", "Water"]:
        count = elem_counts.get(elem, 0)
        pct = round(count / total_elements * 100) if total_elements > 0 else 0
        color = elem_colors_svg.get(elem, "#999")

        svg_parts.append(
            f'<circle cx="{width // 2 - 80}" cy="{y_pos}" r="6" fill="{color}"/>'
        )
        svg_parts.append(
            f'<text x="{width // 2 - 65}" y="{y_pos + 4}" font-size="13" '
            f'fill="#333" font-family="system-ui">{elem}: {pct}%</text>'
        )

        # Bar
        bar_width = int(pct * 2)
        svg_parts.append(
            f'<rect x="{width // 2 + 80}" y="{y_pos - 6}" width="{bar_width}" height="12" '
            f'fill="{color}" opacity="0.7" rx="3"/>'
        )

        y_pos += 25

    # Luck pillars summary
    if result.luck_pillars:
        svg_parts.append(
            f'<text x="{width // 2}" y="800" text-anchor="middle" font-size="14" '
            f'font-weight="bold" fill="#34495e" font-family="system-ui">'
            f'Luck Pillars (大运)</text>'
        )

        for i, lp in enumerate(result.luck_pillars[:4]):  # Show first 4
            x_pos = start_x + i * 160
            svg_parts.append(
                f'<text x="{x_pos}" y="825" text-anchor="middle" font-size="11" '
                f'fill="#555" font-family="system-ui">'
                f'Ages {lp.start_age}-{lp.start_age + 9}: {lp.stem_branch.stem_index}/{lp.stem_branch.branch_index}</text>'
            )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
