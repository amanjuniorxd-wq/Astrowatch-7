"""
Astrowatch World Astrology -- reading engine.

This is the one place in world_astrology that actually SYNTHESIZES a reading
across traditions, rather than just cataloguing knowledge (schema.py/traditions/)
or classifying how techniques relate in the abstract (cross_tradition.py). It
builds on the SAME machinery already validated elsewhere in this project --
kundli.compute_kundli, mundane.entity_chart (the universal entity-chart rule),
panchang.compute_partial_panchang -- nothing here recomputes an astronomical
position from scratch.

WHAT IS ACTUALLY CROSS-TRADITION HERE, HONESTLY STATED: of the 10 traditions
catalogued in traditions/*.py, only 4 have ANY computed=True content (jyotisha,
hellenistic, western, chinese -- see registry.build_registry().computed_
traditions()), and of those 4, only Jyotisha and Hellenistic share a comparable
VALENCE concept (planetary dignity strong/weak) that can be numerically compared
via dignity_tables.py. Western's computed content is tropical sign placement only
(no valence system implemented for it in this project); Chinese's is the
sexagenary year cycle (a categorical fact, not a valence). So the "singular
pattern combining fields of knowledge" this engine produces is, precisely:

  - A real, computed Jyotisha-vs-Hellenistic agreement classification on the
    chart's currently ruling Mahadasha/Antardasha lord (Strong / Moderate /
    Tradition-specific / Contradictory / Insufficient -- see classify_agreement).
  - Real, computed, but DESCRIPTIVE-ONLY context from Western (tropical sign)
    and Chinese (sexagenary year) astrology, explicitly not folded into the
    agreement score, because this project has no validated way to assign them
    a comparable valence.
  - Explicit callouts of which other traditions (Babylonian, Persian/Islamic,
    Tibetan, Egyptian, Japanese, Mesoamerican) are catalogued as knowledge but
    NOT part of the computed synthesis at all, and why.

This is a narrower, more honest claim than "all 10 traditions agree/disagree,"
and that narrowness is deliberate -- see world_astrology/__init__.py.
"""
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone as dt_timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ASTROWATCH_DIR not in sys.path:
    sys.path.insert(0, ASTROWATCH_DIR)

import coordinates
from mundane.entity_chart import (
    compute_entity_chart, full_lifetime_dasha, EntityChart,
    TIME_SOURCE_ASSUMED_MIDNIGHT,
)
from mundane.dasha_timeline import jd_to_iso_date
from panchang import compute_partial_panchang, PanchangPartial

from . import dignity_tables as dt
from .traditions import chinese as chinese_mod
from .registry import build_registry
from . import cross_tradition as ct

WESTERN_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                  "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]


