"""Interpretations for gematria core numbers.

Each system produces totals from 1–108 (for typical names).
Interpretations are keyed by reduced value (1-9, 11, 22, 33) with
famous-pair context for the raw total.

Gematria tradition associates specific numbers with spiritual meanings;
reduced values map to kabbalistic/Pythagorean number symbolism.
"""

from __future__ import annotations

# ── Core interpretations keyed by reduced value ──────────────────────

CORE: dict[int, dict[str, str | list[str]]] = {
    1: {
        "title": "Unity & Will",
        "summary": "The number of creation, leadership, and individuality. Represents the spark of divine will manifesting as form.",
        "strengths": ["Initiative", "Independence", "Courage", "Originality"],
        "challenges": ["Isolation", "Domination", "Impatience", "Ego"],
    },
    2: {
        "title": "Balance & Partnership",
        "summary": "The number of duality, cooperation, and sensitivity. Represents the power of relationship and diplomacy.",
        "strengths": ["Cooperation", "Sensitivity", "Diplomacy", "Patience"],
        "challenges": ["Indecision", "Over-sensitivity", "Dependency", "Passivity"],
    },
    3: {
        "title": "Expression & Creativity",
        "summary": "The number of joy, communication, and artistic expression. Represents the creative force of the universe manifesting as beauty.",
        "strengths": ["Creativity", "Communication", "Joy", "Inspiration"],
        "challenges": ["Scattered energy", "Superficiality", "Moodiness", "Gossip"],
    },
    4: {
        "title": "Foundation & Stability",
        "summary": "The number of structure, discipline, and hard work. Represents the four corners of the earth and the foundation of lasting achievement.",
        "strengths": ["Stability", "Organization", "Reliability", "Diligence"],
        "challenges": ["Rigidity", "Boredom", "Limiting self", "Stubbornness"],
    },
    5: {
        "title": "Freedom & Change",
        "summary": "The number of adventure, versatility, and dynamic change. Represents the five senses and the restless spirit of exploration.",
        "strengths": ["Adaptability", "Curiosity", "Resourcefulness", "Versatility"],
        "challenges": ["Restlessness", "Inconsistency", "Excess", "Irresponsibility"],
    },
    6: {
        "title": "Harmony & Responsibility",
        "summary": "The number of love, nurturing, and domestic harmony. Represents the golden ratio and the balance of giving and receiving.",
        "strengths": ["Compassion", "Responsibility", "Healing", "Protection"],
        "challenges": ["Self-sacrifice", "Interference", "Perfectionism", "Martyrdom"],
    },
    7: {
        "title": "Wisdom & Spirituality",
        "summary": "The number of introspection, analysis, and spiritual seeking. Represents the seven days of creation and the search for hidden truth.",
        "strengths": ["Wisdom", "Intuition", "Analysis", "Spirituality"],
        "challenges": ["Secretiveness", "Isolation", "Doubt", "Cynicism"],
    },
    8: {
        "title": "Power & Abundance",
        "summary": "The number of material mastery, authority, and cosmic justice. Represents the infinity symbol — infinite flow of abundance.",
        "strengths": ["Achievement", "Authority", "Business acumen", "Efficiency"],
        "challenges": ["Materialism", "Workaholism", "Control", "Ruthlessness"],
    },
    9: {
        "title": "Humanity & Completion",
        "summary": "The number of universal love, compassion, and spiritual completion. Represents the end of a cycle and the wisdom gained.",
        "strengths": ["Compassion", "Generosity", "Tolerance", "Idealism"],
        "challenges": ["Disillusionment", "Moodiness", "Attachment", "Detachment"],
    },
    11: {
        "title": "Illumination (Master Number)",
        "summary": "The master number of spiritual illumination, intuition, and visionary leadership. Represents the channel between divine and human.",
        "strengths": ["Inspiration", "Intuition", "Idealism", "Enlightenment"],
        "challenges": ["Anxiety", "Unrealistic ideals", "Nervous tension", "Impressionability"],
    },
    22: {
        "title": "Master Builder (Master Number)",
        "summary": "The most powerful master number — the ability to turn grand visions into tangible reality on a massive scale.",
        "strengths": ["Visionary leadership", "Practical idealism", "Great accomplishment"],
        "challenges": ["Overwhelm", "Self-doubt", "Pressure", "Tyranny"],
    },
    33: {
        "title": "Master Teacher (Master Number)",
        "summary": "The rarest master number — spiritual mastery through selfless service and compassionate teaching for the highest good.",
        "strengths": ["Spiritual mastery", "Nurturing", "Healing", "Selfless love"],
        "challenges": ["Self-neglect", "Idealism", "Emotional burden", "Martyrdom"],
    },
}

# ── Famous pairs — numbers that share the same reduced value ──────────

