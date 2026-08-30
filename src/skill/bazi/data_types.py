"""Data types for the Ba Zi (Four Pillars of Destiny) skill."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


# ── Heavenly Stems (天干) ────────────────────────────────────────────────
STEMS = [
    # index: 0   1   2   3   4   5   6   7   8   9
    ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"),
]  # Chinese characters

STEMS_EN = [
    "Jia (Yang Wood)", "Yi (Yin Wood)", "Bing (Yang Fire)", "Ding (Yin Fire)",
    "Wu (Yang Earth)", "Ji (Yin Earth)", "Geng (Yang Metal)", "Xin (Yin Metal)",
    "Ren (Yang Water)", "Gui (Yin Water)",
]

STEMS_ELEMENT = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
STEMS_YIN_YANG = ["Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]

# Direct mapping for Chinese characters by index
STEM_CHAR = {
    0: "甲", 1: "乙", 2: "丙", 3: "丁", 4: "戊",
    5: "己", 6: "庚", 7: "辛", 8: "壬", 9: "癸",
}

# ── Earthly Branches (地支) ──────────────────────────────────────────────
BRANCHES = [
    # index: 0   1   2   3   4   5   6   7   8   9   10  11
    ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"),
]

BRANCHES_EN = [
    "Zi (Rat/Water)", "Chou (Ox/Earth)", "Yin (Tiger/Wood)", "Mao (Rabbit/Wood)",
    "Chen (Dragon/Earth)", "Si (Snake/Fire)", "Wu (Horse/Fire)", "Wei (Goat/Earth)",
    "Shen (Monkey/Metal)", "You (Rooster/Metal)", "Xu (Dog/Earth)", "Hai (Pig/Water)",
]

BRANCHES_ELEMENT = ["Water", "Earth", "Wood", "Wood", "Earth", "Fire", "Fire", "Earth", "Metal", "Metal", "Earth", "Water"]
BRANCHES_YIN_YANG = ["Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]

# Direct mapping for Chinese characters by index
BRANCH_CHAR = {
    0: "子", 1: "丑", 2: "寅", 3: "卯", 4: "辰", 5: "巳",
    6: "午", 7: "未", 8: "申", 9: "酉", 10: "戌", 11: "亥",
}

# Hidden stems (藏干) for each branch
HIDDEN_STEMS = {
    0: [9],       # 子 → 癸 (Gui, yin water)
    1: [5, 9, 7], # 丑 → 己, 癸, 辛 (Ji, Gui, Xin)
    2: [0, 2, 4], # 寅 → 甲, 丙, 戊 (Jia, Bing, Wu)
    3: [1],       # 卯 → 乙 (Yi, yin wood)
    4: [4, 1, 8], # 辰 → 戊, 乙, 壬 (Wu, Yi, Ren)
    5: [2, 6],    # 巳 → 丙, 庚 (Bing, Geng)
    6: [3, 5],    # 午 → 丁, 己 (Ding, Ji)
    7: [5, 3, 1], # 未 → 己, 丁, 乙 (Ji, Ding, Yi)
    8: [6, 8, 4], # 申 → 庚, 壬, 戊 (Geng, Ren, Wu)
    9: [7],       # 酉 → 辛 (Xin, yin metal)
    10: [4, 7, 3],# 戌 → 戊, 辛, 丁 (Wu, Xin, Ding)
    11: [8, 0],   # 亥 → 壬, 甲 (Ren, Jia)
}

# Month branches for solar terms (Ba Zi uses solar, not lunar months)
# Each branch corresponds to a 2-month period starting from 立春 (~Feb 4)
MONTH_BRANCHES = [11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
# Index: Jan=11(丑), Feb=0(子), Mar=1(寅)... but we need to handle solar terms

# Simplified month branch mapping (Gregorian month → Ba Zi month branch)
# This is an approximation; precise calculation requires exact solar term dates
MONTH_BRANCH_MAP = {
    1: 11,   # Jan → 丑 (Chou) — before 立春
    2: 0 if False else 2,  # Feb → depends on 立春 (~Feb 4)
    3: 3,    # Mar → 卯 (Mao) — after 惊蛰 (~Mar 5)
    4: 4,    # Apr → 辰 (Chen) — after 清明 (~Apr 4)
    5: 5,    # May → 巳 (Si) — after 立夏 (~May 5)
    6: 6,    # Jun → 午 (Wu) — after 芒种 (~Jun 5)
    7: 7,    # Jul → 未 (Wei) — after 小暑 (~Jul 6)
    8: 8,    # Aug → 申 (Shen) — after 立秋 (~Aug 7)
    9: 9,    # Sep → 酉 (You) — after 白露 (~Sep 7)
    10: 10,  # Oct → 戌 (Xu) — after 寒露 (~Oct 8)
    11: 11,  # Nov → 亥 (Hai) — after 立冬 (~Nov 7)
    12: 0,   # Dec → 子 (Zi) — after 大雪 (~Dec 7)
}

# Hour branch mapping (2-hour blocks)
HOUR_BRANCH_MAP = {
    23: 0, 0: 0,   # 子 (Rat): 23:00-01:59
    1: 1, 2: 1,    # 丑 (Ox): 01:00-02:59
    3: 2, 4: 2,    # 寅 (Tiger): 03:00-04:59
    5: 3, 6: 3,    # 卯 (Rabbit): 05:00-06:59
    7: 4, 8: 4,    # 辰 (Dragon): 07:00-08:59
    9: 5, 10: 5,   # 巳 (Snake): 09:00-10:59
    11: 6, 12: 6,  # 午 (Horse): 11:00-12:59
    13: 7, 14: 7,  # 未 (Goat): 13:00-14:59
    15: 8, 16: 8,  # 申 (Monkey): 15:00-16:59
    17: 9, 18: 9,  # 酉 (Rooster): 17:00-18:59
    19: 10, 20: 10,# 戌 (Dog): 19:00-20:59
    21: 11, 22: 11,# 亥 (Pig): 21:00-22:59
}


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass
class StemBranch:
    """A single stem-branch pair (e.g., 甲子)."""
    stem_index: int      # 0-9
    branch_index: int    # 0-11

    @property
    def chinese(self) -> str:
        return f"{STEMS[0][self.stem_index]}{BRANCHES[0][self.branch_index]}"

    @property
    def english(self) -> str:
        return f"{STEMS_EN[self.stem_index]} · {BRANCHES_EN[self.branch_index]}"

    @property
    def element(self) -> str:
        """Primary element (from stem)."""
        return STEMS_ELEMENT[self.stem_index]

    @property
    def yin_yang(self) -> str:
        return STEMS_YIN_YANG[self.stem_index]

    @property
    def hidden_stems_chinese(self) -> list[str]:
        """Get Chinese characters of hidden stems for this branch."""
        return [STEMS[0][s] for s in HIDDEN_STEMS.get(self.branch_index, [])]


@dataclass
class Pillar:
    """One of the four pillars (Year, Month, Day, Hour)."""
    label: str                    # "Year", "Month", "Day", "Hour"
    stem_branch: StemBranch
    hidden_stems: list[str] = ""  # Chinese characters of hidden stems


@dataclass
class BaziRecord:
    """Input data for Ba Zi computation."""
    name: str
    date_of_birth: date
    hour: int = -1              # -1 = unknown, 0-23 = known
    minute: int = 0
    gender: Optional[Gender] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.name.strip():
            errors.append("Name is required.")
        if self.date_of_birth > date.today():
            errors.append("Date of birth cannot be in the future.")
        return errors


@dataclass
class LuckPillar:
    """One of the 大运 (luck pillars) — a 10-year cycle."""
    stem_branch: StemBranch
    start_age: int              # Age when this luck pillar begins
    year_range: str             # e.g., "2035-2045"


@dataclass
class BaziResult:
    """Complete Ba Zi analysis."""
    name: str
    birth_date: date
    hour: int
    gender: Optional[Gender]
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar
    luck_pillars: list[LuckPillar] = field(default_factory=list)

    # Element counts (across all 8 characters + hidden stems)
    element_counts: dict[str, int] = field(default_factory=lambda: {
        "Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0
    })

    # Day master info
    day_master_element: str = ""
    day_master_yin_yang: str = ""
