"""Interpretations for numerology core numbers.

Each system (Pythagorean, Chaldean) has its own interpretation data.
Numbers: 1-9 plus master numbers 11, 22, 33.
Categories: life_path, expression, soul_urge, personality, birthday.
"""

from __future__ import annotations

INTERPRETATIONS: dict[str, dict[int, dict[str, str]]] = {
    "life_path": {
        1: {
            "title": "The Leader",
            "summary": "Independent, ambitious, and pioneering. You forge your own path.",
            "strengths": ["Leadership", "Originality", "Determination"],
            "challenges": ["Stubbornness", "Isolation", "Aggression"],
        },
        2: {
            "title": "The Diplomat",
            "summary": "Cooperative, sensitive, and peace-making. You build bridges between people.",
            "strengths": ["Diplomacy", "Patience", "Intuition"],
            "challenges": ["Over-sensitivity", "Indecision", "Passivity"],
        },
        3: {
            "title": "The Communicator",
            "summary": "Creative, expressive, and joyful. You inspire through words and art.",
            "strengths": ["Creativity", "Communication", "Optimism"],
            "challenges": ["Scattered energy", "Superficiality", "Moodiness"],
        },
        4: {
            "title": "The Builder",
            "summary": "Practical, disciplined, and reliable. You create lasting foundations.",
            "strengths": ["Stability", "Organization", "Hard work"],
            "challenges": ["Rigidity", "Boredom", "Limiting self"],
        },
        5: {
            "title": "The Adventurer",
            "summary": "Dynamic, freedom-loving, and versatile. You thrive on change.",
            "strengths": ["Adaptability", "Curiosity", "Resourcefulness"],
            "challenges": ["Restlessness", "Inconsistency", "Excess"],
        },
        6: {
            "title": "The Nurturer",
            "summary": "Responsible, caring, and harmonious. You create beauty and balance.",
            "strengths": ["Compassion", "Responsibility", "Healing"],
            "challenges": ["Self-sacrifice", "Interference", "Perfectionism"],
        },
        7: {
            "title": "The Seeker",
            "summary": "Analytical, introspective, and spiritual. You seek deeper truth.",
            "strengths": ["Wisdom", "Intuition", "Research"],
            "challenges": ["Secretiveness", "Isolation", "Doubt"],
        },
        8: {
            "title": "The Powerhouse",
            "summary": "Ambitious, authoritative, and material-minded. You manifest abundance.",
            "strengths": ["Achievement", "Business acumen", "Authority"],
            "challenges": ["Materialism", "Workaholism", "Control"],
        },
        9: {
            "title": "The Humanitarian",
            "summary": "Compassionate, generous, and idealistic. You serve the greater good.",
            "strengths": ["Compassion", "Tolerance", "Creativity"],
            "challenges": ["Moodiness", "Disillusionment", "Attachment"],
        },
        11: {
            "title": "The Illuminator (Master Number)",
            "summary": "Spiritually gifted, inspirational, and visionary. You illuminate the path for others.",
            "strengths": ["Inspiration", "Intuition", "Idealism"],
            "challenges": ["Anxiety", "Unrealistic ideals", "Nervous tension"],
        },
        22: {
            "title": "The Master Builder (Master Number)",
            "summary": "The most powerful number. You turn grand dreams into tangible reality.",
            "strengths": ["Visionary leadership", "Practical idealism", "Great accomplishment"],
            "challenges": ["Overwhelm", "Self-doubt", "Pressure"],
        },
        33: {
            "title": "The Master Teacher (Master Number)",
            "summary": "Rare and powerful. You uplift humanity through selfless service and spiritual teaching.",
            "strengths": ["Spiritual mastery", "Nurturing", "Healing"],
            "challenges": ["Self-neglect", "Idealism", "Emotional burden"],
        },
    },
    "expression": {
        1: {
            "title": "Natural Leader",
            "summary": "Your talents lean toward independence and innovation.",
            "strengths": ["Initiative", "Originality", "Courage"],
            "challenges": ["Ego", "Dominance", "Impatience"],
        },
        2: {
            "title": "Peacemaker",
            "summary": "Your talents lie in cooperation and mediation.",
            "strengths": ["Sensitivity", "Partnership", "Balance"],
            "challenges": ["Dependency", "Timidity", "Over-accommodation"],
        },
        3: {
            "title": "Creative Self-Expresser",
            "summary": "Your talents are in communication, art, and joy.",
            "strengths": ["Artistic ability", "Social grace", "Inspiration"],
            "challenges": ["Gossip", "Scattered focus", "Superficiality"],
        },
        4: {
            "title": "Organizer",
            "summary": "Your talents are in building, planning, and execution.",
            "strengths": ["Reliability", "Methodical approach", "Loyalty"],
            "challenges": ["Dullness", "Stubbornness", "Rigidity"],
        },
        5: {
            "title": "Freedom Seeker",
            "summary": "Your talents are in adaptability and progressive thinking.",
            "strengths": ["Versatility", "Quick thinking", "Magnetism"],
            "challenges": ["Irresponsibility", "Inconsistency", "Indulgence"],
        },
        6: {
            "title": "Responsible Nurturer",
            "summary": "Your talents are in service, healing, and domestic harmony.",
            "strengths": ["Protective nature", "Artistic taste", "Compassion"],
            "challenges": ["Self-righteousness", "Meddling", "Martyrdom"],
        },
        7: {
            "title": "Analytical Thinker",
            "summary": "Your talents are in research, analysis, and spiritual understanding.",
            "strengths": ["Intellectual depth", "Wisdom", "Spirituality"],
            "challenges": ["Cynicism", " aloofness", "Secrecy"],
        },
        8: {
            "title": "Achiever",
            "summary": "Your talents are in business, management, and material mastery.",
            "strengths": ["Executive ability", "Ambition", "Efficiency"],
            "challenges": ["Ruthlessness", "Materialism", "Work obsession"],
        },
        9: {
            "title": "Cosmopolitan Humanitarian",
            "summary": "Your talents are in universal love, tolerance, and artistic expression.",
            "strengths": ["Generosity", "Cultural awareness", "Compassion"],
            "challenges": ["Emotional turmoil", "Obsession", "Detachment"],
        },
        11: {
            "title": "Spiritual Messenger (Master)",
            "summary": "Your talents are in spiritual illumination and inspirational leadership.",
            "strengths": ["Visionary insight", "Charisma", "Idealism"],
            "challenges": ["Impressionability", "Anxiety", "Misguided idealism"],
        },
        22: {
            "title": "Master Architect (Master)",
            "summary": "Your talents are in building large-scale projects that benefit humanity.",
            "strengths": ["Master visionary", "Practical wisdom", "Unusual power"],
            "challenges": ["Self-abnegation", "Pressure", "Tyranny"],
        },
        33: {
            "title": "Spiritual Healer (Master)",
            "summary": "Your talents are in selfless service and spiritual guidance.",
            "strengths": ["Compassionate wisdom", "Healing presence", "Self-sacrifice"],
            "challenges": ["Emotional overload", "Martyrdom", "Unrealistic expectations"],
        },
    },
    "soul_urge": {
        1: {"title": "Desire for Independence", "summary": "You deeply want to lead and be first.", "strengths": ["Drive", "Self-reliance"], "challenges": ["Impatience", "Forcefulness"]},
        2: {"title": "Desire for Harmony", "summary": "You crave partnership, peace, and understanding.", "strengths": ["Empathy", "Cooperation"], "challenges": ["Neediness", "Over-sensitivity"]},
        3: {"title": "Desire for Expression", "summary": "You want to create, communicate, and bring joy.", "strengths": ["Creativity", "Social charm"], "challenges": ["Gossip", "Superficiality"]},
        4: {"title": "Desire for Stability", "summary": "You seek order, structure, and lasting security.", "strengths": ["Determination", "Loyalty"], "challenges": ["Rigidity", "Boredom"]},
        5: {"title": "Desire for Freedom", "summary": "You crave adventure, variety, and personal liberty.", "strengths": ["Curiosity", "Adaptability"], "challenges": ["Restlessness", "Excess"]},
        6: {"title": "Desire for Love & Home", "summary": "You yearn for harmony, beauty, and nurturing others.", "strengths": ["Compassion", "Responsibility"], "challenges": ["Self-sacrifice", "Control"]},
        7: {"title": "Desire for Truth", "summary": "You seek understanding, wisdom, and spiritual knowledge.", "strengths": ["Intuition", "Analysis"], "challenges": ["Isolation", "Doubt"]},
        8: {"title": "Desire for Achievement", "summary": "You want success, recognition, and material abundance.", "strengths": ["Ambition", "Authority"], "challenges": ["Materialism", "Workaholism"]},
        9: {"title": "Desire to Serve", "summary": "You yearn to make the world better through compassion.", "strengths": ["Idealism", "Generosity"], "challenges": ["Disillusionment", "Moodiness"]},
        11: {"title": "Desire for Spiritual Illumination (Master)", "summary": "You are driven to inspire and enlighten others.", "strengths": ["Visionary passion", "Intuitive depth"], "challenges": ["Nervous tension", "Anxiety"]},
        22: {"title": "Desire to Build Legacies (Master)", "summary": "You want to create lasting structures that serve the world.", "strengths": ["Grand vision", "Practical idealism"], "challenges": ["Overwhelm", "Pressure"]},
        33: {"title": "Desire to Heal Humanity (Master)", "summary": "You are driven by selfless love and spiritual teaching.", "strengths": ["Compassionate mastery", "Healing presence"], "challenges": ["Self-neglect", "Emotional burden"]},
    },
    "personality": {
        1: {"title": "Projects Leadership", "summary": "Others see you as confident, original, and decisive.", "strengths": ["Charisma", "Authority"], "challenges": ["Aloofness", "Dominance"]},
        2: {"title": "Projects Gentleness", "summary": "Others see you as diplomatic, kind, and approachable.", "strengths": ["Warmth", "Tact"], "challenges": ["Timidity", "Over-caution"]},
        3: {"title": "Projects Charm", "summary": "Others see you as creative, witty, and entertaining.", "strengths": ["Social grace", "Optimism"], "challenges": ["Gossip", "Inconsistency"]},
        4: {"title": "Projects Discipline", "summary": "Others see you as reliable, practical, and hardworking.", "strengths": ["Stability", "Trustworthiness"], "challenges": ["Dullness", "Rigidity"]},
        5: {"title": "Projects Magnetism", "summary": "Others see you as adventurous, dynamic, and exciting.", "strengths": ["Versatility", "Appeal"], "challenges": ["Recklessness", "Irresponsibility"]},
        6: {"title": "Projects Warmth", "summary": "Others see you as responsible, nurturing, and protective.", "strengths": ["Compassion", "Refinement"], "challenges": ["Interference", "Self-righteousness"]},
        7: {"title": "Projects Mystery", "summary": "Others see you as intellectual, refined, and reserved.", "strengths": ["Intellect", "Spirituality"], "challenges": ["Secretiveness", "Cynicism"]},
        8: {"title": "Projects Power", "summary": "Others see you as authoritative, successful, and commanding.", "strengths": ["Executive ability", "Confidence"], "challenges": ["Materialism", "Intimidation"]},
        9: {"title": "Projects Cosmopolitanism", "summary": "Others see you as worldly, generous, and idealistic.", "strengths": ["Tolerance", "Cultural depth"], "challenges": ["Detachment", "Moodiness"]},
        11: {"title": "Projects Spiritual Aura (Master)", "summary": "Others sense your spiritual intensity and inspirational presence.", "strengths": ["Radiance", "Visionary energy"], "challenges": ["Nervousness", "Impressionability"]},
        22: {"title": "Projects Masterful Authority (Master)", "summary": "Others see you as a powerful builder with unusual capability.", "strengths": ["Commanding presence", "Practical vision"], "challenges": ["Overbearing", "Pressure"]},
        33: {"title": "Projects Compassionate Mastery (Master)", "summary": "Others sense deep warmth, healing energy, and spiritual maturity.", "strengths": ["Grace", "Selfless love"], "challenges": ["Emotional burden", "Idealism"]},
    },
    "birthday": {
        1: {"title": "Leader", "summary": "A day-1 birthday gives natural leadership talent and pioneering spirit."},
        2: {"title": "Diplomat", "summary": "A day-2 birthday brings cooperation, patience, and sensitivity."},
        3: {"title": "Creative Communicator", "summary": "A day-3 birthday gifts artistic ability, social charm, and optimism."},
        4: {"title": "Builder", "summary": "A day-4 birthday provides discipline, practicality, and organizational skill."},
        5: {"title": "Adventurer", "summary": "A day-5 birthday brings versatility, curiosity, and love of freedom."},
        6: {"title": "Nurturer", "summary": "A day-6 birthday gifts responsibility, harmony, and artistic taste."},
        7: {"title": "Thinker", "summary": "A day-7 birthday provides analytical depth, spirituality, and wisdom."},
        8: {"title": "Achiever", "summary": "A day-8 birthday brings executive ability, ambition, and material success."},
        9: {"title": "Humanitarian", "summary": "A day-9 birthday gifts compassion, tolerance, and universal love."},
        10: {"title": "Independent Leader", "summary": "A day-10 birthday reduces to 1 — leadership with a need for independence."},
        11: {"title": "Illuminator (Master)", "summary": "An 11 birthday is a master number — spiritual illumination and inspiration."},
        12: {"title": "Creative Diplomat", "summary": "A day-12 reduces to 3 — creativity combined with cooperation."},
        13: {"title": "Transformative Builder", "summary": "A day-13 reduces to 4 — practical achievement through transformation."},
        14: {"title": "Dynamic Adventurer", "summary": "A day-14 reduces to 5 — freedom-loving with transformative power."},
        15: {"title": "Compassionate Nurturer", "summary": "A day-15 reduces to 6 — nurturing with artistic and humanitarian gifts."},
        16: {"title": "Spiritual Seeker", "summary": "A day-16 reduces to 7 — introspective, analytical, spiritually inclined."},
        17: {"title": "Ambitious Achiever", "summary": "A day-17 reduces to 8 — material success through hard work and faith."},
        18: {"title": "Compassionate Humanitarian", "summary": "A day-18 reduces to 9 — selfless service with artistic sensitivity."},
        19: {"title": "Independent Pioneer", "summary": "A day-19 reduces to 1 — leadership tempered by karmic lessons."},
        20: {"title": "Sensitive Diplomat", "summary": "A day-20 reduces to 2 — cooperation enhanced by intuition."},
        21: {"title": "Creative Communicator", "summary": "A day-21 reduces to 3 — artistic expression with karmic balance."},
        22: {"title": "Master Builder (Master)", "summary": "A 22 birthday is a master number — the ability to build lasting legacies."},
        23: {"title": "Adventurous Leader", "summary": "A day-23 reduces to 5 — freedom combined with communication gifts."},
        24: {"title": "Practical Creative", "summary": "A day-24 reduces to 6 — nurturing blended with artistic expression."},
        25: {"title": "Spiritual Communicator", "summary": "A day-25 reduces to 7 — analytical depth with creative gifts."},
        26: {"title": "Harmonious Achiever", "summary": "A day-26 reduces to 8 — material success through responsibility."},
        27: {"title": "Transformative Humanitarian", "summary": "A day-27 reduces to 9 — compassion with spiritual depth."},
        28: {"title": "Ambitious Diplomat", "summary": "A day-28 reduces to 10 → 1 — leadership through cooperation."},
        29: {"title": "Visionary Communicator", "summary": "A day-29 reduces to 11 (master) — inspirational communication gifts."},
        30: {"title": "Nurturing Leader", "summary": "A day-30 reduces to 3 — creative expression with responsibility."},
        31: {"title": "Independent Builder", "summary": "A day-31 reduces to 4 — pioneering spirit with practical discipline."},
    },
}


