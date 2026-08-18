"""
Astrowatch — Rule Registry (Astrowatch MVP-1 coverage)
==============================================
Structured, source-cited mundane-astrology rules actually extracted and verified
against the primary translations this session. This is NOT the full corpus --
only the chapters listed in `COVERAGE` below have been read and encoded.

Every field with a `citation` traces back to a specific chapter/verse in a named
public-domain translation (see sources.py-equivalent notes inline). Interpretive
text here is PARAPHRASED/normalized from the source, not verbatim reproduction --
go to the cited chapter/verse for the original wording.

Do not add rules to this file from general astrology knowledge. If it's not cited,
it doesn't belong here.
"""

from dataclasses import dataclass, field
from typing import List, Optional


COVERAGE = {
    "brihat_samhita": {
        "translation": "N. Chidambaram Iyer, 1884 (chapters 16-20, 42)",
        "chapters_extracted": ["16", "17", "18", "19", "20", "42"],
        "chapters_not_yet_extracted": [
            "21-41 (atmospheric/earthquake/weather)", "46 (portents)", "103-104 (transits)",
        ],
    },
    "ptolemy_tetrabiblos": {
        "translation": "J.M. Ashmand (sacred-texts.com edition)",
        "chapters_extracted": ["Book II Ch. III", "Book II Ch. VI"],
        "chapters_not_yet_extracted": [
            "Book II Ch. V, VII-XIV", "Book I (partial only, Ch. 1-9)",
        ],
    },
    "grand_conjunction": {
        "status": "Gjamasp material fully classified as Level D (editorial/historical "
                   "report in Ashmand's preface) -- no primary text present in corpus.",
    },
}


@dataclass
class Rule:
    rule_id: str
    tradition: str          # "brihat_samhita" | "ptolemy" | "grand_conjunction"
    author: str
    chapter: str
    citation: str            # verse/section reference
    trigger_type: str        # e.g. "conjunction_defeat", "aspect", "lunar_pass", "eclipse_locality"
    trigger_params: dict     # machine-readable trigger description, engine-specific
    domain: List[str]        # e.g. ["military", "political"]
    geography: str
    timing: str
    interpretation: str      # paraphrased, not verbatim
    modifiers: Optional[str] = None
    exceptions: Optional[str] = None
    source_confidence: str = "Level A"  # per Astrowatch source-weighting scale

    # Phase 4: what coordinate convention this rule actually needs. One of:
    # "zodiac_independent" | "tropical" | "sidereal_unresolved" | "sidereal_tropical_n/a"
    # Never "sidereal_lahiri" -- Lahiri is not textually justified for this corpus
    # (see VALIDATION_REPORT.md Phase 4). Engines refuse to run a rule whose requirement
    # is "sidereal_unresolved" against real dates rather than silently picking Lahiri.
    zodiac_requirement: str = "unresolved"
    zodiac_requirement_note: str = ""


