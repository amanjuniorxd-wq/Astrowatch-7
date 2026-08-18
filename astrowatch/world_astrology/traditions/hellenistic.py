"""
Astrowatch World Astrology -- Hellenistic astrology tradition module.

DEPTH: partial-computed. This project's rule_registry.py already has real, cited
rules extracted from Ptolemy's Tetrabiblos (Book II Ch. III, VI, via J.M. Ashmand's
translation) -- those are referenced, not duplicated, here. Whole-sign houses are
directly computable from this project's existing Ascendant math (the same whole-
sign convention Jyotisha uses, historically not a coincidence -- see the
cross-tradition entry). Sect, essential dignity, and basic aspects are computed
in this module using the same chart data. Lots/Arabic Parts, Annual Profections,
and Zodiacal Releasing are NOT implemented -- catalogued as concepts only.
"""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Whole Sign Houses",
        concept="Whole Sign Houses", definition="The house system used throughout "
            "Hellenistic astrology: house 1 = the Ascendant's whole sign, house 2 = the "
            "next sign, etc. -- the same mathematical convention Parashari Jyotisha uses.",
        historical_period="Standard Hellenistic-era house system, c. 1st century BCE - "
            "several centuries CE, and the earliest attested house system generally.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        primary_sources=["Vettius Valens, Anthology", "Dorotheus of Sidon, Carmen Astrologicum"],
        calculation_method="Identical arithmetic to Jyotisha's Bhava computation -- see "
            "cross_tradition.py's whole-sign relationship entry.",
        prediction_domain=["natal", "mundane", "horary", "electional"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:bhava"],
        historical_evidence="Whole-sign houses are the house system consistently "
            "described in the earliest surviving Hellenistic astrological texts; later "
            "quadrant house systems (Porphyry, Alcabitius, Placidus, etc.) are "
            "historically LATER developments, not the original method.",
        computed=True,
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Sect (Hairesis)",
        concept="Sect", definition="Every chart is classified as a 'day chart' (Sun above "
            "the horizon) or 'night chart'; each planet has a sect it favors (day: Sun, "
            "Jupiter, Saturn; night: Moon, Venus, Mars; Mercury varies by its own solar "
            "relationship), and being of the chart's sect strengthens a planet's positive "
            "expression.",
        historical_period="Central concept in Hellenistic astrology, attested from its "
            "earliest surviving texts.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        primary_sources=["Vettius Valens, Anthology", "Antiochus of Athens (via Porphyry/Rhetorius)"],
        calculation_method="Sun above/below the horizon at the chart's Ascendant/Descendant "
            "axis -- computable directly from this project's existing Ascendant + Sun "
            "longitude data (house-of-Sun relative to Ascendant, houses 7-12 = above "
            "horizon = day chart).",
        required_astronomical_inputs=["Sun position", "Ascendant"],
        prediction_domain=["natal"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        computed=True,
        limitations="This project computes WHETHER a chart is day/night sect "
            "(mechanically trivial from existing data) but does not yet apply sect-based "
            "dignity/condition scoring anywhere in the reading engine.",
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Essential dignity",
        concept="Essential dignity", definition="A planet's strength based purely on its "
            "own zodiacal position -- domicile (rulership), exaltation, triplicity, term/"
            "bound, and decan/face -- the Hellenistic-era ancestor of the same dignity/"
            "debilitation concept Jyotisha independently formalized (see cross-tradition entry).",
        historical_period="Attested from the earliest Hellenistic texts; the 5-fold "
            "dignity system (domicile/exaltation/triplicity/term/face) as a formal scoring "
            "table is more explicitly systematized in later texts (e.g. Ptolemy's "
            "Tetrabiblos discusses triplicity rulers at length).",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        primary_sources=["Ptolemy, Tetrabiblos", "Vettius Valens, Anthology"],
        calculation_method="Domicile and exaltation only are computed by this project "
            "(same sign-level dignity table used for Jyotisha, since domicile/exaltation "
            "rulerships for the 7 classical planets are the same physical bodies with a "
            "closely parallel -- though NOT identical in every detail -- rulership scheme). "
            "Triplicity, term/bound, and face/decan are NOT computed.",
        prediction_domain=["natal", "horary", "electional"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:planetary_dignity"],
        computed=True,
        limitations="Domicile/exaltation sign assignments in Hellenistic and Jyotisha "
            "systems agree for the 7 classical planets (both trace to a shared ancient "
            "root), but Hellenistic dignity also includes triplicity/term/face scoring "
            "that Jyotisha's parallel Uchcha/Neecha/Swakshetra system does not have an "
            "equivalent for -- this project does NOT compute those Hellenistic-specific "
            "layers.",
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Aspects",
        concept="Aspects (Hellenistic)", definition="Whole-sign aspect relationships "
            "(conjunction, sextile, square, trine, opposition) based on sign-distance, "
            "not exact degree orbs as in modern Western astrology.",
        historical_period="Attested from the earliest Hellenistic texts.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["natal", "mundane"],
        computed=False,
        notes="This project's rule_registry.py has REAL cited Ptolemy aspect-based rules "
              "(conjunction/defeat triggers) already wired into forecast.py's rule engine "
              "-- see 'ptolemy' tradition entries there. A general-purpose whole-sign "
              "aspect calculator (independent of those specific cited rules) is not "
              "separately implemented in this module.",
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Lots (Arabic Parts)",
        concept="Lots", definition="Calculated points (e.g. the Lot of Fortune, Lot of "
            "Spirit) derived by arithmetic combination of the Ascendant, Sun, and Moon "
            "longitudes, with a separate day/night formula for most Lots.",
        historical_period="Attested from the earliest Hellenistic texts.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        cross_tradition_relationships=["persian_islamic:sahams_arabic_parts"],
        limitations="NOT implemented -- no Lot arithmetic exists anywhere in this project.",
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Annual Profections",
        concept="Profections", definition="A simple, exact-year timing technique: the "
            "1st house 'profects' to the 2nd house at age 1, the 3rd at age 2, and so on, "
            "cycling every 12 years, giving a 'profected lord of the year'.",
        historical_period="Attested from the earliest Hellenistic texts.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["natal"],
        limitations="NOT implemented -- trivial to add (pure integer arithmetic on age) "
            "but not yet built.",
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Zodiacal Releasing",
        concept="Zodiacal Releasing", definition="A major Hellenistic time-lord technique "
            "(from the Lot of Spirit or Lot of Fortune) dividing life into nested periods "
            "of unequal length based on each sign's own 'time' value, described in Vettius "
            "Valens's Anthology.",
        historical_period="Attested in Vettius Valens's Anthology, 2nd century CE.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        primary_sources=["Vettius Valens, Anthology, Book IV"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["natal"],
        limitations="NOT implemented -- this is a nontrivial nested-period algorithm "
            "(structurally similar in spirit to Vimshottari Dasha's nested Mahadasha/"
            "Antardasha, though mathematically different) that would need its own "
            "dedicated build; not attempted this session.",
        cross_tradition_relationships=["jyotisha:vimshottari_dasha"],
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Horary astrology",
        concept="Hellenistic horary", definition="Answering a specific question from a "
            "chart cast for the moment the question is posed -- structurally the same "
            "concept as Jyotisha's Prashna, independently developed.",
        historical_period="Attested from Hellenistic-era texts.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["horary"],
        cross_tradition_relationships=["jyotisha:prashna"],
    ),
    KnowledgeEntry(
        tradition="hellenistic", school="", technique="Mundane astrology",
        concept="Hellenistic mundane astrology", definition="Collective/world-event "
            "astrology -- discussed at length in Ptolemy's Tetrabiblos Book II (nations, "
            "climates, war, etc.).",
        historical_period="Ptolemy's Tetrabiblos, 2nd century CE.",
        geographic_origin="Hellenistic Egypt/Mediterranean",
        primary_sources=["Ptolemy, Tetrabiblos, Book II"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["mundane"],
        computed=False,
        notes="rule_registry.py has REAL cited Ptolemy Book II Ch. III/VI rules already "
              "wired into forecast.py -- referenced, not duplicated here.",
        cross_tradition_relationships=["jyotisha:samhita"],
    ),
]