def get_interpretation(category: str, number: int) -> dict[str, str]:
    """Look up interpretation for a category and number.

    Falls back to the reduced number if exact match not found (e.g., 29 → 2).
    For master numbers, looks up exact key first, then reduced.
    """
    data = INTERPRETATIONS.get(category, {})
    if number in data:
        return data[number]

    # Fallback: reduce and look up again
    from .data_types import reduce_number as _reduce
    reduced = _reduce(number)
    if reduced in data:
        return data[reduced]

    return {
        "title": f"Number {number}",
        "summary": "Interpretation not available.",
        "strengths": [],
        "challenges": [],
    }


def format_interpretation(category: str, number: int, breakdown: str = "") -> str:
    """Format a human-readable interpretation paragraph."""
    interp = get_interpretation(category, number)
    title = interp.get("title", f"Number {number}")
    summary = interp.get("summary", "")

    parts = [f"**{title}** ({number}): {summary}"]
    if breakdown:
        parts.append(f"*Calculation:* {breakdown}")

    strengths = interp.get("strengths", [])
    challenges = interp.get("challenges", [])
    if strengths:
        parts.append(f"Strengths: {', '.join(strengths)}")
    if challenges:
        parts.append(f"Challenges: {', '.join(challenges)}")

    return "\n".join(parts)
