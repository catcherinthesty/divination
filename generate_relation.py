#!/usr/bin/env python3
"""Generate bakl_arh_relation.html — family synastry chart for Bristol + Aria."""

import json
from pathlib import Path

PROJECT = Path("/home/jheinsen/Projects/astrology")
SYN_FILE = Path("/home/jheinsen/.qwen/tmp/c327bffecf7fcf7080977cf99f9a3601ea181853f0f9831a8e4211837a6a1cf8/tool-results/22LdCAdxKmUboc0rCHQ9pNrSE3Iw3o6v.txt")

HOUSE_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9,
    "tenth": 10, "eleventh": 11, "twelfth": 12,
}

def load():
    with open(SYN_FILE) as f:
        return json.load(f)["chart_data"]

def short_name(name):
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}. {parts[-1]}"
    return name

def build_aspect_rows(aspects, p1_label, p2_label):
    """Build rows for inter-chart aspects (between the two people)."""
    rows = []
    major_types = ("conjunction", "square", "trine", "opposition")
    for a in sorted(aspects, key=lambda x: x["orbit"]):
        atype = a.get("aspect", "")
        orb = a.get("orbit", 999)
        if atype not in major_types or orb > 8:
            continue
        p1 = a["p1_name"]
        p2 = a["p2_name"]
        movement = a.get("aspect_movement", "")
        arrow = "→" if movement == "Applying" else ("←" if movement == "Separating" else "•")
        cls = "applying" if movement == "Applying" else ("separating" if movement == "Separating" else "static")
        rows.append(
            f"<tr><td>{p1} ({p1_label})</td><td class='highlight'>{atype}</td><td>{p2} ({p2_label})</td>"
            f"<td>{orb:.1f}°</td><td class='{cls}'>{arrow} {movement}</td></tr>"
        )
    return rows

def build_house_overlay(first_sub, second_sub):
    """Show which houses each person's planets fall into for the other."""
    # Map planet -> house for each subject
    def planet_houses(sub):
        ph = {}
        for key, val in sub.items():
            if isinstance(val, dict) and "name" in val and val.get("point_type") == "AstrologicalPoint":
                ph[val["name"]] = val.get("house", "")
        return ph

    first_ph = planet_houses(first_sub)
    second_ph = planet_houses(second_sub)

    # Get house names list
    hnames = sub.get("houses_names_list", []) if (sub := first_sub) else []

    rows = []
    for pname, house in sorted(first_ph.items(), key=lambda x: x[0]):
        if house:
            hnum = HOUSE_ORDINALS.get(house.split("_")[0].lower(), "?")
            rows.append(f"<tr><td>{pname}</td><td>falls in {second_sub['name']}'s {house.replace('_', ' ').title()} (H{hnum})</td></tr>")

    return "\n".join(rows)