FAMOUS_PAIRS: dict[int, list[tuple[int, str]]] = {
    1: [
        (1, "The primal spark of creation"),
        (10, "Self-awareness and independence"),
        (19, "Karmic lesson in self-reliance"),
        (28, "Leadership through practical means"),
        (37, "Creative authority and spiritual will"),
        (46, "Building lasting foundations of power"),
        (55, "Dynamic double freedom — master builder of change"),
        (64, "Authority tempered by responsibility"),
        (73, "Spiritual mastery through wisdom"),
        (82, "Material and spiritual abundance combined"),
        (91, "Humanitarian leadership with universal vision"),
    ],
    2: [
        (2, "The power of partnership"),
        (11, "Illumination — master number channeling"),
        (20, "Diplomacy and intuitive insight"),
        (29, "Sensitive leadership through cooperation"),
        (38, "Creative harmony in relationships"),
        (47, "Stable partnerships built on wisdom"),
        (56, "Adaptability through cooperation"),
        (65, "Nurturing change through balance"),
        (74, "Spiritual partnership and stability"),
        (83, "Authority through creative expression"),
        (92, "Humanitarian partnership with sensitivity"),
    ],
    3: [
        (3, "Pure creative expression"),
        (12, "Joyful communication and social grace"),
        (21, "Artistic talent with cooperative spirit"),
        (30, "Creative self-expression at full power"),
        (39, "Mastery of artistic communication"),
        (48, "Structured creativity and practical artistry"),
        (57, "Adventurous creative spirit"),
        (66, "Double nurturing through creative expression"),
        (75, "Wisdom expressed through dynamic change"),
        (84, "Material success through creative means"),
        (93, "Universal love expressed artistically"),
    ],
    4: [
        (4, "The architect of reality"),
        (13, "Transformation through disciplined work"),
        (22, "Master Builder — vision made manifest"),
        (31, "Creative foundation and independent building"),
        (40, "Self-built structure and discipline"),
        (49, "Karmic mastery of the material world"),
        (58, "Dynamic stability and progressive foundations"),
        (67, "Nurturing through spiritual wisdom"),
        (76, "Authority grounded in spiritual understanding"),
        (85, "Material power balanced with freedom"),
        (94, "Humanitarian service through disciplined action"),
    ],
    5: [
        (5, "The restless explorer"),
        (14, "Freedom through transformative change"),
        (23, "Creative adventure and communication"),
        (32, "Cooperative versatility and charm"),
        (41, "Independent freedom with practical grounding"),
        (50, "Self-realized freedom and adaptability"),
        (59, "Dynamic transformation through change"),
        (68, "Nurturing the adventurer within"),
        (77, "Double spiritual insight through experience"),
        (86, "Material mastery balanced with harmony"),
        (95, "Humanitarian freedom and universal love"),
    ],
    6: [
        (6, "The cosmic nurturer"),
        (15, "Freedom through responsibility"),
        (24, "Creative stability and harmonious building"),
        (33, "Master Teacher — selfless compassion"),
        (42, "Structured nurturing and cooperative love"),
        (51, "Independent responsibility and adaptability"),
        (60, "Self-realized harmony and domestic mastery"),
        (69, "Nurturing through universal understanding"),
        (78, "Spiritual authority with material responsibility"),
        (87, "Material power tempered by spiritual wisdom"),
        (96, "Humanitarian love expressed through service"),
    ],
    7: [
        (7, "The mystic and seeker"),
        (16, "Awakening through spiritual crisis"),
        (25, "Adventurous wisdom and spiritual exploration"),
        (34, "Creative foundation in spiritual matters"),
        (43, "Structured creativity with deep analysis"),
        (52, "Dynamic partnership in spiritual seeking"),
        (61, "Nurturing through independent wisdom"),
        (70, "Self-realized spiritual mastery"),
        (79, "Spiritual authority and universal understanding"),
        (88, "Double material-spiritual balance"),
        (97, "Humanitarian wisdom and spiritual completion"),
    ],
    8: [
        (8, "The master of abundance"),
        (17, "Authority through spiritual wisdom"),
        (26, "Material power balanced with nurturing"),
        (35, "Creative expression leading to abundance"),
        (44, "Double foundation of material success"),
        (53, "Dynamic creativity in the material world"),
        (62, "Harmonious partnership building wealth"),
        (71, "Spiritual wisdom expressed as authority"),
        (80, "Self-realized material mastery"),
        (89, "Authority through universal understanding"),
        (98, "Humanitarian leadership and abundance"),
    ],
    9: [
        (9, "The humanitarian and sage"),
        (18, "Spiritual authority with material wisdom"),
        (27, "Creative partnership in service of humanity"),
        (36, "Artistic expression of universal love"),
        (45, "Structured freedom in humanitarian work"),
        (54, "Dynamic foundation for global change"),
        (63, "Nurturing through creative expression"),
        (72, "Spiritual partnership with cooperative wisdom"),
        (81, "Mastery of abundance in service of others"),
        (90, "Self-realized humanitarian vision"),
    ],
    11: [
        (11, "The illuminator — channel between divine and human"),
        (20, "Intuitive insight amplified by spiritual awareness"),
        (29, "Sensitive leadership through visionary means"),
        (38, "Creative harmony in spiritual relationships"),
        (47, "Stable partnerships built on enlightenment"),
        (56, "Adaptability through spiritual insight"),
        (65, "Nurturing change through illumination"),
        (74, "Spiritual partnership and intuitive wisdom"),
        (83, "Authority through creative vision"),
        (92, "Humanitarian partnership with illumination"),
    ],
    22: [
        (22, "The master builder — vision made manifest"),
        (31, "Leadership through practical construction"),
        (40, "Self-built structure and discipline"),
        (49, "Karmic mastery of the material world"),
        (58, "Dynamic stability and progressive foundations"),
        (67, "Nurturing through spiritual wisdom"),
        (76, "Authority grounded in spiritual understanding"),
        (85, "Material power balanced with freedom"),
        (94, "Humanitarian service through disciplined action"),
        (103, "Grand vision tempered by worldly experience"),
    ],
    33: [
        (33, "The master teacher — selfless compassion and healing"),
        (42, "Structured nurturing and cooperative love"),
        (51, "Independent responsibility and adaptability"),
        (60, "Self-realized harmony and domestic mastery"),
        (69, "Nurturing through universal understanding"),
        (78, "Spiritual authority with material responsibility"),
        (87, "Material power tempered by spiritual wisdom"),
        (96, "Humanitarian love expressed through service"),
        (105, "Teaching compassion on a global scale"),
        (114, "Mastery of healing through creative expression"),
    ],
}

