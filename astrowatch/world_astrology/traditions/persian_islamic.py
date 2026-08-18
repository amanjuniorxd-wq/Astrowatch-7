"""Astrowatch World Astrology -- Persian / Islamic (medieval Arabic) astrology
module. SEED-LEVEL. NO computational engine specific to this tradition (this
project's Varshaphal/solar-return computation is labeled under Jyotisha/Tajika,
not duplicated here)."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Greek-to-Arabic transmission",
        concept="Translation movement", definition="The systematic translation of "
            "Hellenistic (and some Indian and Persian/Pahlavi) astrological and "
            "astronomical texts into Arabic, centered on Baghdad's House of Wisdom "
            "and related institutions, forming the textual basis of Islamic Golden Age "
            "astrology.",
        historical_period="c. 8th-10th century CE", geographic_origin="Abbasid Caliphate "
            "(Baghdad and other centers)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["hellenistic:whole_sign_houses", "western:medieval_astrology"],
        historical_evidence="Well-established in mainstream history-of-science "
            "scholarship; the general pattern (not every specific translator/date) is "
            "not in serious dispute.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Indian-to-Islamic transmission",
        concept="Indian astronomical/astrological influence", definition="Alongside Greek "
            "material, Indian astronomical texts (via Sanskrit-to-Arabic/Pahlavi routes, "
            "notably associated with the transmission of works in the Sindhind tradition) "
            "also fed into early Islamic astronomy/astrology.",
        historical_period="c. 8th century CE onward", geographic_origin="Transmitted from "
            "the Indian subcontinent into the early Abbasid world",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:rashi"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Abu Ma'shar al-Balkhi (Albumasar)",
        concept="Abu Ma'shar al-Balkhi", definition="A major 9th-century Persian "
            "astrologer, best known in the Latin West as 'Albumasar'; author of works on "
            "general astrology and, notably, on the theory of historical/political cycles "
            "tied to great planetary conjunctions.",
        historical_period="c. 787-886 CE", geographic_origin="Balkh (in modern Afghanistan) "
            "/ Baghdad",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        primary_sources=["Abu Ma'shar, Kitab al-Madkhal al-Kabir (Great Introduction to Astrology)"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Al-Biruni",
        concept="Al-Biruni", definition="An 11th-century Khwarazmian "
            "polymath who wrote extensively on astronomy, mathematics, and astrology, "
            "including a systematic instructional text on astrology.",
        historical_period="973-c. 1050 CE", geographic_origin="Khwarazm (Central Asia)",
        primary_sources=["Al-Biruni, Kitab al-Tafhim li-Awa'il Sina'at al-Tanjim "
                          "(The Book of Instruction in the Elements of the Art of Astrology)"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Masha'allah ibn Athari",
        concept="Masha'allah ibn Athari", definition="An early Islamic-era astrologer "
            "(of Jewish-Persian background) active in 8th-century Baghdad, traditionally "
            "associated (per later tradition) with the astrological election used for the "
            "founding of Baghdad, among other works.",
        historical_period="c. 740-815 CE", geographic_origin="Basra / Baghdad",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        limitations="The specific claim that Masha'allah personally cast the founding "
            "chart of Baghdad is a traditional attribution repeated in later sources, "
            "not independently re-verified against primary evidence this session -- "
            "marked accordingly rather than stated as settled fact.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Great Conjunction theory",
        concept="Great Conjunctions (Jupiter-Saturn cycles)", definition="A historical/"
            "political-astrology framework (most associated with Abu Ma'shar) reading "
            "the roughly 20-year Jupiter-Saturn conjunction cycle, and its longer "
            "sign-triplicity-shifting cycle (roughly every ~200 and ~800 years), as "
            "governing large-scale historical change, dynasties, and religions.",
        historical_period="Systematized in the 9th century CE (Abu Ma'shar), though the "
            "underlying observation that Jupiter-Saturn conjunctions cycle through "
            "zodiacal triplicities is much older (traceable to Hellenistic and earlier "
            "sources).",
        geographic_origin="Islamic Golden Age (Persian/Abbasid)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        prediction_domain=["mundane"],
        computed=False,
        limitations="NOT implemented computationally in this project -- no Jupiter-"
            "Saturn conjunction cycle tracker exists in this codebase.",
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="Tajika-adjacent", technique="Annual revolutions",
        concept="Tahwil al-sana / annual revolution", definition="A solar-return-based "
            "annual chart technique used in Persian/Islamic astrology for yearly "
            "predictions -- historically the direct ancestor of Jyotisha's Tajika/"
            "Varshaphal school (see that module).",
        historical_period="Islamic Golden Age.", geographic_origin="Persian/Islamic world",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:tajika_system", "western:solar_lunar_returns"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="persian_islamic", school="", technique="Sahams (Arabic Parts)",
        concept="Sahams / Arabic Parts", definition="Calculated sensitive points "
            "(structurally the same concept as Hellenistic Lots), used extensively in "
            "Persian/Islamic and Tajika astrology.",
        historical_period="Islamic Golden Age, inherited from Hellenistic Lots.",
        geographic_origin="Persian/Islamic world",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["hellenistic:lots_arabic_parts"],
        computed=False,
    ),
]
