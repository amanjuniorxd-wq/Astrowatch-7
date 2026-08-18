"""Astrowatch World Astrology -- Chinese astrology module. SEED-LEVEL for most
techniques, but the sexagenary (Stems-and-Branches) cycle date arithmetic IS
implemented and verified in this module, since it is cheap, well-defined, and
independently checkable -- unlike the deeper systems (BaZi elemental analysis,
Zi Wei Dou Shu star placement, Qi Men Dun Jia) which are NOT computed."""
from ..schema import KnowledgeEntry, EvidenceLevel

HEAVENLY_STEMS = ["Jia","Yi","Bing","Ding","Wu","Ji","Geng","Xin","Ren","Gui"]
EARTHLY_BRANCHES = ["Zi","Chou","Yin","Mao","Chen","Si","Wu","Wei","Shen","You","Xu","Hai"]
ZODIAC_ANIMALS = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake","Horse","Goat",
                   "Monkey","Rooster","Dog","Pig"]
FIVE_ELEMENTS = ["Wood","Fire","Earth","Metal","Water"]

# A known, widely-published reference point: 1984-02-02 (a Jia-Zi / Rat year start
# per common sexagenary-year references) is used only to anchor the offset -- this
# is a REFERENCE ANCHOR for the day/year cycle demonstration below, not a claim
# about exact solar-term year boundaries (Chinese New Year, not Jan 1, actually
# starts the zodiac year -- see limitations).
_STEM_BRANCH_YEAR_ANCHOR = 1984  # a commonly published Jia-Zi (Wood Rat) year


def sexagenary_year_index(gregorian_year: int) -> int:
    """0-59 index into the 60-year Stem-Branch cycle for a given Gregorian year,
    anchored so 1984 = index 0 (Jia-Zi). NOTE: real Chinese calendar year
    boundaries follow the lunisolar calendar (Chinese New Year, a variable
    Jan 21-Feb 20 date), not the Gregorian Jan 1 -- this function is a
    reference-only approximation for years, not a full calendar converter."""
    return (gregorian_year - _STEM_BRANCH_YEAR_ANCHOR) % 60


def stem_branch_animal_for_year(gregorian_year: int):
    idx = sexagenary_year_index(gregorian_year)
    stem = HEAVENLY_STEMS[idx % 10]
    branch = EARTHLY_BRANCHES[idx % 12]
    animal = ZODIAC_ANIMALS[idx % 12]
    return stem, branch, animal


