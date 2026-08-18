"""
Astrowatch World Astrology -- shared sign-level dignity table.

These sign assignments (exaltation / debilitation ["fall" in Hellenistic terms] /
own-sign ["domicile" in Hellenistic terms]) are the SAME values already used and
validated elsewhere in this project (kundli_mass/analyze_midterms_2026.py,
kundli_mass/analyze_chart_archetypes.py) for the 7 classical planets shared by
Jyotisha and Hellenistic astrology. This module exists so world_astrology's new
code has one canonical place to pull them from, without either (a) re-deriving
them from scratch (risking a silent mismatch with the already-validated values)
or (b) importing from a kundli_mass/*.py analysis script, which are one-off
scripts, not a stable library surface. The OLD scripts are left untouched -- this
is new shared infrastructure for new code, not a refactor of already-committed,
already-delivered work.

IMPORTANT LIMITATION SHARED BY BOTH TRADITIONS' USE OF THIS TABLE: only sign-level
dignity is here (exaltation sign, "fall" sign, domicile sign(s)). Jyotisha's own
Moolatrikona and Hellenistic's triplicity/term/face are NOT in this table and are
NOT computed anywhere in this project -- see each tradition module's own
`limitations` text on its dignity-related KnowledgeEntry.
"""
from typing import Dict, Set

# Sidereal (Jyotisha rashi names) -- Hellenistic dignity re-uses these same signs
# since both systems assign the classical planets to the same 12 zodiacal signs at
# the sign level (only the ayanamsha/zodiac-frame differs, not the rulership scheme).
EXALTATION_SIGN: Dict[str, str] = {
    "sun": "Mesha", "moon": "Vrishabha", "mars": "Makara", "mercury": "Kanya",
    "jupiter": "Karka", "venus": "Meena", "saturn": "Tula",
}
DEBILITATION_SIGN: Dict[str, str] = {  # Jyotisha "neecha" / Hellenistic "fall"
    "sun": "Tula", "moon": "Vrischika", "mars": "Karka", "mercury": "Meena",
    "jupiter": "Makara", "venus": "Kanya", "saturn": "Mesha",
}
OWN_SIGNS: Dict[str, Set[str]] = {  # Jyotisha "swakshetra" / Hellenistic "domicile"
    "sun": {"Simha"}, "moon": {"Karka"}, "mars": {"Mesha", "Vrischika"},
    "mercury": {"Mithuna", "Kanya"}, "jupiter": {"Dhanu", "Meena"},
    "venus": {"Vrishabha", "Tula"}, "saturn": {"Makara", "Kumbha"},
}

RASHI_LORD = {  # sign ruler -- identical to kundli_mass/analyze_chart_archetypes.py's table
    "Mesha": "mars", "Vrishabha": "venus", "Mithuna": "mercury", "Karka": "moon",
    "Simha": "sun", "Kanya": "mercury", "Tula": "venus", "Vrischika": "mars",
    "Dhanu": "jupiter", "Makara": "saturn", "Kumbha": "saturn", "Meena": "jupiter",
}

JYOTISHA_BENEFICS = {"jupiter", "venus", "mercury", "moon"}
JYOTISHA_MALEFICS = {"sun", "mars", "saturn", "rahu", "ketu"}

HELLENISTIC_BENEFICS = {"jupiter", "venus"}
HELLENISTIC_MALEFICS = {"mars", "saturn"}
HELLENISTIC_LUMINARIES = {"sun", "moon"}
HELLENISTIC_DAY_SECT = {"sun", "jupiter", "saturn"}
HELLENISTIC_NIGHT_SECT = {"moon", "venus", "mars"}
# Mercury's sect adherence classically depends on its own solar phase (oriental vs.
# occidental of the Sun), which this project does not compute -- Mercury and the
# lunar nodes are treated as sect-neutral (not "of sect" or "contrary to sect") here,
# an explicit, documented simplification, not a claim of classical completeness.

KENDRA_HOUSES = {1, 4, 7, 10}
TRIKONA_HOUSES = {1, 5, 9}
DUSHTANA_HOUSES = {6, 8, 12}


def dignity_of(graha: str, rashi_name: str) -> str:
    """EXALTED / DEBILITATED / OWN_SIGN / NEUTRAL / N/A (nodes have no dignity
    per this table). Identical logic/values to the already-validated function of
    the same name in kundli_mass/analyze_midterms_2026.py."""
    if graha not in EXALTATION_SIGN:
        return "N/A"
    if rashi_name == EXALTATION_SIGN[graha]:
        return "EXALTED"
    if rashi_name == DEBILITATION_SIGN[graha]:
        return "DEBILITATED"
    if rashi_name in OWN_SIGNS[graha]:
        return "OWN_SIGN"
    return "NEUTRAL"


def house_of(rashi_idx: int, asc_idx: int) -> int:
    return ((rashi_idx - asc_idx) % 12) + 1


def house_kind(house_num: int) -> str:
    if house_num in KENDRA_HOUSES:
        return "kendra"
    if house_num in TRIKONA_HOUSES:
        return "trikona"
    if house_num in DUSHTANA_HOUSES:
        return "dushtana"
    return "other"


def jyotisha_score(graha: str, rashi_name: str, house_num: int):
    """Mirrors kundli_mass/analyze_midterms_2026.py's score_lord() convention
    exactly (same weights), factored out so world_astrology can reuse it without
    importing a one-off analysis script. Returns (score, dignity, house_kind)."""
    d = dignity_of(graha, rashi_name)
    kind = house_kind(house_num)
    dign_pts = {"EXALTED": 2, "OWN_SIGN": 1, "NEUTRAL": 0, "DEBILITATED": -2, "N/A": 0}[d]
    house_pts = {"kendra": 1, "trikona": 1, "dushtana": -1, "other": 0}[kind]
    nature_pts = 0.5 if graha in JYOTISHA_BENEFICS else -0.5
    return dign_pts + house_pts + nature_pts, d, kind


def hellenistic_sect_favor(is_day_chart: bool, graha: str):
    """True = of the chart's sect (favored), False = contrary to sect,
    None = not computed for this body (Mercury, Rahu, Ketu -- see module docstring)."""
    if graha in HELLENISTIC_DAY_SECT:
        return is_day_chart
    if graha in HELLENISTIC_NIGHT_SECT:
        return not is_day_chart
    return None


def hellenistic_score(graha: str, rashi_name: str, is_day_chart: bool):
    """Domicile/exaltation/fall dignity + sect-favor + benefic/malefic nature,
    scaled to be directly comparable to jyotisha_score's output range. Returns
    (score, dignity, of_sect) -- of_sect is None where not computed (see
    hellenistic_sect_favor)."""
    d = dignity_of(graha, rashi_name)
    dign_pts = {"EXALTED": 2, "OWN_SIGN": 1, "NEUTRAL": 0, "DEBILITATED": -2, "N/A": 0}[d]
    of_sect = hellenistic_sect_favor(is_day_chart, graha)
    sect_pts = 0.5 if of_sect is True else (-0.5 if of_sect is False else 0.0)
    if graha in HELLENISTIC_BENEFICS:
        nature_pts = 0.5
    elif graha in HELLENISTIC_MALEFICS:
        nature_pts = -0.5
    else:
        nature_pts = 0.0  # luminaries / mercury / nodes -- sect-neutral scheme here
    return dign_pts + sect_pts + nature_pts, d, of_sect
