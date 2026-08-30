"""Ba Zi (八字) / Four Pillars of Destiny computation engine.

All algorithms are deterministic and based on the Chinese sexagenary cycle.
No external dependencies — pure integer arithmetic on dates/times.

Key calculations:
- Year pillar: sexagenary cycle from year number
- Month pillar: solar term approximation + 五虎遁 (Five Tigers Run) method
- Day pillar: Julian Day Number → sexagenary day index
- Hour pillar: time-of-day + 五鼠遁 (Five Rats Run) method
- Luck pillars (大运): forward/backward cycles based on gender & stem polarity
"""

from __future__ import annotations

import math
from datetime import date, timedelta

from .data_types import (
    BRANCHES,
    BRANCHES_ELEMENT,
    BRANCHES_YIN_YANG,
    HIDDEN_STEMS,
    STEMS,
    STEMS_ELEMENT,
    STEMS_EN,
    STEMS_YIN_YANG,
    BaziRecord,
    BaziResult,
    Gender,
    LuckPillar,
    Pillar,
    StemBranch,
)


def jdn(gregorian_date: date) -> int:
    """Compute Julian Day Number for a Gregorian date.

    Standard algorithm from Jean Meeus, Astronomical Algorithms.
    """
    y = gregorian_date.year
    m = gregorian_date.month
    d = gregorian_date.day

    a = (14 - m) // 12
    jy = y + 4800 - a
    jm = m + 12 * a - 3
    jdn = d + (153 * jm + 2) // 5 + 365 * jy + jy // 4 - jy // 100 + jy // 400 - 32045
    return jdn


# Anchor: Jan 1, 4 CE was a 甲子 day (stem=0, branch=0)
_JDN_ANCHOR = jdn(date(4, 1, 1))  # = 1721424


def _sexagenary_index(jdn_value: int) -> tuple[int, int]:
    """Convert a JDN value to (stem_index, branch_index) in the 60-cycle.

    Stem cycles every 10, branch every 12. Combined cycle is 60.
    """
    idx = (jdn_value - _JDN_ANCHOR) % 60
    return idx % 10, idx % 12


def compute_year_pillar(year: int) -> StemBranch:
    """Compute the year pillar from the Gregorian year number.

    Uses the sexagenary cycle anchored at year 4 CE = 甲子.
    Note: In Ba Zi, the year changes at 立春 (~Feb 4), not Jan 1.
    For simplicity, we use the calendar year and note this limitation.
    """
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    return StemBranch(stem_index=stem_idx, branch_index=branch_idx)


def compute_month_pillar(year: int, month: int, day: int) -> StemBranch:
    """Compute the month pillar.

    Uses the 五虎遁 (Five Tigers Run) method to determine the month stem
    based on the year stem, and maps the Gregorian month to a branch.

    Month branches (simplified solar term approximation):
      Feb-Mar → 寅 (Tiger), Mar-Apr → 卯 (Rabbit), etc.
    """
    # Determine month branch from approximate solar terms
    # In precise Ba Zi, this requires exact solar term dates
    # Solar term boundaries (approximate):
    #   立春 ~Feb 4 → 寅月 starts
    #   惊蛰 ~Mar 5 → 卯月 starts
    #   清明 ~Apr 4 → 辰月 starts
    #   立夏 ~May 5 → 巳月 starts
    #   芒种 ~Jun 5 → 午月 starts
    #   小暑 ~Jul 6 → 未月 starts
    #   立秋 ~Aug 7 → 申月 starts
    #   白露 ~Sep 7 → 酉月 starts
    #   寒露 ~Oct 8 → 戌月 starts
    #   立冬 ~Nov 7 → 亥月 starts
    #   大雪 ~Dec 7 → 子月 starts
    month_branch_map = {
        1: 11,   # Jan → 丑 (Chou) — before 立春
        2: 11 if day < 4 else 2,  # Feb → 丑 or 寅 depending on 立春 (~Feb 4)
        3: 2 if day < 5 else 3,  # Mar → 寅 or 卯 depending on 惊蛰 (~Mar 5)
        4: 3 if day < 4 else 4,  # Apr → 卯 or 辰 depending on 清明 (~Apr 4)
        5: 4 if day < 5 else 5,  # May → 辰 or 巳 depending on 立夏 (~May 5)
        6: 5 if day < 5 else 6,  # Jun → 巳 or 午 depending on 芒种 (~Jun 5)
        7: 6 if day < 6 else 7,  # Jul → 午 or 未 depending on 小暑 (~Jul 6)
        8: 7 if day < 7 else 8,  # Aug → 未 or 申 depending on 立秋 (~Aug 7)
        9: 8 if day < 7 else 9,  # Sep → 申 or 酉 depending on 白露 (~Sep 7)
        10: 9 if day < 8 else 10,  # Oct → 酉 or 戌 depending on 寒露 (~Oct 8)
        11: 10 if day < 7 else 11,  # Nov → 戌 or 亥 depending on 立冬 (~Nov 7)
        12: 11 if day < 7 else 0,  # Dec → 亥 or 子 depending on 大雪 (~Dec 7)
    }

    branch_idx = month_branch_map.get(month, 2)

    # 五虎遁 (Five Tigers Run): determine month stem from year stem
    year_stem = (year - 4) % 10
    # Mapping: year stem → starting month stem for 寅月 (Tiger month)
    tiger_stem_map = {
        0: 2,  # 甲 or 己 years → 丙寅 (stem=2)
        1: 4,  # 乙 or 庚 years → 戊寅 (stem=4)
        2: 6,  # 丙 or 辛 years → 庚寅 (stem=6)
        3: 8,  # 丁 or 壬 years → 壬寅 (stem=8)
        4: 0,  # 戊 or 癸 years → 甲寅 (stem=0)
        5: 2,  # same as 0
        6: 4,  # same as 1
        7: 6,  # same as 2
        8: 8,  # same as 3
        9: 0,  # same as 4
    }

    start_stem = tiger_stem_map[year_stem]

    # Calculate month stem based on branch position relative to 寅 (branch=2)
    # 寅 is always the first month in Ba Zi (month 1 of the cycle)
    offset = (branch_idx - 2) % 12
    stem_idx = (start_stem + offset) % 10

    return StemBranch(stem_index=stem_idx, branch_index=branch_idx)