RULES: List[Rule] = [

    # --- Bṛhat Saṃhitā Ch. XVII -- graha-yuddha (planetary conflict) ---
    Rule(
        rule_id="BS-17-04",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 4",
        trigger_type="grahayuddha_class",
        trigger_params={"class": "bheda"},
        domain=["environmental", "social"],
        geography="general / unspecified region of the affected planets' significations",
        timing="at time of conjunction",
        interpretation="Closest-class planetary conjunction (one disc apparently eclipsed "
                        "by the other) -> drought; friends/allied families turn hostile.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-17-04b",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 4",
        trigger_type="grahayuddha_class",
        trigger_params={"class": "ullekha"},
        domain=["military"],
        geography="general",
        timing="at time of conjunction",
        interpretation="Second-closest conjunction class (discs appear to touch) -> war "
                        "in the land, princes quarrel with enemies, but food remains abundant.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-17-05",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 5",
        trigger_type="grahayuddha_class",
        trigger_params={"class": "amsumardana"},
        domain=["military", "economic", "environmental"],
        geography="general",
        timing="at time of conjunction",
        interpretation="Kings at war; mankind suffers from weapons, disease, and hunger.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-17-05b",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 5",
        trigger_type="grahayuddha_class",
        trigger_params={"class": "asavya_apasavya"},
        domain=["political"],
        geography="general",
        timing="at time of conjunction",
        interpretation="Widest-separation conjunction class -> rulers at war with one another.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-17-25",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 25",
        trigger_type="grahayuddha_defeat",
        trigger_params={"defeated": "saturn", "victor": "venus"},
        domain=["economic"],
        geography="general",
        timing="at time of conjunction",
        interpretation="Saturn defeated in conjunction with Venus -> grain/food prices "
                        "rise; snakes and birds suffer.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-17-16",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVII", citation="Sl. 16",
        trigger_type="grahayuddha_defeat",
        trigger_params={"defeated": "mercury", "victor": "jupiter"},
        domain=["geological", "social"],
        geography="Mlecchas, Śūdras, mountainous-country peoples (unmapped ancient names)",
        timing="at time of conjunction",
        interpretation="Mercury defeated in conjunction with Jupiter -> named groups "
                        "suffer, and earthquakes occur.",
        source_confidence="Level A",
    ),

    # --- Bṛhat Saṃhitā Ch. XVIII -- Moon's conjunction with planets ---
    Rule(
        rule_id="BS-18-02",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVIII", citation="Sl. 2",
        trigger_type="lunar_pass",
        trigger_params={"planet": "mars", "side": "north"},
        domain=["military", "economic"],
        geography="general",
        timing="at time of passage",
        interpretation="Moon passes north of Mars -> mountain-warriors and armies "
                        "marching to battle prosper; crops abundant.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-18-06",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVIII", citation="Sl. 6",
        trigger_type="lunar_pass",
        trigger_params={"planet": "saturn", "side": "north"},
        domain=["political"],
        geography="Śaka, Bāhlīka, Sindh, Pahlava, Yavana peoples (unmapped ancient names)",
        timing="at time of passage",
        interpretation="Moon passes north of Saturn -> citizen-rulers triumph in battle; "
                        "named western/foreign peoples prosper.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-18-general",
        tradition="brihat_samhita", author="Varahamihira", chapter="XVIII", citation="Sl. 1, 7-8",
        trigger_type="lunar_pass_general",
        trigger_params={"rule": "north=prosperity, south=misery, reverses by side"},
        domain=["political", "military", "economic", "environmental"],
        geography="general",
        timing="at time of passage",
        interpretation="General rule: Moon passing north of any planet/asterism -> "
                        "prosperity for what it signifies; passing south -> misery. "
                        "These are 'mere meetings' (Samāgama), not conjunctions in fight.",
        source_confidence="Level A",
    ),

    # --- Bṛhat Saṃhitā Ch. XIX -- planetary years ---
    Rule(
        rule_id="BS-19-saturn-year",
        tradition="brihat_samhita", author="Varahamihira", chapter="XIX", citation="Sl. 1-22 (Saturn portion)",
        trigger_type="year_lord",
        trigger_params={"year_lord": "saturn"},
        domain=["military", "economic", "social"],
        geography="general",
        timing="annual (year lord determined by weekday of Caitra new moon)",
        interpretation="Year ruled by Saturn -> major wars, robber bands, cattle death, "
                        "wealth loss, epidemics, civil-strife mourning.",
        modifiers="Effect intensified if Saturn is strong/undebilitated at the relevant "
                   "moment, muted if weak/afflicted.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-19-jupiter-year",
        tradition="brihat_samhita", author="Varahamihira", chapter="XIX", citation="Sl. 1-22 (Jupiter portion)",
        trigger_type="year_lord",
        trigger_params={"year_lord": "jupiter"},
        domain=["economic", "political"],
        geography="general",
        timing="annual",
        interpretation="Year ruled by Jupiter -> abundant crops, general prosperity, "
                        "just rule.",
        source_confidence="Level A",
    ),

    # --- Bṛhat Saṃhitā Ch. XX -- planetary triangle / meetings ---
    Rule(
        rule_id="BS-20-02",
        tradition="brihat_samhita", author="Varahamihira", chapter="XX", citation="Sl. 2",
        trigger_type="multi_planet_shape",
        trigger_params={"shapes": ["circle", "bow", "triangle", "rod", "citadel", "lance"]},
        domain=["economic", "military", "environmental"],
        geography="general",
        timing="when the visual configuration forms",
        interpretation="Multiple planets forming one of these geometric configurations "
                        "-> starvation, drought, and war.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-20-sannipata",
        tradition="brihat_samhita", author="Varahamihira", chapter="XX", citation="Sl. 5-9",
        trigger_type="named_meeting_type",
        trigger_params={"meeting_type": "sannipata"},
        domain=["military"],
        geography="general",
        timing="at time of meeting",
        interpretation="'Sannipāta'-class planetary meeting -> mankind at war with one another.",
        source_confidence="Level A",
    ),

    # --- Bṛhat Saṃhitā Ch. XLII -- price fluctuation ---
    Rule(
        rule_id="BS-42-01a",
        tradition="brihat_samhita", author="Varahamihira", chapter="XLII", citation="Sl. 1",
        trigger_type="omen_on_lunar_node_day",
        trigger_params={"phenomena": ["heavy_rain", "meteor", "danda_formation", "halo",
                                       "eclipse", "parhelion"], "day": "new_or_full_moon"},
        domain=["economic"],
        geography="general",
        timing="new moon or full moon day specifically",
        interpretation="Listed unusual celestial phenomena occurring ON a new/full moon "
                        "day -> predicts RISING prices.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-42-01b",
        tradition="brihat_samhita", author="Varahamihira", chapter="XLII", citation="Sl. 1",
        trigger_type="omen_on_other_day",
        trigger_params={"phenomena": ["heavy_rain", "meteor", "danda_formation", "halo",
                                       "eclipse", "parhelion"], "day": "not_new_or_full_moon"},
        domain=["military", "political"],
        geography="general",
        timing="any day other than new/full moon",
        interpretation="Same phenomena on any OTHER day of the month -> predicts rulers "
                        "going to war rather than a price effect. (Same input, different "
                        "domain, timing-dependent -- a direct MODIFIER example.)",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-42-14",
        tradition="brihat_samhita", author="Varahamihira", chapter="XLII", citation="Sl. 14",
        trigger_type="aspect_to_luminary",
        trigger_params={"luminary": "moon_or_sun_at_new_full_moon", "aspecting": "benefic"},
        domain=["economic"],
        geography="general",
        timing="new/full moon",
        interpretation="New/full moon conjunct or aspected by benefic planets -> prices rise.",
        source_confidence="Level A",
    ),
    Rule(
        rule_id="BS-42-14b",
        tradition="brihat_samhita", author="Varahamihira", chapter="XLII", citation="Sl. 14",
        trigger_type="aspect_to_luminary",
        trigger_params={"luminary": "sun", "aspecting": "malefic"},
        domain=["economic"],
        geography="general",
        timing="relevant lunar day",
        interpretation="Sun conjunct/aspected by malefic planets -> prices fall.",
        source_confidence="Level A",
    ),

    # --- Ptolemy Book II Ch. III -- geography/triplicity table ---
    Rule(
        rule_id="PT-II-3-general",
        tradition="ptolemy", author="Claudius Ptolemy (tr. Ashmand)", chapter="Book II, Ch. III",
        citation="full chapter",
        trigger_type="triplicity_region_table",
        trigger_params={
            "fire_triplicity_signs": ["Aries", "Leo", "Sagittarius"],
            "earth_triplicity_signs": ["Taurus", "Virgo", "Capricorn"],
            "air_triplicity_signs": ["Gemini", "Libra", "Aquarius"],
            "water_triplicity_signs": ["Cancer", "Scorpio", "Pisces"],
            "quadrants": ["NW=Europe", "SE=southern Asia", "NE=northern Asia", "SW=Africa/Libya"],
        },
        domain=["political", "military", "diplomatic", "social"],
        geography="quadrant-and-triplicity-dependent; see geography module for named "
                   "country table (not modernized yet)",
        timing="whenever the relevant triplicity/sign is activated (eclipse, ingress, etc.)",
        interpretation="Master lookup: each zodiac triplicity governs a quadrant of the "
                        "known world and specific named ancient countries within it; used "
                        "as the geography key for eclipse/ingress interpretation.",
        source_confidence="Level A",
    ),

    # --- Ptolemy Book II Ch. VI -- eclipse locality rule ---
    Rule(
        rule_id="PT-II-6-01",
        tradition="ptolemy", author="Claudius Ptolemy (tr. Ashmand)", chapter="Book II, Ch. VI",
        citation="full chapter",
        trigger_type="eclipse",
        trigger_params={"applies_table": "PT-II-3-general"},
        domain=["political", "military", "environmental"],
        geography="determined via PT-II-3-general lookup at the eclipse's zodiacal degree",
        timing="at the eclipse; effect window separately determined (Book II Ch. VII, not yet extracted)",
        interpretation="For any solar/lunar eclipse: note the zodiacal degree of the "
                        "eclipse, find which countries are 'in familiarity' with that "
                        "degree via the Ch. III table -- those countries are comprehended "
                        "in the event, concentrated in whichever of them could actually "
                        "see the eclipse above the horizon.",
        source_confidence="Level A",
    ),
]


