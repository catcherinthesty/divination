"""SVG gematria chart renderer.

Produces a deterministic three-panel chart showing all three systems
(Simple, Ordinal, Reverse) side by side with word-by-word breakdowns.

Same record always produces byte-identical SVG (constitution Principle I).
"""

from __future__ import annotations

from .data_types import GematriaResult, System


def render_gematria_wheel(result: GematriaResult, width: int = 900, height: int = 600) -> str:
    """Render a gematria chart as an SVG string.

    Layout:
      - Title row: name and reduced value
      - Three columns: Simple | Ordinal | Reverse
      - Each column shows total, reduced, initials value, and word breakdowns
      - Color-coded by system
    """
    ns = "http://www.w3.org/2000/svg"
    systems = [System.SIMPLE, System.ORDINAL, System.REVERSE]
    colors = {"#2980b9", "#27ae60", "#e74c3c"}  # blue, green, red
    labels = ["Simple", "Ordinal", "Reverse"]

    col_w = width // 3
    padding = 30
    title_y = 40
    header_y = 80

    svg_parts: list[str] = []
    svg_parts.append(f'<svg xmlns="{ns}" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')

    # Background
    svg_parts.append(f'<rect width="{width}" height="{height}" fill="#fafbfc" rx="8"/>')

    # Title
    name = result.name
    main_reduced = result.results.get(systems[0], result.results.get(list(result.results.keys())[0]))
    main_total = main_reduced.total if main_reduced else 0
    main_reduced_val = main_reduced.reduced if main_reduced else 0

    svg_parts.append(
        f'<text x="{width // 2}" y="{title_y}" text-anchor="middle" '
        f'font-size="20" font-weight="bold" fill="#2c3e50" '
        f'font-family="system-ui, sans-serif">Gematria — {name}</text>'
    )
    svg_parts.append(
        f'<text x="{width // 2}" y="{title_y + 22}" text-anchor="middle" '
        f'font-size="13" fill="#7f8c8d" '
        f'font-family="system-ui, sans-serif">Total: {main_total}  ·  Reduced: {main_reduced_val}</text>'
    )

    # Draw each column
    for idx, (sys_obj, color, label) in enumerate(zip(systems, colors, labels)):
        x0 = idx * col_w + padding
        col_data = result.results.get(sys_obj)

        if col_data is None:
            continue

        _draw_column(svg_parts, x0, header_y, col_w - 2 * padding, height, label, color, col_data)

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def _draw_column(
    parts: list[str],
    x0: int,
    y0: int,
    w: int,
    h: int,
    label: str,
    color: str,
    data,
) -> None:
    """Draw one column of the gematria chart."""
    # Column header
    parts.append(
        f'<text x="{x0 + w // 2}" y="{y0}" text-anchor="middle" '
        f'font-size="14" font-weight="bold" fill="{color}" '
        f'font-family="system-ui, sans-serif">{label}</text>'
    )

    # Divider line
    parts.append(
        f'<line x1="{x0}" y1="{y0 + 5}" x2="{x0 + w}" y2="{y0 + 5}" '
        f'stroke="{color}" stroke-width="1" opacity="0.3"/>'
    )

    current_y = y0 + 30

    # Total
    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="12" fill="#666" '
        f'font-family="system-ui, sans-serif">Total:</text>'
    )
    parts.append(
        f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
        f'font-size="18" font-weight="bold" fill="{color}" '
        f'font-family="system-ui, sans-serif">{data.total}</text>'
    )
    current_y += 28

    # Reduced
    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="12" fill="#666" '
        f'font-family="system-ui, sans-serif">Reduced:</text>'
    )
    reduced_color = "#f39c12" if data.reduced in (11, 22, 33) else color
    parts.append(
        f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
        f'font-size="20" font-weight="bold" fill="{reduced_color}" '
        f'font-family="system-ui, sans-serif">{data.reduced}</text>'
    )
    current_y += 28

    # Initials value
    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="12" fill="#666" '
        f'font-family="system-ui, sans-serif">Initials:</text>'
    )
    parts.append(
        f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
        f'font-size="14" font-weight="bold" fill="{color}" '
        f'font-family="system-ui, sans-serif">{data.initials_value}</text>'
    )
    current_y += 28

    # Separator
    parts.append(
        f'<line x1="{x0 + 10}" y1="{current_y}" x2="{x0 + w - 10}" y2="{current_y}" '
        f'stroke="#ddd" stroke-width="0.5"/>'
    )
    current_y += 18

    # Word breakdowns
    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="11" font-weight="bold" fill="#999" '
        f'font-family="system-ui, sans-serif">Words:</text>'
    )
    current_y += 16

    for word_data in data.words[:6]:  # max 6 words visible
        word_label = word_data.word[:15]  # truncate long words
        parts.append(
            f'<text x="{x0 + 10}" y="{current_y}" font-size="11" fill="#444" '
            f'font-family="system-ui, sans-serif">{word_label}:</text>'
        )
        parts.append(
            f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
            f'font-size="11" fill="#666" font-family="system-ui, sans-serif">'
            f'{word_data.total} → {word_data.reduced}</text>'
        )
        current_y += 15

    # Vowel / Consonant totals
    total_vowels = sum(w.vowel_total for w in data.words)
    total_consonants = sum(w.consonant_total for w in data.words)

    current_y += 8
    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="11" fill="#666" '
        f'font-family="system-ui, sans-serif">Vowels:</text>'
    )
    parts.append(
        f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
        f'font-size="12" fill="#8e44ad" font-weight="bold" '
        f'font-family="system-ui, sans-serif">{total_vowels}</text>'
    )
    current_y += 16

    parts.append(
        f'<text x="{x0 + 10}" y="{current_y}" font-size="11" fill="#666" '
        f'font-family="system-ui, sans-serif">Consonants:</text>'
    )
    parts.append(
        f'<text x="{x0 + w - 10}" y="{current_y}" text-anchor="end" '
        f'font-size="12" fill="#8e44ad" font-weight="bold" '
        f'font-family="system-ui, sans-serif">{total_consonants}</text>'
    )