def compute_day_pillar(gregorian_date: date) -> StemBranch:
    """Compute the day pillar using Julian Day Number.

    JDN → sexagenary cycle index → (stem, branch) pair.
    This is the most precise pillar calculation.
    """
    jd = jdn(gregorian_date)
    stem_idx, branch_idx = _sexagenary_index(jd)
    return StemBranch(stem_index=stem_idx, branch_index=branch_idx)


def compute_hour_pillar(day_stem: int, hour: int) -> StemBranch:
    """Compute the hour pillar.

    Uses 五鼠遁 (Five Rats Run): the hour stem depends on the day stem.
    Hour branches are fixed by the 2-hour time block.
    """
    # Determine hour branch from 2-hour block
    # 子=0 (23-1), 丑=1 (1-3), 寅=2 (3-5), ..., 亥=11 (21-23)
    if hour == 23 or hour == 0:
        branch_idx = 0
    elif hour == 1 or hour == 2:
        branch_idx = 1
    elif hour == 3 or hour == 4:
        branch_idx = 2
    elif hour == 5 or hour == 6:
        branch_idx = 3
    elif hour == 7 or hour == 8:
        branch_idx = 4
    elif hour == 9 or hour == 10:
        branch_idx = 5
    elif hour == 11 or hour == 12:
        branch_idx = 6
    elif hour == 13 or hour == 14:
        branch_idx = 7
    elif hour == 15 or hour == 16:
        branch_idx = 8
    elif hour == 17 or hour == 18:
        branch_idx = 9
    elif hour == 19 or hour == 20:
        branch_idx = 10
    elif hour == 21 or hour == 22:
        branch_idx = 11
    else:
        branch_idx = 0  # default

    # 五鼠遁 (Five Rats Run): starting stem for 子时 (Rat hour)
    rat_stem_map = {
        0: 0,  # 甲 or 己 days → 甲子 (stem=0)
        1: 2,  # 乙 or 庚 days → 丙子 (stem=2)
        2: 4,  # 丙 or 辛 days → 戊子 (stem=4)
        3: 6,  # 丁 or 壬 days → 庚子 (stem=6)
        4: 8,  # 戊 or 癸 days → 壬子 (stem=8)
        5: 0,  # same as 0
        6: 2,  # same as 1
        7: 4,  # same as 2
        8: 6,  # same as 3
        9: 8,  # same as 4
    }

    start_stem = rat_stem_map[day_stem]

    # Hour stem offset from 子 (branch=0)
    offset = branch_idx
    stem_idx = (start_stem + offset) % 10

    return StemBranch(stem_index=stem_idx, branch_index=branch_idx)


