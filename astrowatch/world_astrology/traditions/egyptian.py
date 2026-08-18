"""Astrowatch World Astrology -- Egyptian astrology module (SEED-LEVEL, reference
only). NOTE: much of what is popularly marketed as "Egyptian astrology" (e.g. the
often-circulated "Egyptian zodiac" of Nile-god signs) is a MODERN syncretic
invention, not a native ancient Egyptian system -- this module explicitly flags
that distinction rather than repeating the popular claim as if it were ancient."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="egyptian", school="", technique="Decans",
        concept="Decans (36 ten-day star groups)", definition="36 groups of stars "
            "(decans), each associated with a ~10-day period of the 360-day civil "
            "calendar (plus 5 epagomenal days), used for nighttime timekeeping via "
            "their heliacal risings; attested on coffin lids ('diagonal star clocks') "
            "from the Middle Kingdom onward. The decan system is historically "
            "significant as a likely contributor (via Hellenistic Egypt) to the "
            "36 Hellenistic/Western zodiac decans (3 decans per zodiac sign).",
        historical_period="Diagonal star clocks attested from the Middle Kingdom "
            "(c. 2100-1700 BCE); decans continued in use through the Ptolemaic period, "
            "where they became linked to the 12-sign zodiac (itself a Babylonian/"
            "Hellenistic import into Egypt, not a native Egyptian invention).",
        geographic_origin="Ancient Egypt", confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["hellenistic:zodiac_signs", "babylonian:zodiac_origin"],
        notes="The link from native Egyptian decans to the later 3-decans-per-sign "
              "Hellenistic scheme is HISTORICAL_INFLUENCE, not DIRECT_CORRESPONDENCE -- "
              "the native decan system organized the whole sky into 36 star groups for "
              "timekeeping, independent of any 12-sign zodiac (which reached Egypt from "
              "Babylon/the Hellenistic world only later, in the Ptolemaic period).",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="egyptian", school="", technique="12-sign zodiac in Egypt (Ptolemaic import)",
        concept="Egyptian adoption of the Babylonian/Hellenistic zodiac",
        definition="The familiar 12-sign zodiac (as depicted famously on the Dendera "
            "Temple ceiling relief, Ptolemaic/Roman period) was adopted into Egypt from "
            "Babylonian/Hellenistic astronomy/astrology; it is NOT a native ancient "
            "Egyptian invention, despite popular framing to the contrary.",
        historical_period="Ptolemaic period (post-4th century BCE) through Roman Egypt; "
            "the Dendera zodiac itself dates to c. 50 BCE.",
        geographic_origin="Egypt (import, ultimate origin Mesopotamia)",
        confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["babylonian:zodiac_origin", "hellenistic:zodiac_signs"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="egyptian", school="", technique="'Egyptian zodiac' (modern pop-astrology system)",
        concept="Modern 'Egyptian zodiac' god-signs", definition="A widely circulated "
            "modern system assigning personality profiles to 12 Egyptian deities "
            "(e.g. Horus, Isis, Osiris) by birth-date range, popularized in modern "
            "books/websites. This is a MODERN SYNCRETIC INVENTION, not an ancient "
            "Egyptian astrological system -- it is included here only to explicitly "
            "distinguish it from the genuine ancient decan tradition above, since the "
            "two are frequently and incorrectly conflated in popular sources.",
        historical_period="Modern (20th-21st century popular astrology publishing).",
        geographic_origin="Not ancient Egypt -- modern Western pop-astrology",
        confidence_level=EvidenceLevel.MODERN_INTERPRETATION,
        computed=False,
        limitations="Explicitly NOT treated as historical ancient Egyptian astrology in "
            "this system -- included only as a documented disambiguation entry so this "
            "project does not implicitly endorse the popular conflation.",
    ),
    KnowledgeEntry(
        tradition="egyptian", school="", technique="Heliacal rising of Sopdet (Sirius)",
        concept="Sothic cycle / Sopdet heliacal rising", definition="The heliacal rising "
            "of the star Sopdet (Sirius) was used to mark the start of the Egyptian "
            "civil new year and was linked to the annual Nile flood; a foundational "
            "astronomical-observational practice underlying Egyptian timekeeping, though "
            "it functioned primarily as a calendrical/agricultural marker rather than a "
            "predictive/interpretive astrological technique in the sense used by other "
            "traditions in this system.",
        historical_period="Attested from the Old Kingdom onward.",
        geographic_origin="Ancient Egypt", confidence_level=EvidenceLevel.ESTABLISHED,
        computed=False,
        limitations="Genuine astronomical/calendrical technique, but this project has "
            "not implemented heliacal-rising calculation (it requires atmospheric "
            "extinction/visibility modeling, not just raw ephemeris longitude, and is "
            "out of scope for this module).",
    ),
]
