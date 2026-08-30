"""Interpretations for Ba Zi (Four Pillars of Destiny).

Element interactions, day master profiles, pillar meanings, and luck cycle analysis.
All interpretations are deterministic lookup tables — same input always produces same output.
"""

from __future__ import annotations

# ── Five Elements (五行) interactions ────────────────────────────────────
ELEMENTS = {
    "Wood": {"emoji": "🌳", "color": "#2d5016", "direction": "East", "season": "Spring"},
    "Fire": {"emoji": "🔥", "color": "#c0392b", "direction": "South", "season": "Summer"},
    "Earth": {"emoji": "⛰️", "color": "#8d6e63", "direction": "Center", "season": "Late Summer"},
    "Metal": {"emoji": "⚔️", "color": "#bdc3c7", "direction": "West", "season": "Autumn"},
    "Water": {"emoji": "💧", "color": "#2980b9", "direction": "North", "season": "Winter"},
}

# Generating cycle (creation): Wood→Fire→Earth→Metal→Water→Wood
GENERATING_CYCLE = {
    "Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood",
}

# Overcoming cycle (destruction): Wood→Earth→Water→Fire→Metal→Wood
OVERCOMING_CYCLE = {
    "Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood",
}


def get_element_description(element: str) -> dict:
    """Get detailed description for an element."""
    base = ELEMENTS.get(element, {})
    generating = GENERATING_CYCLE.get(element, "")
    overcoming = OVERCOMING_CYCLE.get(element, "")

    return {
        **base,
        "generates": generating,
        "overcome_by": next((k for k, v in GENERATING_CYCLE.items() if v == element), ""),
        "overcomes": overcoming,
    }


# ── Day Master profiles ──────────────────────────────────────────────────
DAY_MASTER_PROFILES = {
    ("Yang", "Wood"): {
        "title": "Jia Wood (甲木) — The Great Tree",
        "description": "Like a towering tree reaching for the sky. Strong-willed, upright, and benevolent. Values growth, education, and long-term vision.",
        "strengths": ["Benevolence", "Growth-oriented", "Upright character", "Educational focus"],
        "challenges": ["Stubbornness", "Inflexibility", "Impatience with slow growth"],
    },
    ("Yin", "Wood"): {
        "title": "Yi Wood (乙木) — The Vine/Flower",
        "description": "Like a vine or flower that bends but doesn't break. Adaptable, resourceful, and socially skilled.",
        "strengths": ["Adaptability", "Resourcefulness", "Social grace", "Resilience"],
        "challenges": ["Indecisiveness", "Over-dependence on others", "Lack of direction"],
    },
    ("Yang", "Fire"): {
        "title": "Bing Fire (丙火) — The Sun",
        "description": "Like the sun — warm, generous, and illuminating. Natural leader who shines on everyone.",
        "strengths": ["Warmth", "Generosity", "Leadership", "Illumination"],
        "challenges": ["Overbearing", "Inconsistency", "Burnout from over-giving"],
    },
    ("Yin", "Fire"): {
        "title": "Ding Fire (丁火) — The Candle",
        "description": "Like a candle flame — focused, precise, and illuminating in darkness. Intellectual and detail-oriented.",
        "strengths": ["Precision", "Intellectual depth", "Guidance in darkness"],
        "challenges": ["Fickleness", "Self-doubt", "Over-analysis"],
    },
    ("Yang", "Earth"): {
        "title": "Wu Earth (戊土) — The Mountain",
        "description": "Like a mountain — stable, immovable, and trustworthy. Provides foundation for others.",
        "strengths": ["Stability", "Trustworthiness", "Patience", "Protection"],
        "challenges": ["Rigidity", "Slow to change", "Emotional coldness"],
    },
    ("Yin", "Earth"): {
        "title": "Ji Earth (己土) — The Garden Soil",
        "description": "Like fertile garden soil — nurturing, productive, and supportive. Nourishes growth in others.",
        "strengths": ["Nurturing", "Productivity", "Supportiveness", "Tolerance"],
        "challenges": ["Over-accommodation", "Lack of boundaries", "Moodiness"],
    },
    ("Yang", "Metal"): {
        "title": "Geng Metal (庚金) — The Sword",
        "description": "Like a sword or axe — decisive, strong, and justice-oriented. Acts with directness and courage.",
        "strengths": ["Decisiveness", "Courage", "Justice", "Strength"],
        "challenges": ["Ruthlessness", "Conflict-prone", "Lack of subtlety"],
    },
    ("Yin", "Metal"): {
        "title": "Xin Metal (辛金) — The Jewelry",
        "description": "Like jewelry or precious metal — refined, elegant, and value-conscious. Appreciates beauty and quality.",
        "strengths": ["Refinement", "Elegance", "Value-orientation", "Attention to detail"],
        "challenges": ["Vanity", "Pretentiousness", "Over-sensitivity"],
    },
    ("Yang", "Water"): {
        "title": "Ren Water (壬水) — The Ocean",
        "description": "Like the ocean — vast, powerful, and unstoppable. Adaptable in form but relentless in purpose.",
        "strengths": ["Vastness", "Power", "Adaptability", "Wisdom"],
        "challenges": ["Overwhelming", "Unpredictable", "Lack of boundaries"],
    },
    ("Yin", "Water"): {
        "title": "Gui Water (癸水) — The Rain/Dew",
        "description": "Like rain or dew — gentle, penetrating, and nourishing. Nurtures through persistence.",
        "strengths": ["Gentleness", "Penetration", "Nurturing", "Intuition"],
        "challenges": ["Melancholy", "Over-sensitivity", "Indecisiveness"],
    },
}