def western_tropical_sign(tropical_lon_deg: float) -> str:
    idx = int((tropical_lon_deg % 360.0) // 30.0)
    return WESTERN_SIGNS[idx]


def _today_utc_jd() -> float:
    now = datetime.now(dt_timezone.utc)
    return coordinates.julian_day(now.year, now.month, now.day,
                                   now.hour + now.minute / 60.0 + now.second / 3600.0)


@dataclass
class DashaPeriodFinding:
    mahadasha_lord: str
    mahadasha_start: str
    mahadasha_end: str
    antardasha_lord: str
    antardasha_start: str
    antardasha_end: str


@dataclass
class AgreementFinding:
    classification: str    # Strong | Moderate | Tradition-specific | Contradictory | Insufficient
    reasoning: str
    jyotisha_score: Optional[float]
    jyotisha_dignity: Optional[str]
    hellenistic_score: Optional[float]
    hellenistic_dignity: Optional[str]


@dataclass
class ChartBundle:
    entity: EntityChart
    as_of_jd: float
    as_of_date: str
    is_day_chart: bool
    dasha: DashaPeriodFinding
    agreement: AgreementFinding
    natal_panchang: PanchangPartial
    western_signs: Dict[str, str]           # graha -> tropical sign name
    chinese_birth_year: tuple               # (stem, branch, animal) for inception year
    chinese_as_of_year: tuple               # (stem, branch, animal) for as_of year


def _find_ruling_period(entity: EntityChart, as_of_jd: float, max_cycles) -> tuple:
    as_of_date = jd_to_iso_date(as_of_jd)
    end_jd = as_of_jd + 1.0  # small buffer past as_of so the walker's boundary covers it
    periods = full_lifetime_dasha(entity, end_jd, max_cycles=max_cycles)
    for p in periods:
        maha_i, ml, ms, me, ant_i, al, a_s, ae = p
        if jd_to_iso_date(a_s) <= as_of_date < jd_to_iso_date(ae):
            return ml, ms, me, al, a_s, ae
    raise RuntimeError(
        f"no Dasha period found covering {as_of_date} for {entity.entity_name} -- "
        f"as_of date may be outside this walker's computed range."
    )


def classify_agreement(jy_score: float, jy_dignity: str,
                        he_score: Optional[float], he_dignity: Optional[str]) -> AgreementFinding:
    if he_score is None:
        return AgreementFinding(
            classification="Tradition-specific",
            reasoning="Hellenistic dignity/sect scoring does not apply to this graha "
                "(a lunar node) in this project's classical-7-planet Hellenistic "
                "implementation -- Rahu/Ketu have no Hellenistic sect or essential-"
                "dignity equivalent computed here, so only Jyotisha's finding is usable.",
            jyotisha_score=jy_score, jyotisha_dignity=jy_dignity,
            hellenistic_score=None, hellenistic_dignity=None,
        )
    jy_sign = 1 if jy_score > 0 else (-1 if jy_score < 0 else 0)
    he_sign = 1 if he_score > 0 else (-1 if he_score < 0 else 0)
    if jy_sign == 0 or he_sign == 0:
        return AgreementFinding(
            classification="Insufficient",
            reasoning=f"One or both combined scores are exactly neutral "
                f"(Jyotisha={jy_score:+.1f}, Hellenistic={he_score:+.1f}) -- not enough "
                f"signal in either direction to call agreement or contradiction.",
            jyotisha_score=jy_score, jyotisha_dignity=jy_dignity,
            hellenistic_score=he_score, hellenistic_dignity=he_dignity,
        )
    if jy_sign != he_sign:
        return AgreementFinding(
            classification="Contradictory",
            reasoning=f"Jyotisha's combined score ({jy_score:+.1f}, weighting sign "
                f"dignity + house placement + Jyotisha benefic/malefic nature) is "
                f"{'positive' if jy_sign > 0 else 'negative'}, while Hellenistic's "
                f"combined score ({he_score:+.1f}, weighting the same sign dignity + "
                f"sect-favor + Hellenistic benefic/malefic nature) is "
                f"{'positive' if he_sign > 0 else 'negative'} -- the two traditions' "
                f"secondary weighting factors (house vs. sect) point opposite ways "
                f"even though the raw sign-level dignity below is shared.",
            jyotisha_score=jy_score, jyotisha_dignity=jy_dignity,
            hellenistic_score=he_score, hellenistic_dignity=he_dignity,
        )
    gap = abs(jy_score - he_score)
    if gap <= 1.0:
        classification = "Strong"
        strength_note = "closely aligned in both direction and magnitude"
    else:
        classification = "Moderate"
        strength_note = "aligned in direction but diverging in magnitude"
    return AgreementFinding(
        classification=classification,
        reasoning=f"Both traditions assign this planet the SAME sign-level dignity "
            f"({jy_dignity}, from the shared dignity_tables.py sign data -- see that "
            f"module's docstring) and their combined scores are {strength_note} "
            f"(Jyotisha {jy_score:+.1f} vs. Hellenistic {he_score:+.1f}). They diverge "
            f"only in HOW they weight the same base dignity: Jyotisha adds house "
            f"placement (kendra/trikona/dushtana), Hellenistic adds sect-favor "
            f"(day/night chart). That divergence in secondary weighting is exactly "
            f"why this is {classification.upper()} agreement rather than a claim of "
            f"identical technique.",
        jyotisha_score=jy_score, jyotisha_dignity=jy_dignity,
        hellenistic_score=he_score, hellenistic_dignity=he_dignity,
    )


def build_chart_bundle(
    entity_name: str, entity_type: str, inception_date: str,
    latitude: float, longitude: float, timezone_name: str,
    inception_time: Optional[str] = None, as_of_date: Optional[str] = None,
) -> ChartBundle:
    """Core computation shared by all three reading modes. entity_type follows
    the mundane-astrology rule's convention (see mundane/entity_chart.py) --
    "person" caps the Dasha walk at 1 cycle (matches this project's existing
    person-corpus convention); anything else walks unlimited cycles (nations/
    organizations can outlive a single 120-year Vimshottari cycle)."""
    entity = compute_entity_chart(entity_name, entity_type, inception_date,
                                   latitude, longitude, timezone_name, inception_time)
    if as_of_date:
        y, m, d = (int(x) for x in as_of_date.split("-"))
        as_of_jd = coordinates.julian_day(y, m, d, 12.0)  # noon UTC, date-level granularity only
    else:
        as_of_jd = _today_utc_jd()

    max_cycles = 1 if entity_type == "person" else None
    ml, ms, me, al, a_s, ae = _find_ruling_period(entity, as_of_jd, max_cycles)
    dasha_finding = DashaPeriodFinding(
        mahadasha_lord=ml, mahadasha_start=jd_to_iso_date(ms), mahadasha_end=jd_to_iso_date(me),
        antardasha_lord=al, antardasha_start=jd_to_iso_date(a_s), antardasha_end=jd_to_iso_date(ae),
    )

    chart = entity.chart
    asc_idx = chart.ascendant_rashi.rashi_index
    sun_house = chart.grahas["sun"].house
    is_day_chart = sun_house in range(7, 13)

    al_placement = chart.grahas.get(al)
    if al_placement is not None:
        rashi_name = al_placement.rashi.rashi_name
        house_num = al_placement.house
        jy_score, jy_dignity, _kind = dt.jyotisha_score(al, rashi_name, house_num)
        if al in dt.EXALTATION_SIGN:  # only the 7 classical planets have a Hellenistic entry
            he_score, he_dignity, _of_sect = dt.hellenistic_score(al, rashi_name, is_day_chart)
        else:
            he_score, he_dignity = None, None
        agreement = classify_agreement(jy_score, jy_dignity, he_score, he_dignity)
    else:
        agreement = AgreementFinding("Insufficient", "Antardasha lord graha data unavailable.",
                                      None, None, None, None)

    natal_panchang = compute_partial_panchang(
        entity.jd_ut, chart.grahas["sun"].tropical_lon_deg,
        chart.grahas["moon"].tropical_lon_deg, chart.grahas["moon"].sidereal_lon_deg,
    )

    western_signs = {name: western_tropical_sign(g.tropical_lon_deg)
                      for name, g in chart.grahas.items()}

    inception_year = int(inception_date.split("-")[0])
    as_of_year = int(jd_to_iso_date(as_of_jd).split("-")[0])

    return ChartBundle(
        entity=entity, as_of_jd=as_of_jd, as_of_date=jd_to_iso_date(as_of_jd),
        is_day_chart=is_day_chart, dasha=dasha_finding, agreement=agreement,
        natal_panchang=natal_panchang, western_signs=western_signs,
        chinese_birth_year=chinese_mod.stem_branch_animal_for_year(inception_year),
        chinese_as_of_year=chinese_mod.stem_branch_animal_for_year(as_of_year),
    )


# ---------------------------------------------------------------------------
# Reading modes
# ---------------------------------------------------------------------------

def generate_short_reading(entity_name: str, entity_type: str, inception_date: str,
                            latitude: float, longitude: float, timezone_name: str,
                            inception_time: Optional[str] = None,
                            as_of_date: Optional[str] = None,
                            max_sentences: int = 5) -> str:
    """A configurable-length short reading. Sentences are pre-ranked by
    importance and the list is truncated to max_sentences -- callers asking
    for fewer sentences always get the highest-priority findings, not an
    arbitrary subset."""
    b = build_chart_bundle(entity_name, entity_type, inception_date, latitude,
                            longitude, timezone_name, inception_time, as_of_date)
    chart = b.entity.chart
    moon = chart.grahas["moon"]
    time_caveat = (" (inception time ASSUMED at midnight -- Ascendant/house findings "
                    "below are not reliable; see limitations)"
                   if b.entity.time_source == TIME_SOURCE_ASSUMED_MIDNIGHT else "")

    sentences = [
        f"{entity_name}'s Ascendant is {chart.ascendant_rashi.rashi_name}, with Moon in "
        f"{moon.rashi.rashi_name} ({moon.nakshatra.nakshatra_name} Nakshatra){time_caveat}.",

        f"As of {b.as_of_date}, the ruling Vimshottari period is {b.dasha.mahadasha_lord.title()} "
        f"Mahadasha ({b.dasha.mahadasha_start} to {b.dasha.mahadasha_end}) with "
        f"{b.dasha.antardasha_lord.title()} Antardasha (through {b.dasha.antardasha_end}).",

        (f"Jyotisha reads {b.dasha.antardasha_lord.title()} as {b.agreement.jyotisha_dignity} "
         f"in this chart (combined strength score {b.agreement.jyotisha_score:+.1f})."
         if b.agreement.jyotisha_score is not None else
         "Jyotisha dignity data for the current Antardasha lord was not available."),

        (f"Hellenistic astrology, applying the same sign-level dignity data to a "
         f"{'day' if b.is_day_chart else 'night'} chart, scores {b.dasha.antardasha_lord.title()} "
         f"at {b.agreement.hellenistic_score:+.1f} ({b.agreement.hellenistic_dignity})."
         if b.agreement.hellenistic_score is not None else
         f"Hellenistic scoring does not apply to {b.dasha.antardasha_lord.title()} in this "
         f"project's implementation ({b.agreement.reasoning})"),

        f"Cross-tradition agreement on this period's dominant planetary influence: "
        f"{b.agreement.classification.upper()} -- {b.agreement.reasoning}",

        f"For descriptive context (not folded into the score above): the tropical "
        f"(Western) Sun sign is {b.western_signs['sun']}, and the {b.as_of_date[:4]} "
        f"Chinese sexagenary year is {b.chinese_as_of_year[0]}-{b.chinese_as_of_year[1]} "
        f"({b.chinese_as_of_year[2]}).",
    ]
    return " ".join(sentences[:max_sentences])


DETAILED_READING_SECTIONS = [
    "1. Identification & Data Provenance",
    "2. Jyotisha Core Chart (Ascendant, Grahas, Bhavas)",
    "3. Moon, Nakshatra & Birth Panchang",
    "4. Jyotisha Planetary Dignity Summary",
    "5. Current Mahadasha / Antardasha Timeline Context",
    "6. Hellenistic Sect Classification",
    "7. Hellenistic Essential Dignity Summary",
    "8. Cross-Tradition Agreement: Jyotisha vs. Hellenistic",
    "9. Western Tropical Placements (Descriptive)",
    "10. Chinese Sexagenary Year Context (Birth Year & Current Year)",
    "11. Traditions Catalogued But Not Computed For This Reading",
    "12. Evidence-Level Summary of Techniques Used",
    "13. Known Limitations of This Specific Reading",
    "14. Historical Validation Status",
    "15. Synthesized Single Prediction",
]


def generate_detailed_reading(entity_name: str, entity_type: str, inception_date: str,
                               latitude: float, longitude: float, timezone_name: str,
                               inception_time: Optional[str] = None,
                               as_of_date: Optional[str] = None) -> str:
    """15-section detailed reading. Every section is either real computed
    content (labeled with which module/function produced it) or an explicit
    'not computed' statement -- no section is filled with invented prose."""
    b = build_chart_bundle(entity_name, entity_type, inception_date, latitude,
                            longitude, timezone_name, inception_time, as_of_date)
    e = b.entity
    chart = e.chart
    reg = build_registry()
    lines: List[str] = []

    def sec(title):
        lines.append(f"\n== {title} ==")

    sec(DETAILED_READING_SECTIONS[0])
    lines.append(f"Entity: {entity_name} ({entity_type})")
    lines.append(f"Inception: {e.inception_date} {e.inception_time} {e.timezone_name} "
                 f"[{e.time_source}]")
    lines.append(f"Location: {e.latitude:.4f}, {e.longitude:.4f}")
    lines.append(f"Reading generated for as-of date: {b.as_of_date}")
    lines.append(f"Ayanamsha: {chart.ayanamsha_source} ({chart.ayanamsha_deg:.4f} deg)")
    lines.append(f"Engine: {chart.engine}, node convention: {chart.node_convention}, "
                 f"house system: {chart.house_system}")
    if e.time_source == TIME_SOURCE_ASSUMED_MIDNIGHT:
        lines.append("CAVEAT: inception time was ASSUMED at 00:00 local civil time (no "
                     "documented time available) -- Ascendant and all house-based "
                     "findings in this reading are NOT reliable. Moon Rashi/Nakshatra, "
                     "the Mahadasha/Antardasha lord sequence, and non-Moon sign "
                     "placements remain reasonably meaningful (low sensitivity to a "
                     "few hours' time error). See MUNDANE_ASTROLOGY_RULE.md.")

    sec(DETAILED_READING_SECTIONS[1])
    lines.append(f"Ascendant: {chart.ascendant_rashi.rashi_name} "
                 f"({chart.ascendant_sidereal_deg:.2f} deg sidereal)")
    for name in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]:
        g = chart.grahas[name]
        retro = " (Rx)" if g.retrograde else ""
        lines.append(f"  {name.title():8s}: {g.rashi.rashi_name:12s} house {g.house:2d}  "
                     f"{g.sidereal_lon_deg:7.2f} deg sidereal{retro}")

    sec(DETAILED_READING_SECTIONS[2])
    moon = chart.grahas["moon"]
    p = b.natal_panchang
    lines.append(f"Moon: {moon.rashi.rashi_name}, {moon.nakshatra.nakshatra_name} Nakshatra")
    lines.append(f"Tithi: {p.tithi_name} ({p.paksha} paksha, #{p.tithi_number})")
    lines.append(f"Vara: {p.vara_name}")
    lines.append("Yoga/Karana: NOT COMPUTED (panchang.py explicitly returns None -- see "
                 "that module's docstring; not guessed at).")

    sec(DETAILED_READING_SECTIONS[3])
    for name in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        g = chart.grahas[name]
        d = dt.dignity_of(name, g.rashi.rashi_name)
        lines.append(f"  {name.title():8s}: {d}")
    lines.append("(Rahu/Ketu: N/A -- this dignity table covers the 7 classical planets only.)")

    sec(DETAILED_READING_SECTIONS[4])
    lines.append(f"Mahadasha: {b.dasha.mahadasha_lord.title()} "
                 f"[{b.dasha.mahadasha_start} -> {b.dasha.mahadasha_end}]")
    lines.append(f"Antardasha: {b.dasha.antardasha_lord.title()} "
                 f"[{b.dasha.antardasha_start} -> {b.dasha.antardasha_end}]")
    lines.append(f"(As of {b.as_of_date}; walked via mundane.entity_chart.full_lifetime_dasha, "
                 f"max_cycles={'1 (person convention)' if entity_type == 'person' else 'unlimited'}.)")

    sec(DETAILED_READING_SECTIONS[5])
    lines.append(f"Chart sect: {'DAY' if b.is_day_chart else 'NIGHT'} chart "
                 f"(Sun in house {chart.grahas['sun'].house}, "
                 f"{'above' if b.is_day_chart else 'below'} the horizon per whole-sign "
                 f"houses 7-12 = above).")

    sec(DETAILED_READING_SECTIONS[6])
    for name in ["sun", "moon", "mars", "jupiter", "venus", "saturn"]:
        g = chart.grahas[name]
        d = dt.dignity_of(name, g.rashi.rashi_name)
        of_sect = dt.hellenistic_sect_favor(b.is_day_chart, name)
        sect_str = "N/A (sect-neutral in this implementation)" if of_sect is None else \
                   ("of sect" if of_sect else "contrary to sect")
        lines.append(f"  {name.title():8s}: dignity={d:12s} sect={sect_str}")
    lines.append("(Mercury: sect-neutral here -- classical Mercury sect depends on solar "
                 "phase, not computed. Triplicity/term/face: NOT COMPUTED.)")

    sec(DETAILED_READING_SECTIONS[7])
    a = b.agreement
    lines.append(f"Classification: {a.classification}")
    lines.append(f"Reasoning: {a.reasoning}")

    sec(DETAILED_READING_SECTIONS[8])
    for name in ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]:
        lines.append(f"  {name.title():8s}: {b.western_signs[name]} (tropical)")
    lines.append("(House system, aspects/orbs, and outer planets: NOT COMPUTED for Western "
                 "-- see western.py's 'Modern tropical natal astrology' entry limitations.)")

    sec(DETAILED_READING_SECTIONS[9])
    bs, bb, ba = b.chinese_birth_year
    cs, cb, ca = b.chinese_as_of_year
    lines.append(f"Inception year ({inception_date[:4]}): {bs}-{bb} ({ba})")
    lines.append(f"As-of year ({b.as_of_date[:4]}): {cs}-{cb} ({ca})")
    lines.append("(Reference-only -- see chinese.py's sexagenary_year_index() docstring for "
                 "the year-boundary approximation this uses.)")

    sec(DETAILED_READING_SECTIONS[10])
    seed_traditions = [t for t in reg.traditions() if t not in reg.computed_traditions()]
    lines.append(f"Catalogued but not computed for this reading: {', '.join(seed_traditions)}. "
                 f"These traditions have KnowledgeEntry records in this system (see "
                 f"world_astrology/traditions/) documenting their real techniques, "
                 f"historical context, and sourcing, but no calculation engine for any of "
                 f"them has been built and independently verified in this project.")

    sec(DETAILED_READING_SECTIONS[11])
    used_ids = ["jyotisha:rashi", "jyotisha:nakshatra", "jyotisha:graha", "jyotisha:bhava",
                "jyotisha:mahadasha_/_antardasha", "jyotisha:tithi", "jyotisha:vara",
                "jyotisha:uchcha_/_neecha_/_swakshetra_(exaltation/debilitation/own-sign)",
                "hellenistic:sect", "hellenistic:essential_dignity",
                "western:modern_tropical_natal_astrology", "chinese:ganzhi_(stems_and_branches)"]
    for eid in used_ids:
        entry = reg.get(eid)
        if entry:
            lines.append(f"  {eid}: {entry.confidence_level.value}")

    sec(DETAILED_READING_SECTIONS[12])
    lines.append("Ascendant/house findings unreliable if inception time was assumed "
                 "(see Section 1). Hellenistic scoring covers domicile/exaltation/fall + "
                 "sect only (no triplicity/term/face). Western scoring covers tropical "
                 "sign only (no houses/aspects/outer planets). Chinese year boundary is a "
                 "Jan-1-anchored approximation, not the true lunisolar new year. Yoga/"
                 "Karana panchang limbs not computed.")

    sec(DETAILED_READING_SECTIONS[13])
    lines.append("NOT YET RUN for this entity -- see world_astrology/historical_validation.py "
                 "for the storage schema. No backtested accuracy claim is made for any "
                 "finding in this reading.")

    sec(DETAILED_READING_SECTIONS[14])
    lines.append(f"SYNTHESIZED FINDING: The dominant astrological signal for {entity_name} "
                 f"as of {b.as_of_date} is the {b.dasha.antardasha_lord.title()} Antardasha "
                 f"(within {b.dasha.mahadasha_lord.title()} Mahadasha), independently "
                 f"assessed by Jyotisha ({a.jyotisha_dignity}, score {a.jyotisha_score:+.1f}) "
                 if a.jyotisha_score is not None else
                 f"SYNTHESIZED FINDING: insufficient computed data for a single-sentence "
                 f"synthesis for {entity_name}.")
    if a.jyotisha_score is not None:
        if a.hellenistic_score is not None:
            lines[-1] += (f"and Hellenistic astrology ({a.hellenistic_dignity}, score "
                          f"{a.hellenistic_score:+.1f}), with {a.classification.upper()} "
                          f"cross-tradition agreement on the direction of this influence "
                          f"({'favorable' if a.jyotisha_score > 0 else 'unfavorable' if a.jyotisha_score < 0 else 'neutral'}).")
        else:
            lines[-1] += f"only ({a.reasoning})."

    return "\n".join(lines)


