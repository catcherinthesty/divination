"""SVG numerology wheel renderer.

Produces a deterministic circular chart showing all five core numbers
for both Pythagorean and Chaldean systems.

Same record always produces byte-identical SVG (constitution Principle I).
"""

from __future__ import annotations

import math
from typing import Any

from .data_types import CoreNumbers, System


def render_wheel(
    name: str,
    pyth: CoreNumbers,
    chald: CoreNumbers,
    width: int = 600,
    height: int = 750,
) -> str:
    """Render a numerology wheel as an SVG string.

    Layout:
      - Top arc: Pythagorean numbers (Life Path, Expression, Soul Urge, Personality, Birthday)
      - Bottom arc: Chaldean numbers in same positions
      - Center: name and birth date
      - Connecting lines between corresponding numbers across systems
    """
    ns = "http://www.w3.org/2000/svg"
    cx = width // 2
    cy_top = 140  # center of top arc
    cy_bot = 560  # center of bottom arc
    r = 180       # radius of arcs

    # Angle positions for the 5 numbers (left to right across the arc)
    angles = [math.radians(a) for a in range(-72, 73, 36)]  # -72°, -36°, 0°, 36°, 72°

    labels = ["Life Path", "Expression", "Soul Urge", "Personality", "Birthday"]
    short_labels = ["LP", "EXP", "SU", "PER", "BD"]

    def arc_points(cy: int, core: CoreNumbers) -> list[tuple[float, float]]:
        """Return (x, y) for each of the 5 number positions on the arc."""
        pts = []
        for i, angle in enumerate(angles):
            x = cx + r * math.sin(angle)
            y = cy - r * math.cos(angle)
            pts.append((x, y))
        return pts

    def _draw_wheel(cy: int, core: CoreNumbers, system_name: str, color: str) -> list[str]:
        """Draw one arc wheel (top or bottom)."""
        elements: list[str] = []
        pts = arc_points(cy, core)

        # Arc path
        arc_d = "M {:.1f} {:.1f}".format(pts[0][0], pts[0][1])
        for px, py in pts[1:]:
            arc_d += f" L {px:.1f} {py:.1f}"
        elements.append(
            f'<path d="{arc_d}" fill="none" stroke="{color}" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )

        # Nodes and numbers
        for i, (px, py) in enumerate(pts):
            num = core.life_path if short_labels[i] == "LP" else \
                  core.expression if short_labels[i] == "EXP" else \
                  core.soul_urge if short_labels[i] == "SU" else \
                  core.personality if short_labels[i] == "PER" else core.birthday

            # Outer circle
            elements.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="28" '
                f'fill="#fff" stroke="{color}" stroke-width="2"/>'
            )
            # Number inside
            elements.append(
                f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" '
                f'dominant-baseline="central" font-size="22" font-weight="bold" '
                f'fill="{color}" font-family="system-ui, sans-serif">{num}</text>'
            )
            # Label below node
            label_y = py - 38
            elements.append(
                f'<text x="{px:.1f}" y="{label_y:.1f}" text-anchor="middle" '
                f'font-size="9" fill="#666" font-family="system-ui, sans-serif">'
                f'{short_labels[i]}</text>'
            )

        # System label at bottom of arc
        label_x = cx
        label_y = cy + r + 20
        elements.append(
            f'<text x="{label_x}" y="{label_y:.1f}" text-anchor="middle" '
            f'font-size="13" font-weight="bold" fill="{color}" '
            f'font-family="system-ui, sans-serif">{system_name}</text>'
        )

        return elements

    svg_parts: list[str] = []

    # Background
    svg_parts.append(
        f'<svg xmlns="{ns}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )

    # Title
    svg_parts.append(
        f'<text x="{cx}" y="35" text-anchor="middle" font-size="18" '
        f'font-weight="bold" fill="#2c3e50" font-family="system-ui, sans-serif">'
        f'Numerology Wheel — {name}</text>'
    )

    # Date
    svg_parts.append(
        f'<text x="{cx}" y="58" text-anchor="middle" font-size="12" '
        f'fill="#7f8c8d" font-family="system-ui, sans-serif">'
        f'{name} · {chald.life_path_breakdown.split("→")[0].strip()}</text>'
    )

    # Pythagorean wheel (top) — blue
    svg_parts.extend(_draw_wheel(cy_top, pyth, "Pythagorean", "#2980b9"))

    # Chaldean wheel (bottom) — purple
    svg_parts.extend(_draw_wheel(cy_bot, chald, "Chaldean", "#8e44ad"))

    # Connecting lines between corresponding nodes
    pyth_pts = arc_points(cy_top, pyth)
    chald_pts = arc_points(cy_bot, chald)
    for (px, py), (bx, by) in zip(pyth_pts, chald_pts):
        svg_parts.append(
            f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="#bdc3c7" stroke-width="0.8" stroke-dasharray="4,4"/>'
        )

    # Legend at bottom
    legend_y = height - 30
    svg_parts.append(
        f'<text x="{cx}" y="{legend_y:.1f}" text-anchor="middle" font-size="10" '
        f'fill="#95a5a6" font-family="system-ui, sans-serif">'
        f'Dashed lines connect corresponding numbers across systems for comparison</text>'
    )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)