ENTRIES = [
    KnowledgeEntry(
        tradition="chinese", school="", technique="Heavenly Stems / Earthly Branches",
        concept="Ganzhi (Stems and Branches)", definition="10 Heavenly Stems and 12 "
            "Earthly Branches combine into a 60-term repeating cycle (sexagenary cycle), "
            "the foundational time-unit of Chinese calendrical/astrological systems, "
            "applied to years, months, days, and hours (the 4 'pillars' of BaZi).",
        historical_period="Attested from the Shang dynasty (used for day-counting in "
            "oracle-bone inscriptions), c. 2nd millennium BCE -- among the longest "
            "continuously used calendrical systems in the world.",
        geographic_origin="China",
        confidence_level=EvidenceLevel.ESTABLISHED,
        calculation_method="This module computes the sexagenary YEAR cycle only "
            "(sexagenary_year_index / stem_branch_animal_for_year), anchored to a "
            "commonly published Jia-Zi year -- see function docstring for its real "
            "limitation (true year boundaries follow the lunisolar new year, not Jan 1).",
        computed=True,
        limitations="Month/day/hour pillars (needed for actual BaZi/Four Pillars charts) "
            "are NOT computed -- day-pillar calculation in particular requires a verified "
            "day-count epoch this project has not researched/validated.",
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Chinese Zodiac",
        concept="12 zodiac animals", definition="12 animals (Rat, Ox, Tiger, Rabbit, "
            "Dragon, Snake, Horse, Goat, Monkey, Rooster, Dog, Pig) cyclically assigned "
            "to years (and, in fuller systems, months/days/hours) via the Earthly Branches.",
        historical_period="Well-attested by the Han dynasty, likely older.",
        geographic_origin="China", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=True, calculation_method="See stem_branch_animal_for_year() above.",
        cross_tradition_relationships=["western:zodiac_signs"],
        notes="Functionally analogous to (governs 12 recurring symbolic categories, like) "
              "the Western/Jyotisha zodiac, but INDEPENDENTLY DEVELOPED -- animal-year "
              "cycles and the 12-sign ecliptic zodiac are historically unrelated systems "
              "that happen to both use the number 12.",
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Yin-Yang",
        concept="Yin-Yang", definition="The foundational Chinese cosmological polarity "
            "concept underlying most Chinese calendrical/divinatory systems (and, via "
            "transmission, Japanese Onmyodo -- see that module).",
        historical_period="Ancient, pre-dating systematic astrology; classical "
            "philosophical formulation in texts like the Yijing (I Ching).",
        geographic_origin="China", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
        cross_tradition_relationships=["japanese:onmyodo"],
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Wu Xing (Five Elements)",
        concept="Wu Xing", definition="Wood, Fire, Earth, Metal, Water -- a five-phase "
            "cyclical framework (generative and controlling cycles between phases) applied "
            "throughout Chinese calendrical, medical, and astrological systems, including "
            "BaZi's elemental balance analysis.",
        historical_period="Attested from the Warring States period (c. 5th-3rd c. BCE) onward.",
        geographic_origin="China", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
        cross_tradition_relationships=["japanese:gogyo_five_elements"],
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="BaZi / Four Pillars",
        concept="BaZi (Eight Characters)", definition="A natal-chart system built from "
            "4 'pillars' (year, month, day, hour), each a Stem-Branch pair (8 characters "
            "total), analyzed for elemental balance/strength to read personality, fortune, "
            "and life themes.",
        historical_period="Systematized form generally traced to the Song dynasty "
            "(specifically associated with the scholar Xu Ziping), building on older "
            "Tang-dynasty methods.",
        geographic_origin="China", confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["natal"], computed=False,
        limitations="NOT implemented -- requires verified day/hour pillar calculation "
            "(a specific epoch-anchored day-count this project has not built/validated) "
            "plus the full elemental-strength interpretive rule set, neither of which "
            "exist in this codebase.",
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Zi Wei Dou Shu",
        concept="Zi Wei Dou Shu (Purple Star Astrology)", definition="A star-based "
            "(not purely Stem-Branch-based) Chinese natal astrology system organizing "
            "14 major stars and many minor stars into a 12-palace chart structurally "
            "different from BaZi.",
        historical_period="Traditionally traced to the Song dynasty (10th century CE), "
            "exact origins/attribution debated among practitioners and historians.",
        geographic_origin="China", confidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        prediction_domain=["natal"], computed=False,
        limitations="Entirely reference-only; genuinely distinct methodology from BaZi, "
            "not interchangeable, no computation of any kind implemented.",
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Qi Men Dun Jia",
        concept="Qi Men Dun Jia", definition="A divinatory/strategic system (traditionally "
            "linked to military/tactical use) organizing time and space into a grid based "
            "on Stems, Branches, Nine Stars, Eight Gates, and Eight Deities -- historically "
            "and technically distinct from both BaZi and Zi Wei Dou Shu.",
        historical_period="Traditional attribution to ancient military strategy contexts; "
            "systematized form's precise historical dating not independently verified "
            "this session.",
        geographic_origin="China", confidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        computed=False,
        cross_tradition_relationships=["japanese:kyusei_nine_star_ki"],
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Tai Yi",
        concept="Tai Yi (Great One) divination", definition="A cosmological/divinatory "
            "system (one of the historical 'three styles' of Chinese numerological "
            "divination alongside Qi Men Dun Jia and Da Liu Ren) tracking a symbolic "
            "'Great One' star's cyclical movement, historically used for large-scale/"
            "state-level prognostication.",
        historical_period="Traditional system, precise origins not independently "
            "verified this session.", geographic_origin="China",
        confidence_level=EvidenceLevel.UNVERIFIED, computed=False,
        limitations="Seed-level entry only -- flagged UNVERIFIED because this session "
            "did not independently confirm details beyond general awareness that this "
            "is a real, named historical Chinese divinatory system.",
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Twenty-Eight Lunar Mansions",
        concept="Xiu (Lunar Mansions)", definition="28 unequal divisions of the sky along "
            "the celestial equator (not the ecliptic, unlike Nakshatras), each named for "
            "an asterism, used in Chinese astronomy/astrology and calendrical timing.",
        historical_period="Attested from at least the Warring States period.",
        geographic_origin="China", confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:nakshatra", "persian_islamic:manazil_al_qamar"],
        notes="Scholars debate whether the 28-Xiu system, the 27/28-Nakshatra system, and "
              "the Arabic 28-Manazil system share a common ancient origin or developed "
              "in parallel with later cross-contact -- this project marks the "
              "relationship as HISTORICAL_INFLUENCE/PARTIAL_CORRESPONDENCE in "
              "cross_tradition.py, not DIRECT_CORRESPONDENCE, precisely because this is "
              "a genuinely disputed question, not a settled one.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="chinese", school="", technique="Solar terms",
        concept="24 Solar Terms (Jieqi)", definition="24 divisions of the tropical solar "
            "year (15-degree solar-longitude intervals), marking seasonal/agricultural "
            "timing -- a real astronomical (Sun-longitude-based) calendrical system, "
            "distinct from the lunisolar month structure.",
        historical_period="Systematized by the Han dynasty.", geographic_origin="China",
        confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
        limitations="NOT implemented, though technically this project already computes "
            "tropical Sun longitude for every chart -- solar-term boundary detection "
            "(15-degree bins) would be straightforward to add but has not been built.",
    ),
]