def generate_world_reading(entity_name: str, inception_date: str,
                            latitude: float, longitude: float, timezone_name: str,
                            entity_type: str = "nation",
                            inception_time: Optional[str] = None,
                            as_of_date: Optional[str] = None) -> str:
    """Mundane/world reading mode -- same underlying computation as the other
    two modes (via build_chart_bundle), framed for a collective entity (nation,
    organization, market, etc.) per the project's mundane-astrology rule. Always
    walks unlimited Dasha cycles (entity_type defaults away from 'person'), and
    surfaces the ASSUMED_MIDNIGHT caveat prominently at the top when it applies,
    since it matters even more for house-based mundane claims than for individuals."""
    b = build_chart_bundle(entity_name, entity_type, inception_date, latitude, longitude,
                            timezone_name, inception_time, as_of_date)
    e = b.entity
    a = b.agreement
    lines = [f"WORLD/MUNDANE READING: {entity_name} ({entity_type})", ""]
    if e.time_source == TIME_SOURCE_ASSUMED_MIDNIGHT:
        lines.append(f"[Inception time assumed at 00:00 local civil time -- per the "
                     f"mundane-astrology rule (MUNDANE_ASTROLOGY_RULE.md), the Ascendant "
                     f"and house placements below are NOT reliable for {entity_name}. "
                     f"Moon Rashi/Nakshatra and the Mahadasha/Antardasha sequence remain "
                     f"reasonably meaningful.]")
        lines.append("")
    lines.append(f"Founding chart: Ascendant {e.chart.ascendant_rashi.rashi_name}, Moon "
                 f"{e.chart.grahas['moon'].rashi.rashi_name} "
                 f"({e.chart.grahas['moon'].nakshatra.nakshatra_name}).")
    lines.append(f"Ruling as of {b.as_of_date}: {b.dasha.mahadasha_lord.title()} Mahadasha "
                 f"[{b.dasha.mahadasha_start}-{b.dasha.mahadasha_end}] / "
                 f"{b.dasha.antardasha_lord.title()} Antardasha "
                 f"[{b.dasha.antardasha_start}-{b.dasha.antardasha_end}].")
    lines.append(f"Jyotisha dignity of ruling Antardasha lord: {a.jyotisha_dignity} "
                 f"(score {a.jyotisha_score:+.1f})." if a.jyotisha_score is not None else
                 "Jyotisha dignity: not available for this lord.")
    if a.hellenistic_score is not None:
        lines.append(f"Hellenistic reading of the same lord in this "
                     f"{'day' if b.is_day_chart else 'night'} chart: {a.hellenistic_dignity} "
                     f"(score {a.hellenistic_score:+.1f}).")
    lines.append(f"Cross-tradition agreement: {a.classification} -- {a.reasoning}")
    lines.append("")
    lines.append("Mundane-astrology context (catalogued, not independently computed by this "
                 "reading): Hellenistic mundane astrology (hellenistic:hellenistic_mundane_"
                 "astrology) and Jyotisha Samhita literature (jyotisha:samhita_literature) "
                 "both have real, historically-attested traditions of collective/political "
                 "astrology this system documents but does not run its own rule set for "
                 "beyond the dignity/timing computation above -- see this project's separate, "
                 "already-delivered nations Mahadasha-pattern analysis "
                 "(kundli_mass/NATIONS_MAHADASHA_PATTERN_REPORT.md) for a base-rate-"
                 "normalized empirical pattern study, which is a DIFFERENT, complementary "
                 "body of work from this knowledge-system reading.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full-horoscope long-text narrative (distinct from the 15-section technical
# detailed reading above: this is flowing prose meant to read like an actual
# horoscope write-up, not a labeled technical report).
# ---------------------------------------------------------------------------

def _valence_word(score: Optional[float]) -> str:
    if score is None:
        return "unclear"
    if score >= 1.5:
        return "strongly favorable"
    if score > 0:
        return "mildly favorable"
    if score == 0:
        return "neutral"
    if score > -1.5:
        return "mildly challenging"
    return "strongly challenging"


def generate_full_horoscope_narrative(
    entity_name: str, entity_type: str, inception_date: str,
    latitude: float, longitude: float, timezone_name: str,
    inception_time: Optional[str] = None, as_of_date: Optional[str] = None,
    field: Optional[str] = None, corpus_context: Optional[str] = None,
) -> str:
    """Long-form prose reading combining every field this system has computed
    data for. Distinct from generate_detailed_reading (which is a labeled,
    section-by-section technical report) -- this is meant to be read start to
    finish as a single piece of writing, the way a person reads an actual
    horoscope, while still being precise about what is and isn't computed.

    `field` (optional, e.g. "ACTOR", "SCIENTIST" -- see kundli_mass corpus
    field categories) and `corpus_context` (optional pre-formatted sentence
    describing how this entity's field compares to the corpus-wide pattern,
    produced by kundli_mass/analyze_multi_tradition_archetypes.py) let a
    caller fold in the corpus-wide statistical pattern from task work on the
    1305-person corpus, without this module needing to know how that pattern
    was computed."""
    b = build_chart_bundle(entity_name, entity_type, inception_date, latitude,
                            longitude, timezone_name, inception_time, as_of_date)
    chart = b.entity.chart
    moon = chart.grahas["moon"]
    asc_rashi = chart.ascendant_rashi.rashi_name
    a = b.agreement

    from . import dignity_tables as dt
    from .chart_visuals import RASHI_NAMES_ORDER
    tenth_sign_index = (chart.ascendant_rashi.rashi_index + 9) % 12
    tenth_sign_name = RASHI_NAMES_ORDER[tenth_sign_index]
    tenth_lord = dt.RASHI_LORD[tenth_sign_name]
    tenth_lord_placement = chart.grahas.get(tenth_lord)
    tenth_lord_dignity = (dt.dignity_of(tenth_lord, tenth_lord_placement.rashi.rashi_name)
                           if tenth_lord_placement else "N/A")

    paras = []

    time_note = ("(the exact hour of birth wasn't available, so this reading assumes local "
                 "midnight per this project's standing mundane-astrology convention -- the "
                 "Ascendant and 10th-house reading below should be treated with real caution)"
                 if b.entity.time_source == TIME_SOURCE_ASSUMED_MIDNIGHT else
                 "(using a specifically documented birth time)")
    paras.append(
        f"{entity_name}'s chart rises in {asc_rashi} {time_note}, with the Moon placed in "
        f"{moon.rashi.rashi_name} under the {moon.nakshatra.nakshatra_name} Nakshatra -- in "
        f"Jyotisha terms, this Moon placement is usually read as the seat of the mind and "
        f"emotional temperament more than the Ascendant is, and is comparatively less sensitive "
        f"to an uncertain birth time than the Ascendant is."
    )

    paras.append(
        f"Looking at career and public life through the 10th house from the Ascendant "
        f"({tenth_sign_name}, ruled by {tenth_lord.title()}): {tenth_lord.title()} is placed "
        f"in {tenth_lord_placement.rashi.rashi_name if tenth_lord_placement else 'an unresolved sign'}, "
        f"which Jyotisha's sign-level dignity table calls {tenth_lord_dignity.lower().replace('_',' ')}. "
        + ("This is traditionally read as a strong indicator for visible, well-regarded career "
           "achievement." if tenth_lord_dignity in ("EXALTED", "OWN_SIGN") else
           "This dignity placement of the 10th lord doesn't by itself argue strongly either way "
           "for career prominence -- it's one data point among several, not a verdict." if tenth_lord_dignity == "NEUTRAL" else
           "Classically this would be read as a placement that asks for extra effort in career "
           "matters, though a single dignity marker is far from the whole picture of a chart.")
    )

    paras.append(
        f"As of {b.as_of_date}, the ruling planetary period is {b.dasha.mahadasha_lord.title()} "
        f"Mahadasha (running {b.dasha.mahadasha_start} to {b.dasha.mahadasha_end}), currently "
        f"within a {b.dasha.antardasha_lord.title()} Antardasha (through {b.dasha.antardasha_end}). "
        f"Jyotisha reads this Antardasha lord's own condition -- {a.jyotisha_dignity or 'undetermined'} "
        f"in this chart -- as {_valence_word(a.jyotisha_score)} for this period specifically, "
        f"for whatever domain of life that planet governs for this chart."
    )

    if a.hellenistic_score is not None:
        paras.append(
            f"It's worth checking that same planet against a second, independently developed "
            f"tradition rather than taking Jyotisha's word alone. Hellenistic astrology, applied "
            f"to the same underlying sign placement, classifies this chart as a "
            f"{'day' if b.is_day_chart else 'night'} chart and reads {b.dasha.antardasha_lord.title()} "
            f"as {a.hellenistic_dignity.lower().replace('_',' ') if a.hellenistic_dignity else 'undetermined'} "
            f"-- {_valence_word(a.hellenistic_score)} by its own separate weighting (sect rather "
            f"than house placement). The two traditions' agreement here comes out as "
            f"{a.classification.upper()}: {a.reasoning}"
        )
    else:
        paras.append(
            f"Hellenistic astrology doesn't have a usable equivalent for this specific placement "
            f"({a.reasoning}), so this reading can't cross-check the current period against a "
            f"second tradition here -- it's reported as Jyotisha-only rather than stretched into "
            f"a false agreement."
        )

    stem, branch, animal = b.chinese_birth_year
    paras.append(
        f"For additional, purely descriptive color -- not folded into the assessment above, "
        f"since this project has no validated way to score these traditions for favorability -- "
        f"the same chart's tropical Sun sign in Western astrology is "
        f"{b.western_signs.get('sun', 'unresolved')}, and {entity_name}'s birth year falls in the "
        f"Chinese sexagenary year of {stem}-{branch}, the Year of the {animal}."
    )

    if field:
        from .corpus_patterns import compare_to_corpus
        auto_context = compare_to_corpus(field, tenth_lord_dignity)
        if auto_context:
            paras.append(auto_context)
    if corpus_context:
        paras.append(corpus_context)

    paras.append(
        "Several other historical astrological traditions -- Babylonian, Persian/Islamic, "
        "Tibetan, Egyptian, Japanese, and Mayan/Mesoamerican -- are catalogued in this system "
        "with real historical sourcing, but this project has no working calculation engine for "
        "any of them, so none of them contribute a finding to this reading; they're listed here "
        "for completeness, not silently skipped."
    )

    direction = ("a generally favorable" if (a.jyotisha_score or 0) > 0 else
                 "a generally challenging" if (a.jyotisha_score or 0) < 0 else "a mixed/neutral")
    paras.append(
        f"Taken together, the strongest, most cross-checked signal this system can produce for "
        f"{entity_name} as of {b.as_of_date} is {direction} {b.dasha.antardasha_lord.title()} "
        f"period, with {a.classification.lower()} agreement between the two traditions that "
        f"actually compute a comparable dignity score for this chart."
    )

    return "\n\n".join(paras)
