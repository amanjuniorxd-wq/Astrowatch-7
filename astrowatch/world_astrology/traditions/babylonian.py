"""Astrowatch World Astrology -- Babylonian/Mesopotamian module. SEED-LEVEL: a
small number of well-established reference facts, spot-verified via live search
this session (Enuma Anu Enlil / MUL.APIN / Astronomical Diaries facts). NO
computational engine -- this project does not implement cuneiform-calendar
conversion or any Babylonian-specific astronomical calculation."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="babylonian", school="", technique="Enuma Anu Enlil",
        concept="Celestial omen compilation", definition="A canonical Mesopotamian "
            "series of roughly 70 cuneiform tablets containing an estimated 6,500-7,000 "
            "celestial/meteorological omens, pairing an observed phenomenon (protasis) "
            "with a predicted consequence (apodosis), overwhelmingly focused on the king "
            "and state rather than individuals.",
        historical_period="Origins traced to the Old Babylonian period (2nd millennium "
            "BCE), compiled into its canonical form later.",
        geographic_origin="Mesopotamia",
        primary_sources=["Enuma Anu Enlil (cuneiform tablet series)"],
        secondary_sources=["Francesca Rochberg, scholarship on Babylonian celestial "
                            "divination (general field reference, not a specific title "
                            "verified this session)"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["mundane"],
        historical_evidence="Verified via live search this session (multiple academic "
            "sources); title etymology 'When Anu and Enlil' from its incipit.",
        cross_tradition_relationships=["jyotisha:samhita"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="babylonian", school="", technique="MUL.APIN",
        concept="Star catalog / astronomical compendium", definition="A two-tablet "
            "compendium organizing stars into the 'paths' of Ea, Anu, and Enlil, "
            "including fixed-star (ziqpu) lists, planetary information, heliacal risings, "
            "the Moon's path, calendrical intercalation rules, and a shadow-clock table.",
        historical_period="Compiled roughly 1000 BCE, based on older material.",
        geographic_origin="Mesopotamia",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        historical_evidence="Verified via live search this session.",
        computed=False,
        notes="Represents observational/systematizing astronomy more than omen "
              "interpretation -- see this module's own 'observational vs omen' "
              "distinction note below.",
    ),
    KnowledgeEntry(
        tradition="babylonian", school="", technique="Astronomical Diaries",
        concept="Astronomical Diaries", definition="Regular cuneiform records (Late "
            "Babylonian period) of celestial observations (planetary positions, eclipses, "
            "etc.) alongside terrestrial events (river levels, prices, political events) "
            "for the same period -- among the longest-running systematic observational "
            "records in the ancient world.",
        historical_period="Late Babylonian period, roughly 7th century BCE - 1st century CE.",
        geographic_origin="Mesopotamia (Babylon)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        historical_evidence="Verified via live search this session.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="babylonian", school="", technique="Venus observations",
        concept="Venus Tablet of Ammisaduqa", definition="A record of Venus's heliacal "
            "risings/settings over roughly 21 years during the reign of King Ammisaduqa, "
            "one of the earliest surviving systematic planetary observation records, later "
            "copied and referenced for centuries.",
        historical_period="Original observations traditionally dated to the reign of "
            "Ammisaduqa (Old Babylonian period, exact absolute date debated and tied to "
            "the wider, still-disputed Mesopotamian chronology question).",
        geographic_origin="Mesopotamia",
        confidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        historical_evidence="The tablet's existence and content are established; its "
            "precise absolute dating is a genuine, long-running scholarly dispute tied "
            "to Mesopotamian chronology debates -- not independently re-verified in "
            "detail this session.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="babylonian", school="", technique="Royal and political omens",
        concept="Royal/political omen interpretation", definition="The dominant "
            "application of Babylonian celestial omens: interpreted primarily for the "
            "king and the state (war, succession, the fate of the country), not "
            "individual natal astrology (which develops much later, closer to the "
            "Hellenistic period, in Mesopotamia).",
        historical_period="2nd-1st millennium BCE.", geographic_origin="Mesopotamia",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["mundane"],
        cross_tradition_relationships=["jyotisha:samhita", "hellenistic:mundane_astrology"],
        notes="Individual natal astrology (a horoscope cast for a specific person's "
              "birth) is a LATER Babylonian development, emerging in the mid-1st "
              "millennium BCE, and is understood by scholars as feeding into the later "
              "Hellenistic system rather than being the earliest Babylonian practice.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="babylonian", school="", technique="Observational astronomy vs. omen "
            "interpretation (methodological note)",
        concept="Distinction: astronomy vs. astrology", definition="This project "
            "deliberately keeps Babylonian OBSERVATIONAL astronomy (MUL.APIN's star "
            "catalog, the Astronomical Diaries' position records, mathematical "
            "planetary-period astronomy) conceptually separate from Babylonian OMEN "
            "interpretation (Enuma Anu Enlil's protasis-apodosis omens) -- the former is "
            "empirical record-keeping, the latter is the divinatory-interpretive layer "
            "built on top of it, per the spec's explicit instruction to distinguish these.",
        historical_period="Mesopotamia, 2nd-1st millennium BCE.",
        geographic_origin="Mesopotamia",
        confidence_level=EvidenceLevel.ESTABLISHED,
        notes="This distinction is standard in modern historiography of Mesopotamian "
              "science (both astronomy and celestial divination are real, well-attested, "
              "and historically intertwined activities, but analytically separable).",
        computed=False,
    ),
]
