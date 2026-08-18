"""
Astrowatch World Astrology -- Western astrology tradition module (medieval through
modern), clearly split by historical period per the spec's requirement.

DEPTH: concepts catalogued; only tropical planetary placement (this project's
existing tropical calc_ut output, already computed for every chart alongside the
sidereal one) is actually wired to real numbers. Transits/progressions/synastry/
composite charts/outer-planet interpretation are NOT computed -- this project has
never built transit-to-natal or progression math.
"""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="western", school="Medieval/Traditional", technique="Medieval astrology",
        concept="Medieval Western astrology", definition="The continuation and "
            "elaboration of Hellenistic astrology through the medieval period, heavily "
            "mediated through Arabic-language transmission and translation (see the "
            "Persian/Islamic module) before reaching Latin Europe.",
        historical_period="c. 8th-15th century CE",
        geographic_origin="Transmitted via the Islamic world into Latin Europe",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        cross_tradition_relationships=["persian_islamic:islamic_golden_age_astrology"],
        historical_evidence="Well-documented transmission chain: Hellenistic Greek texts "
            "-> Arabic translation/elaboration (8th-10th c.) -> Latin translation "
            "(12th-13th c., e.g. via Toledo) -> medieval European practice.",
    ),
    KnowledgeEntry(
        tradition="western", school="Renaissance", technique="Renaissance astrology",
        concept="Renaissance Western astrology", definition="Continued elaboration of "
            "traditional astrology through the Renaissance, alongside the beginnings of "
            "the astronomy/astrology split following the Copernican revolution.",
        historical_period="c. 15th-17th century CE", geographic_origin="Europe",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
    ),
    KnowledgeEntry(
        tradition="western", school="Traditional", technique="Traditional Western astrology (revival)",
        concept="Traditional astrology revival", definition="A modern (20th-21st century) "
            "movement to recover and practice Hellenistic/medieval techniques (whole-sign "
            "houses, sect, essential dignity, etc.) as historically attested, distinct "
            "from the modern psychological mainstream.",
        historical_period="Revival movement, late 20th century - present",
        geographic_origin="International (English-language scholarship-driven)",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        notes="Overlaps heavily with this module's Hellenistic entries in practice, but "
              "is itself a modern historiographic/practice movement, not the ancient "
              "tradition itself -- kept as a separate, labeled entry per the spec's "
              "'label historical vs modern' requirement.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Modern natal astrology",
        concept="Modern tropical natal astrology", definition="The mainstream 20th-21st "
            "century Western practice: tropical zodiac, usually Placidus or similar "
            "quadrant houses, incorporating Uranus/Neptune/Pluto, degree-based aspects "
            "with orbs.",
        historical_period="c. late 19th century - present",
        geographic_origin="International, dominant in English-language popular astrology",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION,
        calculation_method="This project's kundli.py already computes tropical longitudes "
            "for every chart (FLG_SWIEPH without FLG_SIDEREAL) alongside the sidereal "
            "values it actually uses for Jyotisha -- so tropical SIGN placement is real, "
            "computed data. House system is NOT computed for tropical/Western use (this "
            "project's Ascendant/house math is whole-sign only, the Hellenistic/Jyotisha "
            "convention, not Placidus).",
        required_astronomical_inputs=["tropical ecliptic longitude"],
        prediction_domain=["natal"],
        computed=True,
        limitations="Only tropical SIGN placement is real/computed. No quadrant house "
            "system, no aspect-orb calculator, and Uranus/Neptune/Pluto are not computed "
            "anywhere in this project (kundli.py's GRAHA_BODY_IDS only includes the 7 "
            "classical planets + mean node) -- so a 'complete' modern Western chart "
            "cannot actually be produced by this codebase.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern/Psychological", technique="Psychological astrology",
        concept="Psychological astrology", definition="A 20th-century movement (strongly "
            "associated with Dane Rudhyar, Liz Greene, and Jungian psychology) "
            "reinterpreting astrological symbolism as a language of psychological "
            "archetype and self-development rather than event prediction.",
        historical_period="c. mid-20th century - present", geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Transits",
        concept="Transits", definition="Reading the CURRENT real-time position of planets "
            "against a natal chart's fixed positions.",
        historical_period="Modern emphasis; the underlying idea of a planet's current "
            "position mattering has ancient roots (cf. Gochara in Jyotisha) but the "
            "specific modern transit-interpretation framework is a later development.",
        geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        cross_tradition_relationships=["jyotisha:gochara"],
        limitations="NOT implemented -- no natal-to-transit comparison/orb logic exists "
            "in this project.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Progressions",
        concept="Secondary progressions", definition="A symbolic timing technique "
            "(most commonly 'a day for a year') advancing the natal chart forward.",
        historical_period="Modern systematization, though the day-for-a-year principle "
            "has older roots (Ptolemy discusses a related concept).",
        geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        limitations="NOT implemented.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Synastry",
        concept="Synastry", definition="Comparing two people's natal charts against each "
            "other for relationship compatibility -- the Western structural analogue of "
            "Jyotisha's Ashtakoot Guna Milan, independently developed.",
        historical_period="Modern emphasis (chart comparison itself is ancient, but "
            "'synastry' as a named systematic practice is a modern term/framework).",
        geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        cross_tradition_relationships=["jyotisha:ashtakoot_guna_milan"],
        notes="This project DOES compute a real match-making system, but it's the "
              "Jyotisha Ashtakoot system (36-point Guna Milan, see matchmaking.js in "
              "Kundli Studio), not Western synastry -- they are functionally analogous "
              "(both compare two natal charts for compatibility) but use entirely "
              "different techniques and are not interchangeable.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Composite charts",
        concept="Composite charts", definition="A single chart built from the midpoints "
            "of two people's natal placements, representing 'the relationship itself' as "
            "an entity.",
        historical_period="20th century development.", geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        limitations="NOT implemented.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Solar / lunar returns",
        concept="Solar and lunar returns", definition="A chart cast for the exact moment "
            "the transiting Sun (or Moon) returns to its natal degree, read as governing "
            "the year (or month) ahead.",
        historical_period="Solar returns have Hellenistic roots (see that module); lunar "
            "returns are a modern monthly-cycle extension of the same idea.",
        geographic_origin="Hellenistic origin, modern extension",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        computed=True,
        calculation_method="This project's Kundli Studio already computes a real solar-"
            "return chart (Newton's-method solver for the exact return instant, plus "
            "Muntha) -- see varshaphal.js. Lunar returns are NOT implemented.",
        limitations="Solar return: computed (as Jyotisha's Varshaphal, not under a "
            "dedicated 'Western' label anywhere in the UI). Lunar return: not computed.",
    ),
    KnowledgeEntry(
        tradition="western", school="Modern", technique="Outer-planet interpretation",
        concept="Uranus, Neptune, Pluto", definition="Modern astrology's incorporation of "
            "the 3 outer planets (undiscovered/unknown to any ancient tradition) as "
            "significators of generational/collective themes.",
        historical_period="Uranus discovered 1781, Neptune 1846, Pluto 1930 -- necessarily "
            "post-dates every ancient tradition in this package by definition.",
        geographic_origin="International",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION, computed=False,
        limitations="NOT computed anywhere in this project -- kundli.py's planetary body "
            "list is fixed to the 7 classical planets + mean node, deliberately, since "
            "every other tradition in this system (Jyotisha, Hellenistic, Babylonian, "
            "etc.) predates telescopic astronomy entirely.",
    ),
]