def main():
    cd = load()
    first = cd["first_subject"]
    second = cd["second_subject"]
    aspects = cd.get("aspects", [])
    score = cd.get("relationship_score", {})
    elem_dist = cd.get("element_distribution", {})
    qual_dist = cd.get("quality_distribution", {})

    p1_name = first["name"]
    p2_name = second["name"]
    p1_short = short_name(p1_name)
    p2_short = short_name(p2_name)
    p1_born = first.get("iso_formatted_local_datetime", "")
    p2_born = second.get("iso_formatted_local_datetime", "")
    p1_city = first.get("city", "")
    p2_city = second.get("city", "")

    # Major aspects between the two people
    major_rows = build_aspect_rows(aspects, p1_short, p2_short)

    # Join rows for HTML template
    major_html = chr(10).join(major_rows) if isinstance(major_rows, list) else major_rows

    # Score
    score_val = score.get("score_value", "?")
    score_desc = score.get("score_description", "?")
    is_destiny = score.get("is_destiny_sign", False)
    score_aspects = score.get("aspects", [])

    # Elements
    total_e = sum(elem_dist.values()) or 1
    fire_pct = elem_dist.get("fire", 0) / total_e * 100
    earth_pct = elem_dist.get("earth", 0) / total_e * 100
    air_pct = elem_dist.get("air", 0) / total_e * 100
    water_pct = elem_dist.get("water", 0) / total_e * 100

    # Qualities
    cardinal = qual_dist.get("cardinal", 0)
    fixed = qual_dist.get("fixed", 0)
    mutable = qual_dist.get("mutable", 0)

    svg_filename = "bakl_arh_relation.svg"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Family Relationship — {p1_name} &amp; {p2_name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0a1a;
    color: #ddd;
    padding: 20px;
    line-height: 1.6;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  h1 {{
    text-align: center;
    font-size: 1.8em;
    margin-bottom: 5px;
    background: linear-gradient(90deg, #f0c040, #e06040, #40c0e0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .subtitle {{ text-align: center; color: #777; margin-bottom: 20px; font-size: 0.9em; }}

  /* Score card */
  .score-card {{
    background: linear-gradient(135deg, rgba(240,192,64,0.1), rgba(64,192,224,0.1));
    border: 2px solid #f0c040;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
  }}
  .score-card .score-value {{ font-size: 3em; color: #f0c040; font-weight: 700; }}
  .score-card .score-desc {{ font-size: 1.2em; color: #40c0e0; margin-top: 4px; }}
  .score-card .destiny {{ color: #e06040; font-weight: 600; margin-top: 8px; }}

  /* People cards */
  .people-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  @media (max-width: 900px) {{ .people-grid {{ grid-template-columns: 1fr; }} }}
  .person-card {{
    background: #141428; border: 1px solid #2a2a4a; border-radius: 10px; padding: 16px;
  }}
  .person-card h3 {{ color: #f0c040; margin-bottom: 8px; }}
  .person-card p {{ font-size: 0.9em; color: #aaa; margin-bottom: 4px; }}

  /* Charts */
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  @media (max-width: 1000px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
  .chart-wrap {{
    background: #fff; border-radius: 12px; padding: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }}
  .chart-wrap img {{ width: 100%; height: auto; }}
  .chart-label {{ text-align: center; color: #888; font-size: 0.85em; margin-top: 8px; }}

  /* Tables */
  .panel {{
    background: #141428; border: 1px solid #2a2a4a; border-radius: 10px; padding: 16px; margin-bottom: 16px;
  }}
  .panel h2 {{ color: #f0c040; font-size: 1.05em; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #2a2a4a; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
  th {{ color: #40c0e0; text-align: left; padding: 6px 8px; font-weight: 600; border-bottom: 1px solid #2a2a4a; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid rgba(42,42,74,0.5); }}
  .highlight {{ color: #f0c040; font-weight: 600; }}
  .applying {{ color: #40c0e0; }}
  .separating {{ color: #e0a040; }}
  .static {{ color: #888; }}

  /* Elements */
  .elem-bar {{ display: flex; height: 28px; border-radius: 6px; overflow: hidden; margin: 8px 0; }}
  .ef {{ background: #e06040; }}
  .ee {{ background: #40c080; }}
  .ea {{ background: #f0c040; }}
  .ew {{ background: #6060e0; }}
  .elem-labels {{ display: flex; justify-content: space-around; font-size: 0.8em; }}

  /* Key aspects */
  .key-aspects {{ margin-bottom: 20px; }}
  .key-aspect-item {{
    padding: 10px; margin-bottom: 8px; background: rgba(42,42,74,0.3); border-radius: 6px;
    border-left: 3px solid #f0c040; font-size: 0.92em;
  }}

  /* Nav */
  nav {{ margin-bottom: 20px; }}
  nav a {{ color: #40c0e0; text-decoration: none; font-size: 0.85em; margin-right: 16px; }}
  nav a:hover {{ color: #f0c040; text-decoration: underline; }}
</style>
</head>
<body>
<div class="container">

<nav>
  <a href="bakl_chart.html">← Bristol's Chart</a>
  <a href="arh_chart.html">→ Aria's Chart</a>
</nav>

<h1>👨‍👩‍👧 Family Relationship — {p1_name} &amp; {p2_name}</h1>
<p class="subtitle">Synastry chart showing how the two natal charts interact • Non-romantic family bond</p>

<!-- Score -->
<div class="score-card">
  <div style="font-size:0.85em;color:#888;margin-bottom:4px;">Relationship Score</div>
  <div class="score-value">{score_val}<span style="font-size:0.4em;color:#888;">/20</span></div>
  <div class="score-desc">{score_desc}</div>
  {f'<div class="destiny">⭐ Destiny Sign Connection</div>' if is_destiny else ''}
  <div style="margin-top:12px;font-size:0.85em;color:#aaa;">Key score drivers:</div>
  <ul style="list-style:none;margin-top:6px;padding:0;">
    {"".join(f'<li style="padding:3px 0;">• {a["p1_name"]} {a["aspect"]} {a["p2_name"]} (orb {a["orbit"]:.1f}°)</li>' for a in score_aspects[:5])}
  </ul>
</div>

<!-- People -->
<div class="people-grid">
  <div class="person-card">
    <h3>{p1_short}</h3>
    <p>📅 Born: {p1_born}</p>
    <p>📍 {p1_city}, US</p>
    <p>☉ Sun in {first["sun"]["sign"]} · ☽ Moon in {first["moon"]["sign"]}</p>
  </div>
  <div class="person-card">
    <h3>{p2_short}</h3>
    <p>📅 Born: {p2_born}</p>
    <p>📍 {p2_city}, US</p>
    <p>☉ Sun in {second["sun"]["sign"]} · ☽ Moon in {second["moon"]["sign"]}</p>
  </div>
</div>

<!-- SVG Charts -->
<div class="charts-grid">
  <div class="chart-wrap">
    <img src="{svg_filename}" alt="Synastry Chart">
    <div class="chart-label">Dual-wheel synastry chart — inner wheel: {p1_short}, outer wheel: {p2_short}</div>
  </div>
</div>

<!-- Major Aspects -->
<div class="panel">
  <h2>🔗 Major Inter-Chart Aspects (orb ≤ 8°)</h2>
  <table>
    <thead><tr><th>{p1_short}</th><th>Aspect</th><th>{p2_short}</th><th>Orb</th><th>Movement</th></tr></thead>
    <tbody>{major_html if major_html else '<tr><td colspan="5" style="color:#777">No major aspects within 8° orb</td></tr>'}</tbody>
  </table>
</div>

<!-- House Overlays -->
<div class="panel">
  <h2>🏠 Planet-in-House Overlays</h2>
  <p style="font-size:0.85em;color:#888;margin-bottom:12px;">Where each person's planets fall in the other's houses reveals how their energies interact in different life areas.</p>
  <table>
    <thead><tr><th>{p1_short}'s Planet</th><th>Falls in {p2_short}'s House</th></tr></thead>
    <tbody>
      {"".join(f'<tr><td>{pname}</td><td>{house.replace("_", " ").title()} (H{HOUSE_ORDINALS.get(house.split("_")[0].lower(), "?")})</td></tr>' for pname, house in sorted([(v["name"], v.get("house","")) for k,v in first.items() if isinstance(v,dict) and v.get("point_type")=="AstrologicalPoint" and v.get("house")], key=lambda x: x[0]))}
    </tbody>
  </table>
</div>

<!-- Elements & Qualities -->
<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
  <div class="panel">
    <h2>🔥 Combined Elements</h2>
    <div class="elem-bar">
      <div class="ef" style="width:{fire_pct:.0f}%"></div>
      <div class="ee" style="width:{earth_pct:.0f}%"></div>
      <div class="ea" style="width:{air_pct:.0f}%"></div>
      <div class="ew" style="width:{water_pct:.0f}%"></div>
    </div>
    <div class="elem-labels">
      <span style="color:#e06040">🔥 Fire: {elem_dist.get('fire',0):.1f}</span>
      <span style="color:#40c080">🌍 Earth: {elem_dist.get('earth',0):.1f}</span>
      <span style="color:#f0c040">💨 Air: {elem_dist.get('air',0):.1f}</span>
      <span style="color:#6060e0">💧 Water: {elem_dist.get('water',0):.1f}</span>
    </div>
  </div>
  <div class="panel">
    <h2>📐 Combined Qualities</h2>
    <table>
      <thead><tr><th>Quality</th><th>Weighted</th></tr></thead>
      <tbody>
        <tr><td>Cardinal</td><td>{qual_dist.get('cardinal',0):.1f}</td></tr>
        <tr><td>Fixed</td><td>{qual_dist.get('fixed',0):.1f}</td></tr>
        <tr><td>Mutable</td><td>{qual_dist.get('mutable',0):.1f}</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- Interpretation -->
<div class="panel">
  <h2>📖 Relationship Interpretation</h2>
  <div style="font-size:0.95em;line-height:1.8;">
"""

    # Build interpretation based on key aspects
    interp_lines = []

    # Sun-Moon relationship (core compatibility)
    for a in aspects:
        if (a["p1_name"] in ("Sun", "Moon") and a["p2_name"] in ("Sun", "Moon")
                and a["p1_owner"] != a["p2_owner"] and a["orbit"] <= 6):
            p1 = a["p1_name"]
            p2 = a["p2_name"]
            orb = a["orbit"]
            atype = a["aspect"]
            owner_p1 = "Bristol" if a["p1_owner"] == p1_name else "Aria"
            owner_p2 = "Bristol" if a["p2_owner"] == p1_name else "Aria"
            interp_lines.append(
                f"<p><strong>{p1} ({owner_p1}) {atype} {p2} ({owner_p2}), orb {orb:.1f}°</strong>: "
                f"This {'core' if atype in ('conjunction','trine') else 'dynamic'} aspect between identity and emotional nature "
                f"creates a natural understanding. In a family context, this suggests {"deep empathy and intuitive connection" if atype in ('conjunction','trine') else 'interesting differences that require patience but offer growth'}.</p>"
            )

    # Venus-Mars (affection and drive)
    for a in aspects:
        if (a["aspect"] in ("conjunction","trine","sextile")
                and ((a["p1_name"] in ("Venus","Mars") and a["p2_name"] in ("Venus","Mars"))
                     or (a["p1_name"] in ("Venus","Mars") and a["p2_owner"] != a["p1_owner"]))
                and a["orbit"] <= 6):
            interp_lines.append(
                f"<p><strong>{a['p1_name']} ↔ {a['p2_name']}</strong>: "
                f"Affection and energy flow smoothly between these two. In family life, this translates to natural warmth, "
                f"ease in expressing care, and a supportive dynamic where each person feels valued.</p>"
            )

    # Saturn aspects (structure and responsibility)
    saturn_aspects = [a for a in aspects if a["aspect"] in ("conjunction","trine","sextile")
                      and "Saturn" in (a["p1_name"], a["p2_name"]) and a["orbit"] <= 6]
    if saturn_aspects:
        interp_lines.append(
            "<p><strong>Saturn connections</strong>: Saturn aspects between family members create bonds of responsibility, "
            "loyalty, and mutual respect. This relationship has the potential for deep commitment and long-term stability. "
            "The older or more mature person may naturally take on a guiding role.</p>"
        )

    # Grand trine or multiple harmonics
    harmonic_count = len([a for a in aspects if a["aspect"] in ("conjunction","trine","sextile") and a["orbit"] <= 4])
    tense_count = len([a for a in aspects if a["aspect"] in ("square","opposition") and a["orbit"] <= 5])
    if harmonic_count >= 3:
        interp_lines.append(
            "<p><strong>Harmonic richness</strong>: With multiple easy aspects between the charts, this family bond "
            "flows naturally. There's an inherent comfort and ease in being together that makes communication and cooperation feel effortless.</p>"
        )
    if tense_count >= 2:
        interp_lines.append(
            "<p><strong>Growth through tension</strong>: The challenging aspects between these charts create productive friction. "
            "These are not bad aspects — they push both people to grow, adapt, and develop patience and understanding. "
            "Family relationships with this geometry often involve learning important life lessons together.</p>"
        )

    # House overlay interpretation
    interp_lines.append(
        "<p><strong>House overlays</strong>: Where one person's planets fall in the other's houses shows which areas of life "
        "are most activated. Planets in angular houses (1st, 4th, 7th, 10th) have the strongest impact, while planets in "
        "the 5th and 11th houses suggest shared joy and friendship as key bonding elements.</p>"
    )

    html += "\n".join(interp_lines) + """
  </div>
</div>

<a href="bakl_chart.html" style="display:inline-block;margin-top:20px;color:#777;font-size:0.85em;text-decoration:none;">← Back to Bristol's Chart</a>
<a href="arh_chart.html" style="display:inline-block;margin-top:20px;margin-left:16px;color:#777;font-size:0.85em;text-decoration:none;">Aria's Chart →</a>

</div>
</body>
</html>"""

    # Save SVG
    with open(PROJECT / svg_filename, "w") as f:
        f.write(chart_data_svg)
    print(f"Saved SVG: {PROJECT / svg_filename}")

    html_path = PROJECT / "bakl_arh_relation.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"Saved HTML: {html_path}")


# Need to get the SVG from the split chart response
synastry_svg_data = json.load(open("/home/jheinsen/.qwen/tmp/c327bffecf7fcf7080977cf99f9a3601ea181853f0f9831a8e4211837a6a1cf8/tool-results/ypRApO3EOZVMYIJYUIzhZai3UaM1RtDY.txt"))
chart_data_svg = synastry_svg_data.get("chart_wheel", "") or synastry_svg_data.get("chart", "")

if __name__ == "__main__":
    main()