def compute_luck_pillars(
    birth_date: date,
    year_stem: int,
    gender: Gender,
    start_age: int = 3,
) -> list[LuckPillar]:
    """Compute the 大运 (luck pillars) — 10-year cycles.

    Direction: forward if (yang male or yin female), backward if (yin male or yang female).
    Starting age: ~3-7 years depending on days to nearest solar term.
    Generates 8 luck pillars (80 years of life).
    """
    # Determine direction
    year_yang = STEMS_YIN_YANG[year_stem] == "Yang"
    is_male = gender == Gender.MALE

    forward = (year_yang and is_male) or (not year_yang and not is_male)

    # Count days to nearest major solar term
    # Simplified: use month boundary as approximation
    if birth_date.month <= 6:
        # Next solar term is around month 7 (立秋 ~Aug 7)
        next_term = date(birth_date.year, 8, 7) if birth_date.month < 8 else date(birth_date.year + 1, 8, 7)
        days_to_term = (next_term - birth_date).days
    else:
        # Next solar term is around month 1 (立春 ~Feb 4)
        next_term = date(birth_date.year, 2, 4) if birth_date.month > 2 else date(birth_date.year + 1, 2, 4)
        days_to_term = (next_term - birth_date).days

    # Each 3 days ≈ 1 year of luck pillar onset
    age_offset = max(3, days_to_term // 3)

    pillars: list[LuckPillar] = []
    current_stem = year_stem
    current_branch = (birth_date.month - 2) % 12  # offset from 寅月

    for i in range(8):  # 8 luck pillars = 80 years
        if forward:
            s_idx = (current_stem + i + 1) % 10
            b_idx = (current_branch + i + 1) % 12
        else:
            s_idx = (current_stem - i - 1) % 10
            b_idx = (current_branch - i - 1) % 12

        sb = StemBranch(stem_index=s_idx, branch_index=b_idx)
        start_age = age_offset + i * 10
        end_age = start_age + 9
        year_range = f"{birth_date.year + start_age}-{birth_date.year + end_age}"

        pillars.append(LuckPillar(
            stem_branch=sb,
            start_age=start_age,
            year_range=year_range,
        ))

    return pillars


def count_elements(pillar: Pillar) -> dict[str, int]:
    """Count elemental contributions from a pillar (stem + hidden stems)."""
    counts: dict[str, int] = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}

    # Stem element (primary)
    counts[STEMS_ELEMENT[pillar.stem_branch.stem_index]] += 1

    # Hidden stems from branch
    for hs_idx in HIDDEN_STEMS.get(pillar.stem_branch.branch_index, []):
        elem = STEMS_ELEMENT[hs_idx]
        counts[elem] += 0.5  # Hidden stems count as half

    return counts


def compute_all(record: BaziRecord) -> BaziResult:
    """Compute all four pillars and luck cycles from a birth record."""
    dob = record.date_of_birth
    hour = record.hour if record.hour >= 0 else 12  # default noon if unknown

    # Compute each pillar
    year_sb = compute_year_pillar(dob.year)
    month_sb = compute_month_pillar(dob.year, dob.month, dob.day)
    day_sb = compute_day_pillar(dob)
    hour_sb = compute_hour_pillar(day_sb.stem_index, hour)

    # Create pillar objects with hidden stems
    year_pillar = Pillar(
        label="Year (年)",
        stem_branch=year_sb,
        hidden_stems=", ".join(STEMS[0][s] for s in HIDDEN_STEMS.get(year_sb.branch_index, [])),
    )
    month_pillar = Pillar(
        label="Month (月)",
        stem_branch=month_sb,
        hidden_stems=", ".join(STEMS[0][s] for s in HIDDEN_STEMS.get(month_sb.branch_index, [])),
    )
    day_pillar = Pillar(
        label="Day (日) — Day Master",
        stem_branch=day_sb,
        hidden_stems=", ".join(STEMS[0][s] for s in HIDDEN_STEMS.get(day_sb.branch_index, [])),
    )
    hour_pillar = Pillar(
        label="Hour (时)",
        stem_branch=hour_sb,
        hidden_stems=", ".join(STEMS[0][s] for s in HIDDEN_STEMS.get(hour_sb.branch_index, [])),
    )

    # Count elements across all pillars
    element_counts = {"Wood": 0.0, "Fire": 0.0, "Earth": 0.0, "Metal": 0.0, "Water": 0.0}
    for pillar in [year_pillar, month_pillar, day_pillar, hour_pillar]:
        counts = count_elements(pillar)
        for elem, val in counts.items():
            element_counts[elem] += val

    # Day master info
    dm_element = STEMS_ELEMENT[day_sb.stem_index]
    dm_yinyang = STEMS_YIN_YANG[day_sb.stem_index]

    # Luck pillars (if gender provided)
    luck_pillars = []
    if record.gender:
        luck_pillars = compute_luck_pillars(
            dob, year_sb.stem_index, record.gender
        )

    return BaziResult(
        name=record.name,
        birth_date=dob,
        hour=hour,
        gender=record.gender,
        year_pillar=year_pillar,
        month_pillar=month_pillar,
        day_pillar=day_pillar,
        hour_pillar=hour_pillar,
        luck_pillars=luck_pillars,
        element_counts={k: round(v) for k, v in element_counts.items()},
        day_master_element=dm_element,
        day_master_yin_yang=dm_yinyang,
    )