# --- Phase 4 zodiac-requirement classification, applied by chapter -----------
# Rationale for each mapping is in VALIDATION_REPORT.md Phase 4. Applied here rather
# than per-Rule() literal to keep the reasoning in one auditable place.
_ZODIAC_REQUIREMENT_BY_CHAPTER = {
    "XVII": ("zodiac_independent", "Conjunction closeness is a planet-to-planet angular "
             "separation; a constant ayanamsa offset cancels out between two bodies."),
    "XVIII": ("zodiac_independent", "Ecliptic-latitude (north/south) comparison; ayanamsa "
              "is a longitude shift and does not affect latitude."),
    "XVI": ("zodiac_independent", "Fixed planet-to-region signification table; no "
            "date-dependent zodiac-sign calculation involved."),
    "XIX": ("sidereal_unresolved", "Year-lord keyed to the calendrical month Caitra, "
            "conventionally sidereal in the Hindu calendar tradition, but the extracted "
            "text specifies no precession model. Do not default to Lahiri."),
    "XX": ("sidereal_unresolved", "Planet-to-planet shape/defeat logic is zodiac-"
           "independent, but the compass-sector geographic mapping's zodiacal basis (if "
           "any) is not established in the extracted text."),
    "XLII": ("sidereal_unresolved", "Rule explicitly keys effects to the Sun's zodiac "
             "sign; text predates any named ayanamsa standard by ~1400 years. Do not "
             "default to Lahiri."),
    "Book II, Ch. III": ("tropical", "Hellenistic triplicity system is unambiguously "
                          "equinox/solstice-anchored (tropical) per established scholarship."),
    "Book II, Ch. VI": ("tropical", "Applies the Ch. III tropical triplicity table."),
}


def _apply_zodiac_requirements():
    for r in RULES:
        mapping = _ZODIAC_REQUIREMENT_BY_CHAPTER.get(r.chapter)
        if mapping:
            r.zodiac_requirement, r.zodiac_requirement_note = mapping
        elif r.tradition == "grand_conjunction":
            r.zodiac_requirement, r.zodiac_requirement_note = (
                "sidereal_tropical_n/a", "Historical report only, no operative calculation to classify.")


_apply_zodiac_requirements()


def rules_for_tradition(tradition: str) -> List[Rule]:
    return [r for r in RULES if r.tradition == tradition]


def rule_by_id(rule_id: str) -> Optional[Rule]:
    for r in RULES:
        if r.rule_id == rule_id:
            return r
    return None