def get_day_master_profile(yin_yang: str, element: str) -> dict:
    """Get the day master profile for a given yin-yang + element combination."""
    key = (yin_yang, element)
    return DAY_MASTER_PROFILES.get(key, {
        "title": f"{yin_yang} {element}",
        "description": "Day master information not available.",
        "strengths": [],
        "challenges": [],
    })


# ── Pillar meanings ──────────────────────────────────────────────────────
PILLAR_MEANINGS = {
    "Year (年)": {
        "area": "Ancestors, grandparents, early childhood (ages 0-16), public image",
        "meaning": "Represents your ancestral foundation and the era you were born into. Shows early environment and family background.",
    },
    "Month (月)": {
        "area": "Parents, siblings, youth (ages 17-32), career foundation",
        "meaning": "The most important pillar — represents your parents and the social environment that shaped you. Indicates career orientation and sibling relationships.",
    },
    "Day (日)": {
        "area": "Self and spouse, middle age (ages 33-48), inner self",
        "meaning": "The Day Master (day stem) represents YOU — your core identity. The day branch represents your spouse palace and innermost self.",
    },
    "Hour (时)": {
        "area": "Children, later life (ages 49+), aspirations, subordinates",
        "meaning": "Represents your children, your legacy, and what you aspire to create. Shows your private thoughts and ambitions.",
    },
}


# ── Element balance analysis ─────────────────────────────────────────────
def analyze_element_balance(element_counts: dict[str, int]) -> dict:
    """Analyze the element distribution and identify dominant/weak elements."""
    total = sum(element_counts.values()) or 1
    percentages = {k: round(v / total * 100) for k, v in element_counts.items()}

    # Find strongest and weakest
    sorted_elements = sorted(percentages.items(), key=lambda x: -x[1])
    dominant = sorted_elements[0] if sorted_elements else ("", 0)
    weak = sorted_elements[-1] if sorted_elements else ("", 0)

    # Check for extreme imbalance (>40% of any element)
    imbalanced = {k: v for k, v in percentages.items() if v > 40}

    return {
        "percentages": percentages,
        "dominant_element": dominant[0],
        "dominant_percentage": dominant[1],
        "weakest_element": weak[0],
        "weakest_percentage": weak[1],
        "imbalanced_elements": imbalanced,
        "is_balanced": len(imbalanced) == 0,
    }


# ── Generating cycle interpretation ───────────────────────────────────────
def get_generating_relationships(element: str) -> dict:
    """Get the generating (creation) cycle relationships for an element."""
    base = get_element_description(element)
    return {
        "element": element,
        "generates": base.get("generates", ""),
        "overcome_by": base.get("overcome_by", ""),
        "description": f"{element} generates {base.get('generates', '')} and is generated by {base.get('overcome_by', '')}.",
    }