# ── System-specific notes ────────────────────────────────────────────

SYSTEM_NOTES: dict[str, dict[str, str]] = {
    "simple": {
        "name": "Simple (Pythagorean)",
        "description": "Cyclic values 1-9 repeated across the alphabet. A=1,B=2,…,I=9,J=1,…,R=9,S=1,…,Z=8.",
        "tradition": "Most common in Western gematria and numerology. Associated with Pythagorean number mysticism.",
    },
    "ordinal": {
        "name": "Full Ordinal",
        "description": "Straight alphabetical values: A=1, B=2, …, Z=26.",
        "tradition": "Used in some English gematria traditions. Higher totals reflect the full alphabet position.",
    },
    "reverse": {
        "name": "Reverse Ordinal",
        "description": "Reverse alphabetical values: A=26, B=25, …, Z=1.",
        "tradition": "Less common but historically significant. Some traditions view it as revealing hidden or inverted meanings.",
    },
}


def get_core_interpretation(number: int) -> dict[str, str | list[str]]:
    """Look up the core interpretation for a reduced number."""
    data = CORE.get(number)
    if data is None:
        # Fallback: reduce and look up again
        from .data_types import reduce_number as _reduce
        reduced = _reduce(number)
        return CORE.get(reduced, {
            "title": f"Number {number}",
            "summary": "Interpretation not available.",
            "strengths": [],
            "challenges": [],
        })
    return data


def get_famous_pairs(number: int) -> list[tuple[int, str]]:
    """Get famous pairs for a reduced number."""
    from .data_types import reduce_number as _reduce
    reduced = _reduce(number)
    return FAMOUS_PAIRS.get(reduced, [])


def format_interpretation(number: int, system_name: str = "") -> str:
    """Format a human-readable interpretation paragraph for a gematria number."""
    interp = get_core_interpretation(number)
    title = interp.get("title", f"Number {number}")
    summary = interp.get("summary", "")

    parts: list[str] = []
    prefix = f"**{system_name}** " if system_name else ""
    parts.append(f"{prefix}{title} ({number}): {summary}")

    strengths = interp.get("strengths", [])
    challenges = interp.get("challenges", [])
    if strengths:
        parts.append(f"Strengths: {', '.join(str(s) for s in strengths)}")
    if challenges:
        parts.append(f"Challenges: {', '.join(str(c) for c in challenges)}")

    # Famous pairs context
    famous = get_famous_pairs(number)
    if famous:
        pair_names = [f"{val} ({desc})" for val, desc in famous[:5]]
        parts.append(f"Famous pairs: {', '.join(pair_names)}{' …' if len(famous) > 5 else ''}")

    return "\n".join(parts)


def get_system_note(system: System) -> dict[str, str]:
    """Get descriptive note for a gematria system."""
    key = system.value.lower()
    return SYSTEM_NOTES.get(key, {
        "name": system.value,
        "description": "Gematria calculation system.",
        "tradition": "",
    })
