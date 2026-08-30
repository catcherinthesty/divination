"""HTML/SVG/JSON chart renderer.

Takes a validated BirthRecord and the Astrologer MCP API response
(chart_data + SVG string) and produces three deterministic output files:

- {initials}_chart.svg     — the rendered chart wheel (written verbatim)
- {initials}_chart.html    — full analysis page from templates/chart.html
- {initials}_api_call.json — input subject, API endpoint, and raw response

All file writes go through chart_writer.atomic_write() (FR-010).
Rendering is pure function of inputs: same chart_data + record always
produces byte-identical files (constitution Principle I).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..data_types import BirthRecord, ChartOutput
from .chart_writer import atomic_write
from .naming import api_call_filename, chart_filename, generate_initials

API_URL = "/api/v5/chart/birth-chart"
API_METHOD = "POST"

_TEMPLATE_PATH = Path(__file__).resolve().parent / "templates" / "chart.html"

# Deterministic display order for the planet table
_PLANET_ORDER = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Pluto", "Chiron", "Ascendant", "Descendant",
    "Medium_Coeli", "Imum_Coeli", "True_North_Lunar_Node",
    "True_South_Lunar_Node", "Mean_Lilith",
]

HOUSE_ORDINALS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9,
    "tenth": 10, "eleventh": 11, "twelfth": 12,
}


def render_chart(
    record: BirthRecord,
    chart_data: dict[str, Any],
    svg_content: str,
    output_dir: str | Path = ".",
    subject_payload: dict[str, Any] | None = None,
) -> ChartOutput:
    """Render all three chart output files for a single subject.

    Args:
        record: Validated BirthRecord (name is used for the page title).
        chart_data: The "chart_data" object from the Astrologer API response.
        svg_content: The rendered SVG string from the API response ("chart").
        output_dir: Directory to write output files into.
        subject_payload: Original API request subject block, recorded in
            api_call.json for reproducibility (FR-011).

    Returns:
        ChartOutput with paths to the three written files.
    """
    out = Path(output_dir)
    initials = generate_initials(record.name)
    sub = chart_data.get("subject", {})

    planets = _extract_planets(sub)
    lunar = sub.get("lunar_phase") or {}

    # Header fields from API subject data (fall back to BirthRecord)
    birth_dt = sub.get("iso_formatted_local_datetime", "")
    city = sub.get("city", record.location_description)
    nation = sub.get("nation", record.nation_code or "")
    tz = sub.get("tz_str", record.timezone or "")
    house_system = sub.get("houses_system_name", "Placidus")
    zodiac = sub.get("zodiac_type", "Tropical")
    diurnal = "Diurnal" if sub.get("is_diurnal") else "Nocturnal"
    phase_name = lunar.get("moon_phase_name", "")
    lunar_phase_text = (
        f" · {lunar.get('moon_emoji', '')} {phase_name}" if phase_name else ""
    )

    def _sign(name: str) -> str:
        p = planets.get(name, {})
        return f"{p.get('emoji', '')} {p.get('sign', '')}".strip()

    elements, qualities = _distributions(planets)
    total_e = sum(elements.values()) or 1

    def _pct(n: int) -> int:
        return int(round(n / total_e * 100))

    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.format(
        name=record.name,
        birth_dt=birth_dt,
        tz=tz,
        city=city,
        nation=nation,
        house_system=house_system,
        zodiac=zodiac,
        diurnal=diurnal,
        lunar_phase_text=lunar_phase_text,
        sun_sign=_sign("Sun"),
        moon_sign=_sign("Moon"),
        asc_sign=_sign("Ascendant"),
        mercury_sign=_sign("Mercury"),
        venus_sign=_sign("Venus"),
        mars_sign=_sign("Mars"),
        phase_name=phase_name,
        chart_ruler=_get_chart_ruler(planets),
        svg_filename=chart_filename(initials, "svg"),
        planet_table_rows=_build_planet_table(planets),
        house_cusp_rows=_build_house_table(sub),
        aspect_rows=_build_aspect_table(chart_data),
        fire_pct=_pct(elements["Fire"]),
        earth_pct=_pct(elements["Earth"]),
        air_pct=_pct(elements["Air"]),
        water_pct=_pct(elements["Water"]),
        fire_count=elements["Fire"],
        earth_count=elements["Earth"],
        air_count=elements["Air"],
        water_count=elements["Water"],
        quality_rows=_build_quality_table(qualities),
        interpretation_text=_build_interpretation(planets, chart_data),
    )

    svg_path = out / chart_filename(initials, "svg")
    html_path = out / chart_filename(initials, "html")
    json_path = out / api_call_filename(initials)

    atomic_write(svg_path, svg_content)
    atomic_write(html_path, html)
    atomic_write(json_path, _build_api_call_json(subject_payload or {}, chart_data))

    return ChartOutput(
        svg_path=str(svg_path),
        html_path=str(html_path),
        json_path=str(json_path),
        subject_name=record.name,
        initials=initials,
    )


# --- Data extraction and table builders ---


def _extract_planets(sub: dict[str, Any]) -> dict[str, Any]:
    """Extract planetary point dicts from the API subject block.

    The API nests each point under its own key; points are identified by
    point_type == "AstrologicalPoint" and carry a "name" field.
    """
    planets: dict[str, Any] = {}
    for val in sub.values():
        if (
            isinstance(val, dict)
            and val.get("point_type") == "AstrologicalPoint"
            and "name" in val
        ):
            planets[val["name"]] = val
    return planets


def _house_number(house: str) -> str:
    """Convert an API house string (e.g. 'fifth_house') to a numeral."""
    if not house:
        return "?"
    word = house.split("_")[0].lower()
    return str(HOUSE_ORDINALS.get(word, "?"))


def _build_planet_table(planets: dict[str, Any]) -> str:
    """Build HTML table rows for the planet list (deterministic order)."""
    rows: list[str] = []
    for pname in _PLANET_ORDER:
        p = planets.get(pname)
        if not p:
            continue
        display_name = pname.replace("_", " ")
        house_num = _house_number(p.get("house", ""))
        retro = "R" if p.get("retrograde") else "&nbsp;"
        deg = p.get("position", 0) or 0
        rows.append(
            f"<tr><td>{p.get('emoji', '')} {display_name}</td>"
            f"<td>{p.get('sign', '')}{deg:.1f}°</td>"
            f"<td>{house_num}</td><td>{retro}</td>"
            f"<td>{p.get('element', '')} {p.get('quality', '')}</td></tr>"
        )
    return "\n".join(rows)


def _build_house_table(sub: dict[str, Any]) -> str:
    """Build HTML table rows for the twelve house cusps."""
    rows: list[str] = []
    for word, num in HOUSE_ORDINALS.items():
        h = sub.get(f"{word}_house")
        if not h:
            continue
        deg = h.get("position", 0) or 0
        rows.append(
            f"<tr><td>{h.get('emoji', '')} H{num}</td>"
            f"<td>{h.get('sign', '')}{deg:.1f}°</td></tr>"
        )
    return "\n".join(rows)


def _build_aspect_table(chart_data: dict[str, Any]) -> str:
    """Build HTML table rows for major aspects (orb ≤ 8°)."""
    rows: list[str] = []
    for a in chart_data.get("aspects", []):
        atype = a.get("aspect", "")
        orb = a.get("orbit", 999) or 0
        if atype not in ("conjunction", "square", "trine", "opposition") or orb > 8:
            continue
        movement = a.get("aspect_movement", "")
        arrow = "→" if movement == "Applying" else "←"
        cls = "applying" if movement == "Applying" else "separating"
        rows.append(
            f"<tr><td>{a.get('p1_name', '')}</td>"
            f"<td class='highlight'>{atype}</td>"
            f"<td>{a.get('p2_name', '')}</td>"
            f"<td>{orb:.1f}°</td>"
            f"<td class='{cls}'>{arrow} {movement}</td></tr>"
        )
    if not rows:
        rows.append(
            '<tr><td colspan="5" style="color:#777">'
            "No major aspects within 8° orb</td></tr>"
        )
    return "\n".join(rows)


def _distributions(planets: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]]:
    """Count element and quality distributions across all planetary points."""
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    qualities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    for p in planets.values():
        e = p.get("element", "")
        if e in elements:
            elements[e] += 1
        q = p.get("quality", "")
        if q in qualities:
            qualities[q] += 1
    return elements, qualities


def _build_quality_table(qualities: dict[str, int]) -> str:
    """Build HTML table rows for the quality distribution."""
    return "\n".join(
        f"<tr><td>{q}</td><td>{c}</td></tr>" for q, c in qualities.items()
    )


_RULERS = {
    "Ari": "Mars ♂", "Tau": "Venus ♀", "Gem": "Mercury ☿",
    "Can": "Moon ☽", "Leo": "Sun ☉", "Vir": "Mercury ☿",
    "Lib": "Venus ♀", "Sco": "Mars ♂/Pluto ♇",
    "Sag": "Jupiter ♃", "Cap": "Saturn ♄",
    "Aqu": "Saturn ♄/Uranus ⛢", "Pis": "Jupiter ♃/Neptune ♆",
}


def _get_chart_ruler(planets: dict[str, Any]) -> str:
    """Determine the chart ruler from the Ascendant sign."""
    sign = planets.get("Ascendant", {}).get("sign", "")
    return _RULERS.get(sign, sign or "?")


def _build_api_call_json(
    subject_payload: dict[str, Any],
    chart_data: dict[str, Any],
) -> str:
    """Build the api_call.json record (FR-011): endpoint, input, raw output."""
    record = {
        "api": {
            "url": API_URL,
            "method": API_METHOD,
            "endpoint_description": (
                "Generates a natal chart (birth chart) for a specific person and time. "
                "Returns both the calculated astrological data and a rendered SVG chart."
            ),
        },
        "input": subject_payload,
        "output": {
            "status": "OK",
            "chart_data": chart_data,
        },
    }
    return json.dumps(record, indent=2, ensure_ascii=False) + "\n"


# --- Interpretation lookup tables (deterministic text per sign/house) ---

SUN_TRAITS = {
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

MOON_TRAITS = {
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

ASC_TRAITS = {
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

ASC_FIRST_IMPRESSION = {
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

HOUSE_MEANINGS = {
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

MERC_TRAITS = {
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

VENUS_TRAITS = {
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

MARS_TRAITS = {
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

_ORDINAL_SUFFIX = {1: "st", 2: "nd", 3: "rd"}


def _ordinal(n: int) -> str:
    """Return the ordinal form of a house number (1 → '1st')."""
    return f"{n}{_ORDINAL_SUFFIX.get(n, 'th')}"


def _house_meaning(house_num: str) -> str:
    """Look up the life-area meaning for a house numeral string."""
    return HOUSE_MEANINGS.get(house_num, "personal growth and life experience")


def _build_interpretation(
    planets: dict[str, Any],
    chart_data: dict[str, Any],
) -> str:
    """Build the deterministic interpretation paragraphs (HTML)."""
    sun = planets.get("Sun", {})
    moon = planets.get("Moon", {})
    asc = planets.get("Ascendant", {})
    merc = planets.get("Mercury", {})
    venus = planets.get("Venus", {})
    mars = planets.get("Mars", {})

    def _house(n: str) -> int:
        return HOUSE_ORDINALS.get(n.split("_")[0].lower(), 0) if n else 0

    sun_h = _house(sun.get("house", ""))
    moon_h = _house(moon.get("house", ""))

    paragraphs: list[str] = []

    if sun:
        sun_s = sun.get("sign", "")
        paragraphs.append(
            f'<p><strong>Sun in {sun_s} ({_ordinal(sun_h)} House)</strong>: '
            f'This chart is anchored by a Sun in {sun_s}, bringing '
            f'{SUN_TRAITS.get(sun_s, "a unique blend of energies")}. '
            f'In the {_ordinal(sun_h)} house, self-expression finds its outlet through '
            f'{_house_meaning(str(sun_h))}.</p>'
        )

    if moon:
        moon_s = moon.get("sign", "")
        paragraphs.append(
            f'<p><strong>Moon in {moon_s} ({_ordinal(moon_h)} House)</strong>: '
            f'Emotionally, this person experiences '
            f'{MOON_TRAITS.get(moon_s, "complex feelings")}. '
            f'Moon in the {_ordinal(moon_h)} house suggests emotional security through '
            f'{_house_meaning(str(moon_h))}.</p>'
        )

    if asc:
        asc_s = asc.get("sign", "")
        paragraphs.append(
            f'<p><strong>Ascendant {asc_s}</strong>: '
            f'The lens through which this person approaches life is '
            f'{ASC_TRAITS.get(asc_s, "distinctive")}. '
            f'With {asc_s} rising, the first impression given to others is one of '
            f'{ASC_FIRST_IMPRESSION.get(asc_s, "a distinctive and memorable presence")}.</p>'
        )

    if merc:
        merc_s = merc.get("sign", "")
        paragraphs.append(
            f'<p><strong>Mercury in {merc_s}</strong>: '
            f'Communication and thought process is '
            f'{MERC_TRAITS.get(merc_s, "distinctive")}.</p>'
        )

    if venus:
        venus_s = venus.get("sign", "")
        paragraphs.append(
            f'<p><strong>Venus in {venus_s}</strong>: '
            f'In love and beauty, this person expresses '
            f'{VENUS_TRAITS.get(venus_s, "a distinctive style")}.</p>'
        )

    if mars:
        mars_s = mars.get("sign", "")
        paragraphs.append(
            f'<p><strong>Mars in {mars_s}</strong>: '
            f'Drive, energy, and action style is '
            f'{MARS_TRAITS.get(mars_s, "distinctive")}.</p>'
        )

    key_aspects = [
        a for a in chart_data.get("aspects", [])
        if a.get("aspect") in ("conjunction", "square", "trine", "opposition")
        and (a.get("orbit", 999) or 0) <= 6
    ]
    if key_aspects:
        aspect_list = ", ".join(
            f"{a['p1_name']} {a['aspect']} {a['p2_name']} (orb {a['orbit']:.1f}°)"
            for a in key_aspects[:6]
        )
        paragraphs.append(
            f'<p><strong>Major Aspects</strong>: Notable aspects include '
            f'{aspect_list}.</p>'
        )

    return "\n".join(paragraphs)

