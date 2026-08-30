#!/usr/bin/env python3
"""
Generate natal chart SVG + HTML analysis for B.A.
Reads the MCP API response and produces chart files.
"""

import json
from pathlib import Path

PROJECT = Path("/home/jheinsen/Projects/astrology")
RESPONSE_FILE = Path("/home/jheinsen/.qwen/tmp/c327bffecf7fcf7080977cf99f9a3601ea181853f0f9831a8e4211837a6a1cf8/tool-results/X10YKNRbmr7BCnockQDBp2QNEu5kM1zd.txt")

HOUSE_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9,
    "tenth": 10, "eleventh": 11, "twelfth": 12,
}


def main():
    with open(RESPONSE_FILE) as f:
        data = json.load(f)

    chart_data = data["chart_data"]
    svg_content = data["chart"]

    # 1. Save the raw SVG
    svg_path = PROJECT / "natal_chart.svg"
    with open(svg_path, "w") as f:
        f.write(svg_content)
    print(f"Saved SVG: {svg_path}")

    # 2. Generate HTML analysis
    html_path = generate_html(chart_data, svg_path)
    print(f"Saved HTML: {html_path}")
    return html_path


def generate_html(chart_data, svg_path):
    """Create and save an HTML page with chart analysis."""
    sub = chart_data["subject"]
    name = sub.get("name", "B.A.")
    birth_dt = sub.get("iso_formatted_local_datetime", "")
    city = sub.get("city", "")
    nation = sub.get("nation", "")
    tz = sub.get("tz_str", "")
    house_system = sub.get("houses_system_name", "Placidus")
    zodiac = sub.get("zodiac_type", "Tropical")
    diurnal = "Diurnal" if sub.get("is_diurnal") else "Nocturnal"
    lunar = sub.get("lunar_phase", {})

    # Flatten subject dict for easy access
    planets = {}
    for key, val in sub.items():
        if isinstance(val, dict) and "name" in val and val.get("point_type") == "AstrologicalPoint":
            planets[val["name"]] = val

    # Planet table
    planet_order = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                    "Uranus", "Neptune", "Pluto", "Chiron", "Ascendant", "Descendant",
                    "Medium_Coeli", "Imum_Coeli", "True_North_Lunar_Node", "True_South_Lunar_Node",
                    "Mean_Lilith"]
    
    planet_rows = []
    for pname in planet_order:
        p = planets.get(pname)
        if not p:
            continue
        display_name = pname.replace("_", " ")
        # Shorten house name
        house = p.get("house", "")
        house_num = house.split("_")[0] if house else "?"
        retro = "R" if p.get("retrograde") else ""
        element = p.get("element", "")
        quality = p.get("quality", "")
        sign = p.get("sign", "")
        deg = p.get("position", 0)
        emoji = p.get("emoji", "")
        planet_rows.append(
            f"<tr><td>{emoji} {display_name}</td><td>{sign}{deg:.1f}°</td>"
            f"<td>{house_num}</td><td>{retro or '&nbsp;'}</td><td>{element} {quality}</td></tr>"
        )

    # House cusps
    house_keys = ["first_house", "second_house", "third_house", "fourth_house",
                  "fifth_house", "sixth_house", "seventh_house", "eighth_house",
                  "ninth_house", "tenth_house", "eleventh_house", "twelfth_house"]
    house_rows = []
    for hkey in house_keys:
        h = sub.get(hkey)
        if h:
            sign = h.get("sign", "")
            emoji = h.get("emoji", "")
            deg = h.get("position", 0)
            num = HOUSE_ORDINALS.get(hkey.split("_")[0], "?")
            house_rows.append(f"<tr><td>{emoji} H{num}</td><td>{sign}{deg:.1f}°</td></tr>")

    # Aspects (major only, tight orb)
    aspect_rows = []
    for a in chart_data.get("aspects", []):
        atype = a.get("aspect", "")
        orb = a.get("orbit", 999)
        p1 = a.get("p1_name", "")
        p2 = a.get("p2_name", "")
        movement = a.get("aspect_movement", "")
        if atype in ("conjunction", "square", "trine", "opposition") and orb <= 8:
            arrow = "→" if movement == "Applying" else "←"
            cls = "applying" if movement == "Applying" else "separating"
            aspect_rows.append(
                f"<tr><td>{p1}</td><td class='highlight'>{atype}</td><td>{p2}</td>"
                f"<td>{orb:.1f}°</td><td class='{cls}'>{arrow} {movement}</td></tr>"
            )

    # Element counts
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    for p in planets.values():
        e = p.get("element", "")
        if e in elements:
            elements[e] += 1
    total_e = sum(elements.values()) or 1

    # Quality counts
    qualities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    for p in planets.values():
        q = p.get("quality", "")
        if q in qualities:
            qualities[q] += 1

    # Interpretations
    interp = build_interpretation(planets, chart_data)

    # Key values for cards
    sun_emoji = planets.get("Sun", {}).get("emoji", "")
    sun_sign = planets.get("Sun", {}).get("sign", "")
    moon_emoji = planets.get("Moon", {}).get("emoji", "")
    moon_sign = planets.get("Moon", {}).get("sign", "")
    asc_emoji = planets.get("Ascendant", {}).get("emoji", "")
    asc_sign = planets.get("Ascendant", {}).get("sign", "")
    merc_emoji = planets.get("Mercury", {}).get("emoji", "")
    merc_sign = planets.get("Mercury", {}).get("sign", "")
    venus_emoji = planets.get("Venus", {}).get("emoji", "")
    venus_sign = planets.get("Venus", {}).get("sign", "")
    mars_emoji = planets.get("Mars", {}).get("emoji", "")
    mars_sign = planets.get("Mars", {}).get("sign", "")
    phase_emoji = lunar.get('moon_emoji', '')
    phase_name = lunar.get('moon_phase_name', '')
    chart_ruler = get_chart_ruler(planets)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Natal Chart — {name}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #0a0a1a;
    color: #ddd;
    padding: 20px;
    line-height: 1.6;
  }}
  .container {{ max-width: 1500px; margin: 0 auto; }}
  h1 {{
    text-align: center;
    font-size: 2em;
    margin-bottom: 5px;
    background: linear-gradient(90deg, #f0c040, #e06040, #40c0e0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  .subtitle {{ text-align: center; color: #777; margin-bottom: 20px; font-size: 0.9em; }}
  .key-cards {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin-bottom: 20px;
  }}
  .card {{
    background: #141428;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
  }}
  .card .label {{ font-size: 0.7em; color: #888; text-transform: uppercase; letter-spacing: 1px; }}
  .card .value {{ font-size: 1.3em; color: #f0c040; font-weight: 700; margin-top: 4px; }}
  .svg-wrap {{
    background: #fff;
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
  }}
  .svg-wrap img {{ width: 100%; height: auto; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }}
  @media (max-width: 1000px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .panel {{
    background: #141428;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 16px;
  }}
  .panel h2 {{
    color: #f0c040;
    font-size: 1.05em;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #2a2a4a;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.85em; }}
  th {{ color: #40c0e0; text-align: left; padding: 6px 8px; font-weight: 600; border-bottom: 1px solid #2a2a4a; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid rgba(42,42,74,0.5); }}
  .highlight {{ color: #f0c040; font-weight: 600; }}
  .applying {{ color: #40c0e0; }}
  .separating {{ color: #e0a040; }}
  .full-w {{ grid-column: 1 / -1; }}
  .elem-bar {{ display: flex; height: 28px; border-radius: 6px; overflow: hidden; margin: 8px 0; }}
  .ef {{ background: #e06040; }}
  .ee {{ background: #40c080; }}
  .ea {{ background: #f0c040; }}
  .ew {{ background: #6060e0; }}
  .elem-labels {{ display: flex; justify-content: space-around; font-size: 0.8em; }}
  .interp p {{
    margin-bottom: 10px;
    padding: 10px;
    background: rgba(42,42,74,0.3);
    border-radius: 6px;
    border-left: 3px solid #f0c040;
    font-size: 0.92em;
  }}
  .interp strong {{ color: #f0c040; }}
</style>
</head>
<body>
<div class="container">
  <h1>🌟 Natal Chart — {name}</h1>
  <p class="subtitle">
    Born {birth_dt} ({tz}) · {city}, {nation} · {house_system} Houses · {zodiac} Zodiac · {diurnal}
    {f" · {phase_emoji} {phase_name}" if phase_name else ""}
  </p>

  <div class="key-cards">
    <div class="card"><div class="label">☉ Sun</div><div class="value">{sun_emoji} {sun_sign}</div></div>
    <div class="card"><div class="label">☽ Moon</div><div class="value">{moon_emoji} {moon_sign}</div></div>
    <div class="card"><div class="label">⬆ Asc</div><div class="value">{asc_emoji} {asc_sign}</div></div>
    <div class="card"><div class="label">☿ Merc</div><div class="value">{merc_emoji} {merc_sign}</div></div>
    <div class="card"><div class="label">♀ Venus</div><div class="value">{venus_emoji} {venus_sign}</div></div>
    <div class="card"><div class="label">♂ Mars</div><div class="value">{mars_emoji} {mars_sign}</div></div>
    <div class="card"><div class="label">🌙 Phase</div><div class="value">{phase_emoji} {phase_name}</div></div>
    <div class="card"><div class="label">Chart Ruler</div><div class="value">{chart_ruler}</div></div>
  </div>

  <div class="svg-wrap">
    <img src="{svg_path.name}" alt="Natal Chart">
  </div>

  <div class="grid">
    <div class="panel">
      <h2>🪐 Planets</h2>
      <table>
        <thead><tr><th>Planet</th><th>Sign</th><th>House</th><th>R</th><th>Quality</th></tr></thead>
        <tbody>{chr(10).join(planet_rows)}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>🏠 House Cusps</h2>
      <table>
        <thead><tr><th>House</th><th>Cusp</th></tr></thead>
        <tbody>{chr(10).join(house_rows)}</tbody>
      </table>
    </div>
    <div class="panel full-w">
      <h2>🔗 Major Aspects (orb ≤ 8°)</h2>
      <table>
        <thead><tr><th>Planet 1</th><th>Aspect</th><th>Planet 2</th><th>Orb</th><th>Movement</th></tr></thead>
        <tbody>{chr(10).join(aspect_rows) if aspect_rows else '<tr><td colspan="5" style="color:#777">No major aspects within 8° orb</td></tr>'}</tbody>
      </table>
    </div>
    <div class="panel">
      <h2>🔥 Elements</h2>
      <div class="elem-bar">
        <div class="ef" style="width:{elements['Fire']/total_e*100:.0f}%"></div>
        <div class="ee" style="width:{elements['Earth']/total_e*100:.0f}%"></div>
        <div class="ea" style="width:{elements['Air']/total_e*100:.0f}%"></div>
        <div class="ew" style="width:{elements['Water']/total_e*100:.0f}%"></div>
      </div>
      <div class="elem-labels">
        <span style="color:#e06040">🔥 Fire: {elements['Fire']}</span>
        <span style="color:#40c080">🌍 Earth: {elements['Earth']}</span>
        <span style="color:#f0c040">💨 Air: {elements['Air']}</span>
        <span style="color:#6060e0">💧 Water: {elements['Water']}</span>
      </div>
    </div>
    <div class="panel">
      <h2>📐 Qualities</h2>
      <table>
        <thead><tr><th>Quality</th><th>Count</th></tr></thead>
        <tbody>
          {chr(10).join(f'<tr><td>{q}</td><td>{c}</td></tr>' for q,c in qualities.items())}
        </tbody>
      </table>
    </div>
    <div class="panel full-w">
      <h2>📖 Interpretation</h2>
      <div class="interp">{interp}</div>
    </div>
  </div>
</div>
</body>
</html>"""

    # Write the HTML file
    html_path = PROJECT / "natal_chart.html"
    with open(html_path, "w") as f:
        f.write(html)

    return html_path


def get_chart_ruler(planets):
    """Get the chart ruler based on Ascendant sign."""
    asc = planets.get("Ascendant", {})
    sign = asc.get("sign", "")
    rulers = {
        "Ari": "Mars ♂", "Tau": "Venus ♀", "Gem": "Mercury ☿",
        "Can": "Moon ☽", "Leo": "Sun ☉", "Vir": "Mercury ☿",
        "Lib": "Venus ♀", "Sco": "Mars ♂/Pluto ♇",
        "Sag": "Jupiter ♃", "Cap": "Saturn ♄",
        "Aqu": "Saturn ♄/Uranus ⛢", "Pis": "Jupiter ♃/Neptune ♆",
    }
    return rulers.get(sign, sign)


def build_interpretation(planets, chart_data):
    """Build interpretation HTML."""
    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})
    asc = planets.get("Ascendant", {})
    merc = planets.get("Mercury", {})
    venus = planets.get("Venus", {})
    mars = planets.get("Mars", {})
    
    sun_h = str(HOUSE_ORDINALS.get(sun.get("house", "").split("_")[0].lower(), "?")) if sun.get("house") else "?"
    moon_h = str(HOUSE_ORDINALS.get(moon.get("house", "").split("_")[0].lower(), "?")) if moon.get("house") else "?"
    
    interpretations = []
    
    # Sun
    sun_sigs = {
        "Ari": "pioneering spirit and bold self-expression",
        "Tau": "steady determination and appreciation for beauty",
        "Gem": "curiosity, communication, and mental versatility",
        "Can": "nurturing nature and emotional depth",
        "Leo": "creative expression, confidence, and generosity",
        "Vir": "analytical thinking, practicality, and service",
        "Lib": "diplomacy, fairness, and pursuit of harmony",
        "Sco": "intensity, transformation, and profound insight",
        "Sag": "adventure, philosophy, and optimistic exploration",
        "Cap": "ambition, discipline, and long-term vision",
        "Aqu": "independence, innovation, and humanitarian ideals",
        "Pis": "compassion, imagination, and spiritual sensitivity",
    }
    interpretations.append(
        f'<p><strong>Sun in {sun.get("sign", "")} ({sun_h}th House)</strong>: '
        f'This chart ruled by a Sun in {sun.get("sign", "")}, bringing {sun_sigs.get(sun.get("sign", ""), "a unique blend of energies")}. '
        f'In the {sun_h}th house, self-expression finds its outlet through {get_house_meaning(sun_h, chart_data)}.</p>'
    )
    
    # Moon
    moon_sigs = {
        "Ari": "direct and passionate emotional responses",
        "Tau": "need for stability, comfort, and sensual pleasure",
        "Gem": "emotional processing through communication and learning",
        "Can": "deep nurturing instincts and emotional sensitivity",
        "Leo": "dramatic, warm, and creative emotional expression",
        "Vir": "analytical approach to emotions and practical care",
        "Lib": "harmony-seeking emotions and partnership orientation",
        "Sco": "intense, transformative emotional depth",
        "Sag": "freedom-loving, optimistic emotional nature",
        "Cap": "reserved, responsible, and protective feelings",
        "Aqu": "detached, intellectual, and friendship-oriented emotions",
        "Pis": "empathetic, dreamy, and spiritually-connected feelings",
    }
    interpretations.append(
        f'<p><strong>Moon in {moon.get("sign", "")} ({moon_h}th House)</strong>: '
        f'Emotionally, this person experiences {moon_sigs.get(moon.get("sign", ""), "complex feelings")}. '
        f'Moon in the {moon_h}th house suggests emotional security through {get_house_meaning(moon_h, chart_data)}.</p>'
    )
    
    # Ascendant
    asc_sigs = {
        "Ari": "dynamic, courageous, and direct",
        "Tau": "calm, grounded, and aesthetically aware",
        "Gem": "curious, adaptable, and communicative",
        "Can": "nurturing, sensitive, and protective",
        "Leo": "charismatic, confident, and creative",
        "Vir": "analytical, refined, and service-minded",
        "Lib": "diplomatic, charming, and fair-minded",
        "Sco": "intense, magnetic, and transformative",
        "Sag": "adventurous, optimistic, and philosophical",
        "Cap": "disciplined, serious, and ambitious",
        "Aqu": "unique, independent, and forward-thinking",
        "Pis": "dreamy, compassionate, and spiritually attuned",
    }
    interpretations.append(
        f'<p><strong>Ascendant {asc.get("sign", "")}</strong>: '
        f'The lens through which this person approaches life is {asc_sigs.get(asc.get("sign", ""), "")}. '
        f'With {asc.get("sign", "")} rising, the first impression given to others is one of {get_asc_first_impression(asc.get("sign", ""))}.</p>'
    )
    
    # Mercury
    if merc:
        merc_sigs = {
            "Ari": "quick, direct, and assertive thinking",
            "Tau": "practical, methodical, and grounded thought",
            "Gem": "versatile, curious, and communicative mind",
            "Can": "intuitive, reflective, and memory-oriented thinking",
            "Leo": "creative, dramatic, and confident expression",
            "Vir": "analytical, precise, and detail-focused mind",
            "Lib": "diplomatic, balanced, and fair-minded reasoning",
            "Sco": "profound, investigative, and penetrating thought",
            "Sag": "philosophical, broad-minded, and optimistic thinking",
            "Cap": "structured, strategic, and practical reasoning",
            "Aqu": "innovative, unconventional, and intellectual thought",
            "Pis": "imaginative, intuitive, and poetic thinking",
        }
        interpretations.append(
            f'<p><strong>Mercury in {merc.get("sign", "")}</strong>: '
            f'Communication and thought process is {merc_sigs.get(merc.get("sign", ""), "")}.</p>'
        )
    
    # Venus
    if venus:
        venus_sigs = {
            "Ari": "passionate, direct, and enthusiastic in love",
            "Tau": "sensual, devoted, and appreciative of beauty",
            "Gem": "playful, intellectually stimulating relationships",
            "Can": "nurturing, emotionally connected partnerships",
            "Leo": "generous, dramatic, and warm-hearted love",
            "Vir": "thoughtful, service-oriented, and refined affection",
            "Lib": "romantic, harmonious, and partnership-loving",
            "Sco": "intense, transformative, and deeply passionate",
            "Sag": "adventurous, freedom-loving, and optimistic in love",
            "Cap": "loyal, committed, and traditional approach to relationships",
            "Aqu": "friendly, unconventional, and intellectually connected",
            "Pis": "dreamy, compassionate, and selflessly loving",
        }
        interpretations.append(
            f'<p><strong>Venus in {venus.get("sign", "")}</strong>: '
            f'In love and beauty, this person expresses {venus_sigs.get(venus.get("sign", ""), "")}.</p>'
        )
    
    # Mars
    if mars:
        mars_sigs = {
            "Ari": "bold, courageous, and immediate action",
            "Tau": "steady, persistent, and determined drive",
            "Gem": "versatile, quick, and mentally-driven energy",
            "Can": "protective, intuitive, and emotionally-motivated action",
            "Leo": "creative, bold, and confidently-driven energy",
            "Vir": "precise, methodical, and service-oriented effort",
            "Lib": "diplomatic, fair, and harmony-seeking action",
            "Sco": "intense, powerful, and transformative drive",
            "Sag": "adventurous, optimistic, and freedom-driven energy",
            "Cap": "disciplined, strategic, and goal-oriented action",
            "Aqu": "innovative, independent, and unconventional drive",
            "Pis": "compassionate, spiritual, and intuitive energy",
        }
        interpretations.append(
            f'<p><strong>Mars in {mars.get("sign", "")}</strong>: '
            f'Drive, energy, and action style is {mars_sigs.get(mars.get("sign", ""), "")}.</p>'
        )
    
    # Key aspects
    key_aspects = [a for a in chart_data.get("aspects", [])
                   if a.get("aspect") in ("conjunction", "square", "trine", "opposition")
                   and a.get("orbit", 999) <= 6]
    if key_aspects:
        aspect_list = []
        for a in key_aspects[:6]:
            aspect_list.append(f"{a['p1_name']} {a['aspect']} {a['p2_name']} (orb {a['orbit']:.1f}°)")
        interpretations.append(
            f'<p><strong>Major Aspects</strong>: Notable aspects include {", ".join(aspect_list)}.</p>'
        )
    
    return chr(10).join(interpretations)


def get_house_meaning(house_num, chart_data):
    """Get meaning of a house number."""
    meanings = {
        "1": "personal identity, self-expression, and initiating new endeavors",
        "2": "building resources, values, and sense of self-worth",
        "3": "communication, learning, short journeys, and local community",
        "4": "home, family roots, inner foundation, and private life",
        "5": "creativity, romance, joy, children, and self-expression through play",
        "6": "daily habits, health, service, and attention to detail",
        "7": "one-on-one partnerships, marriage, and open relationships",
        "8": "transformation, shared resources, intimacy, and deep bonding",
        "9": "higher learning, philosophy, travel, and belief systems",
        "10": "career, public reputation, life direction, and achievements",
        "11": "friendships, groups, community, and future aspirations",
        "12": "inner world, spirituality, subconscious, and hidden strength",
    }
    return meanings.get(house_num, "personal growth and life experience")


def get_asc_first_impression(sign):
    """First impression given by an ascendant sign."""
    impressions = {
        "Ari": "confidence and immediate presence",
        "Tau": "calm stability and approachable warmth",
        "Gem": "curiosity and quick wit",
        "Can": "gentle nurturing and sensitivity",
        "Leo": "charisma and natural authority",
        "Vir": "refinement and attention to detail",
        "Lib": "charm and diplomatic grace",
        "Sco": "mystery and magnetic intensity",
        "Sag": "optimism and adventurous spirit",
        "Cap": "seriousness and quiet authority",
        "Aqu": "uniqueness and intellectual independence",
        "Pis": "gentleness and ethereal quality",
    }
    return impressions.get(sign, "a distinctive and memorable presence")


if __name__ == "__main__":
    main()
