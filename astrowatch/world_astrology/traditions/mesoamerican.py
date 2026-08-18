"""Astrowatch World Astrology -- Mayan/Mesoamerican astrology module (SEED-LEVEL,
reference only). The core, best-established content here is calendrical
(Tzolk'in / Haab' / Long Count), which is real, well-documented astronomy-adjacent
timekeeping -- NOT the same claim as a fully worked-out predictive astrological
interpretive system, which this module does not assert exists in the same sense
as e.g. Hellenistic or Jyotisha natal astrology."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="mesoamerican", school="Maya", technique="Tzolk'in",
        concept="Tzolk'in (260-day sacred count)", definition="A 260-day ritual/"
            "divinatory calendar combining 20 named days with 13 numbers (20x13=260), "
            "used across Mesoamerica (Maya, and related forms among the Aztec/Mexica "
            "as the Tonalpohualli) for naming individuals, timing rituals, and "
            "divination; each of the 260 day-signs carries traditional symbolic/"
            "prognosticatory associations recorded in surviving codices.",
        historical_period="Long-attested pre-Classic through Postclassic Maya "
            "civilization and beyond into the colonial period (some living use "
            "continues today, e.g. among Ixil and K'iche' daykeepers in Guatemala).",
        geographic_origin="Mesoamerica (Maya region; related systems across the "
            "broader Mesoamerican cultural area)",
        confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["mesoamerican:tonalpohualli"],
        computed=False,
        limitations="This project does NOT implement Tzolk'in date conversion or "
            "day-sign lookup -- doing so correctly requires a verified correlation "
            "constant (GMT/Goodman-Martinez-Thompson correlation or a verified "
            "alternative) between the Long Count and the Gregorian calendar, which "
            "this project has not independently validated.",
    ),
    KnowledgeEntry(
        tradition="mesoamerican", school="Aztec/Mexica", technique="Tonalpohualli",
        concept="Tonalpohualli (260-day count, Aztec/Mexica form)", definition="The "
            "Aztec/Mexica 260-day ritual calendar, structurally the same 20-day-sign "
            "x 13-number system as the Maya Tzolk'in, with different day-sign names "
            "and deity associations reflecting the distinct Nahua cultural context; "
            "used for naming, ritual timing, and divinatory day-sign interpretation "
            "(tonalamatl books of days).",
        historical_period="Postclassic period Mexica civilization (14th-16th century "
            "CE), documented extensively in colonial-era codices (e.g. Codex "
            "Borbonicus, Codex Borgia).",
        geographic_origin="Central Mexico (Aztec/Mexica)",
        confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["mesoamerican:tzolkin"],
        notes="PARTIAL_CORRESPONDENCE to Tzolk'in -- same underlying 260-day "
              "mathematical structure (shared Mesoamerican-wide calendrical "
              "invention), but distinct day-sign names/deity associations and "
              "independently developed interpretive traditions.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="mesoamerican", school="Maya", technique="Haab'",
        concept="Haab' (365-day solar calendar)", definition="An 18-month x 20-day "
            "(plus a 5-day Wayeb' period) 365-day approximate solar calendar, run in "
            "parallel with the Tzolk'in; the combination of a Tzolk'in date and a "
            "Haab' date repeats only once every 52 years (the 'Calendar Round').",
        historical_period="Long-attested Maya civilization use, pre-Classic onward.",
        geographic_origin="Mesoamerica (Maya)", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
    ),
    KnowledgeEntry(
        tradition="mesoamerican", school="Maya", technique="Long Count",
        concept="Long Count calendar", definition="A linear (non-repeating, unlike "
            "Tzolk'in/Haab') day count using a modified base-20 positional system "
            "(baktun/katun/tun/winal/k'in units) to track dates across very long "
            "spans, used on Classic-period monumental inscriptions; its correlation "
            "to the Gregorian calendar depends on a scholarly-established constant "
            "(most widely the Goodman-Martinez-Thompson, GMT, correlation).",
        historical_period="Classic period Maya civilization (c. 3rd-10th century CE "
            "monumental inscriptions), with an epoch (creation date) placed in "
            "3114 BCE by the GMT correlation.",
        geographic_origin="Mesoamerica (Maya)", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
        limitations="Not implemented -- the GMT correlation constant is widely accepted "
            "but this project has not independently verified it against a primary "
            "source, and implementing correct proleptic-Gregorian conversion plus the "
            "5-day Wayeb'/leap handling correctly is nontrivial; left as reference-only "
            "rather than risk a silently wrong date-conversion implementation.",
    ),
    KnowledgeEntry(
        tradition="mesoamerican", school="Maya", technique="Day-sign / Year-bearer interpretation",
        concept="Day-sign and Year-bearer symbolic associations", definition="Traditional "
            "symbolic/prognosticatory meanings attached to each of the 20 Tzolk'in "
            "day-signs (e.g. Imix, Ik', Ak'bal...) and to the 4 'Year Bearer' day-signs "
            "that can fall on Haab' New Year, recorded in surviving colonial-era and "
            "post-conquest ethnographic sources and still used by living Maya "
            "daykeepers (especially in the Guatemalan highlands).",
        historical_period="Pre-Columbian through living contemporary practice.",
        geographic_origin="Mesoamerica (Maya)",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        computed=False,
        limitations="Genuinely living tradition with real ethnographic documentation, "
            "but this project has not catalogued the full 20-sign interpretive meanings "
            "from a verified primary/ethnographic source -- marked TRADITIONAL_CLAIM "
            "and left uncatalogued at the individual-meaning level rather than risk "
            "fabricating or half-remembering specific sign meanings.",
    ),
]
