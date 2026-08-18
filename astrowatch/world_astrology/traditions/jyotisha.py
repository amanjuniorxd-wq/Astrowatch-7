"""
Astrowatch World Astrology -- Jyotisha (Indian) tradition module.

DEPTH: the deepest module in this package. Reuses this project's existing,
already-tested Swiss-Ephemeris-backed engine (kundli.py, mahadasha.py,
rashi_nakshatra.py, panchang.py, mundane/entity_chart.py) -- entries marked
computed=True have real, callable code behind them, not just a description.

Parashari Jyotisha is the school actually implemented (whole-sign houses, the
classical 9-graha set, Vimshottari Dasha). Jaimini, Nadi, and Tajika are
DISTINCT, HISTORICALLY DIFFERENT schools with their own techniques (Jaimini uses
different house significators and its own dasha systems entirely, e.g. Chara
Dasha; Nadi traditions use extremely fine-grained divisional charts and a
different textual lineage; Tajika is the Indo-Persian annual-chart school) --
none of those are computed by this project and are listed here as reference-only,
not silently folded into the Parashari entries.
"""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Rashi (zodiac sign)",
        concept="Rashi", definition="The 12 sidereal zodiac signs (Mesha through Meena), "
            "each 30 degrees, used as the base classification for every graha's placement.",
        historical_period="Attested by the early centuries CE (Vedanga Jyotisha predates "
            "the full zodiacal system; the 12-sign sidereal zodiac as used today is "
            "documented from roughly the early centuries CE onward, likely with Hellenistic "
            "cross-influence on the zodiac-as-12-signs concept itself).",
        geographic_origin="Indian subcontinent",
        primary_sources=["Brihat Parashara Hora Shastra (traditional attribution, "
                          "textual date disputed)", "Surya Siddhanta"],
        secondary_sources=["David Pingree, 'Astronomy and Astrology in India and Iran' "
                            "(scholarship on Hellenistic-Indian transmission)"],
        calculation_method="Sidereal ecliptic longitude of a body, divided by 30 degrees, "
            "floor-indexed into 12 signs starting at sidereal Mesha 0 degrees.",
        required_astronomical_inputs=["sidereal ecliptic longitude", "ayanamsha value"],
        prediction_domain=["natal", "mundane", "electional"],
        example="A planet at sidereal longitude 95 degrees is in Karka (Cancer), the 4th sign.",
        confidence_level=EvidenceLevel.ESTABLISHED,
        historical_evidence="The 12-sign sidereal zodiac and Rashi system are universally "
            "used across all later Jyotisha schools; not in scholarly dispute as a live "
            "practice, though its precise historical origin/transmission is.",
        cross_tradition_relationships=["hellenistic:zodiac_signs", "western:zodiac_signs"],
        limitations="This project uses Lahiri ayanamsha specifically -- a real, documented "
            "but NOT the only sidereal ayanamsha in use (Raman, KP, Yukteshwar, etc. all "
            "differ by arcminutes to over a degree). Rashi assignments near a sign boundary "
            "can differ between ayanamshas.",
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Nakshatra",
        concept="Nakshatra", definition="27 lunar mansions of 13d20' each, dividing the "
            "sidereal ecliptic; each has a name, presiding deity, and (per Parashari usage) "
            "a Vimshottari Dasha starting-lord assignment.",
        historical_period="Attested from the Vedic period (lists of Nakshatra names appear "
            "in the Atharvaveda/Taittiriya Samhita), predating the 12-Rashi zodiac.",
        geographic_origin="Indian subcontinent",
        primary_sources=["Taittiriya Samhita", "Brihat Parashara Hora Shastra"],
        calculation_method="Sidereal longitude divided by 13.3333 degrees; each Nakshatra "
            "further split into 4 Padas of 3d20' each.",
        required_astronomical_inputs=["sidereal ecliptic longitude", "ayanamsha value"],
        prediction_domain=["natal", "mundane", "muhurta"],
        example="Moon at sidereal 210 degrees falls in Vishakha (16th Nakshatra).",
        confidence_level=EvidenceLevel.ESTABLISHED,
        historical_evidence="Nakshatra names/order are consistent across the whole "
            "Jyotisha corpus; independently attested from Vedic-era texts.",
        cross_tradition_relationships=["chinese:xiu_lunar_mansions",
                                        "babylonian:path_of_the_moon_stars",
                                        "persian_islamic:manazil_al_qamar"],
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Graha (planet)",
        concept="Graha", definition="The 9 classical 'planets': Surya (Sun), Chandra (Moon), "
            "Mangala (Mars), Budha (Mercury), Guru (Jupiter), Shukra (Venus), Shani (Saturn), "
            "plus the two lunar nodes Rahu and Ketu (not physical bodies).",
        historical_period="Navagraha system attested by early centuries CE.",
        geographic_origin="Indian subcontinent",
        calculation_method="Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn via direct Swiss "
            "Ephemeris calc_ut (FLG_SWIEPH|FLG_SIDEREAL); Rahu via mean lunar node "
            "(swe.MEAN_NODE, a documented, non-default convention choice -- see kundli.py); "
            "Ketu = Rahu + 180 degrees exactly, by definition.",
        required_astronomical_inputs=["Julian Day (UT)", "ephemeris data files"],
        prediction_domain=["natal", "mundane"],
        example="See kundli.py compute_kundli() -- computed for every chart this project builds.",
        confidence_level=EvidenceLevel.ESTABLISHED,
        historical_evidence="Universal across Jyotisha; the mean-vs-true-node choice for "
            "Rahu/Ketu is a real, disclosed methodological choice, not disputed history.",
        cross_tradition_relationships=["hellenistic:seven_classical_planets",
                                        "babylonian:planetary_observations"],
        limitations="Uranus/Neptune/Pluto have NO place in classical Jyotisha and are "
            "correctly not computed here for natal Jyotisha readings.",
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Bhava (house, whole-sign)",
        concept="Bhava", definition="The 12 houses of life-areas, assigned whole-sign from "
            "the Ascendant (Lagna) -- house 1 is the Ascendant's own sign, house 2 the next "
            "sign, etc. (Parashari's dominant convention; other house systems exist in other "
            "schools/later commentaries but are not used by this project).",
        historical_period="Attested alongside the Rashi system, early centuries CE onward.",
        geographic_origin="Indian subcontinent",
        calculation_method="((graha_rashi_index - ascendant_rashi_index) mod 12) + 1.",
        required_astronomical_inputs=["Ascendant sidereal longitude/sign", "graha sidereal sign"],
        prediction_domain=["natal", "mundane"],
        confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["hellenistic:whole_sign_houses"],
        historical_evidence="Whole-sign houses are the house system explicitly described "
            "in Brihat Parashara Hora Shastra and used throughout classical Jyotisha.",
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Vimshottari Dasha",
        concept="Mahadasha / Antardasha", definition="A fixed 120-year cycle split across "
            "9 planetary lords in a fixed order and fixed year-lengths, entered based on the "
            "Moon's Nakshatra at the reference moment (birth, or per this project's mundane-"
            "astrology extension, any entity's real inception moment); each Mahadasha "
            "sub-divides proportionally into 9 Antardashas.",
        historical_period="The dominant, most widely used Dasha system in Jyotisha; textual "
            "attribution to Brihat Parashara Hora Shastra, precise historical dating disputed "
            "by scholars (the surviving text's date is debated, likely with later strata).",
        geographic_origin="Indian subcontinent",
        primary_sources=["Brihat Parashara Hora Shastra"],
        calculation_method="See mahadasha.py -- exact, deterministic arithmetic given a "
            "Moon sidereal longitude and reference Julian Day; no approximation involved.",
        required_astronomical_inputs=["Moon sidereal longitude at the reference instant"],
        prediction_domain=["natal", "mundane"],
        example="See US_MIDTERMS_2026_ASTROLOGICAL_CALCULATION.md and "
                "NATIONS_MAHADASHA_PATTERN_REPORT.md for real applied examples this project "
                "already produced.",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        historical_evidence="Universally used across modern Jyotisha practice; its "
            "PREDICTIVE VALIDITY (as opposed to its mathematical definition) is exactly what "
            "ASTROWATCH-BT-001 tested and found no significant edge for at n=519 events.",
        cross_tradition_relationships=["hellenistic:planetary_periods_firdaria",
                                        "persian_islamic:planetary_periods"],
        limitations="Other historically documented Dasha systems (Yogini Dasha -- which "
            "this project DOES separately compute in the Kundli Studio webapp/mac app, "
            "Ashtottari, Kalachakra, Jaimini's Chara Dasha, and others) exist and are used "
            "by different sub-traditions/for different chart conditions; Vimshottari is not "
            "universally the 'correct' choice, just the most common one.",
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Yogini Dasha",
        concept="Yogini Dasha", definition="An 8-fold, 36-year cyclical Dasha system, "
            "starting lord determined by (Nakshatra_number + 3) mod 8.",
        historical_period="Classical source cited in this project's own implementation "
            "work as the Devi Bhagavata; independently corroborated this session against "
            "multiple concurring modern reference sources.",
        geographic_origin="Indian subcontinent",
        calculation_method="See astrowatch_kundli_studio.html's yogini.js -- verified this "
            "project's own implementation session.",
        prediction_domain=["natal"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        computed=True,
        notes="Computed in the browser/desktop Kundli Studio apps, not yet ported to the "
              "Python backend used by this world_astrology package's reading engine.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Panchanga -- Tithi",
        concept="Tithi", definition="Lunar day: floor((Moon-Sun tropical longitude "
            "difference mod 360)/12) + 1, giving 30 tithis per synodic month.",
        historical_period="Vedic-era calendrical concept.", geographic_origin="Indian subcontinent",
        calculation_method="See panchang.py compute_tithi() -- exact formula, no approximation.",
        prediction_domain=["muhurta", "mundane"],
        confidence_level=EvidenceLevel.ESTABLISHED, computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Panchanga -- Vara",
        concept="Vara", definition="The weekday, one of the 5 traditional Panchanga limbs.",
        historical_period="Vedic-era onward.", geographic_origin="Indian subcontinent",
        calculation_method="See panchang.py compute_vara() -- direct Julian Day arithmetic.",
        prediction_domain=["muhurta", "mundane"],
        confidence_level=EvidenceLevel.ESTABLISHED, computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Panchanga -- Yoga / Karana",
        concept="Yoga and Karana", definition="The remaining 2 of the 5 traditional "
            "Panchanga limbs -- Yoga from the sum of Sun+Moon sidereal longitude binned "
            "into 27; Karana as a half-tithi with 11 named units in a repeating pattern "
            "with named exceptions.",
        historical_period="Vedic-era onward.", geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        computed=False,
        limitations="Explicitly NOT implemented in this project's Python backend (see "
            "panchang.py's own docstring) -- the exact traditional binning/naming "
            "convention for Yoga and the named-exception pattern for Karana were not "
            "researched carefully enough to compute correctly rather than guessed at.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Planetary dignity",
        concept="Uchcha / Neecha / Swakshetra (exaltation/debilitation/own-sign)",
        definition="Each classical graha has one exaltation sign, one debilitation sign "
            "(180 degrees apart), and one or two own signs; placement in these signs is "
            "read as strengthening or weakening that graha's results.",
        historical_period="Attested in Brihat Parashara Hora Shastra and used throughout "
            "classical and modern Jyotisha.",
        geographic_origin="Indian subcontinent",
        calculation_method="Sign-level only in this project (not degree-exact "
            "moolatrikona ranges) -- see the EXALTATION_SIGN/DEBILITATION_SIGN/OWN_SIGNS "
            "tables built and used in analyze_chart_archetypes.py and "
            "analyze_midterms_2026.py this session.",
        prediction_domain=["natal", "mundane"],
        example="Republican Party chart: Moon and Jupiter both DEBILITATED -- see "
                "US_MIDTERMS_2026_ASTROLOGICAL_CALCULATION.md.",
        confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["hellenistic:essential_dignity"],
        computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Retrograde motion (Vakri)",
        concept="Vakri", definition="A graha's apparent backward motion as seen from Earth; "
            "read in Jyotisha as intensifying or complicating that graha's significations.",
        historical_period="Attested in classical Jyotisha.", geographic_origin="Indian subcontinent",
        calculation_method="Direct from Swiss Ephemeris's returned longitudinal speed "
            "(negative = retrograde) -- see kundli.py's GrahaPlacement.retrograde field.",
        prediction_domain=["natal", "mundane"],
        confidence_level=EvidenceLevel.ESTABLISHED, computed=True,
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Parashari", technique="Combustion (Asta)",
        concept="Asta", definition="A planet is read as weakened when within a certain "
            "angular distance of the Sun (the exact orb varies by planet and by text).",
        historical_period="Attested in classical Jyotisha.", geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM, computed=False,
        limitations="NOT implemented in this project -- the orb table (which differs by "
            "planet, and by direct/retrograde motion in some texts) was not researched "
            "this session; do not assume any chart output here reflects combustion.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Varga (divisional charts)",
        concept="Navamsa (D9) and other Vargas", definition="Additional charts derived by "
            "subdividing each sign into smaller segments (Navamsa = ninths) for finer-grained "
            "reading of specific life areas (Navamsa traditionally for marriage/dharma).",
        historical_period="Attested in Brihat Parashara Hora Shastra (16-varga system).",
        geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM, computed=False,
        limitations="NOT implemented anywhere in this project (browser app, desktop app, "
            "or Python backend) -- every chart this project has ever produced is the D1 "
            "(Rashi) chart only.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Jaimini", technique="Jaimini Astrology (overview)",
        concept="Jaimini system", definition="A historically distinct Jyotisha school "
            "attributed to sage Jaimini, using different house-significator rules "
            "(Karakas), its own house-based (not planet-based) aspect rules, and its own "
            "Dasha systems (e.g. Chara Dasha, sign-based).",
        historical_period="Textual tradition (Jaimini Sutras) of disputed precise date.",
        geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM, computed=False,
        limitations="Reference-only in this project. Genuinely distinct from Parashari -- "
            "not interchangeable, not computed, no Jaimini-specific output exists anywhere "
            "in this codebase.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Nadi", technique="Nadi Astrology (overview)",
        concept="Nadi tradition", definition="A family of Jyotisha traditions (e.g. "
            "Bhrigu Nadi, Chandra Nadi) using extremely fine-grained divisional charts and "
            "a distinct textual/oral lineage, often associated with claims of pre-written "
            "individual leaf readings.",
        historical_period="Traditional lineage claims vary widely in verifiability.",
        geographic_origin="South India (predominantly Tamil Nadu tradition)",
        confidence_level=EvidenceLevel.SCHOLARLY_DISPUTED, computed=False,
        limitations="Reference-only; NOT computed. Some Nadi lineage claims (e.g. "
            "individually pre-written leaves) are treated by mainstream historians as "
            "unverifiable/traditional claims rather than established history -- this "
            "project does not adjudicate that dispute, only flags it.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="Tajika", technique="Tajika Astrology (overview)",
        concept="Tajika system", definition="An Indo-Persian annual-chart (Varshaphal) "
            "school incorporating Perso-Arabic techniques (e.g. Sahams/Arabic-Parts-like "
            "points) into a Jyotisha framework, historically resulting from the same "
            "Indian-Islamic astrological transmission covered in the Persian/Islamic module.",
        historical_period="Developed following Indo-Islamic contact, roughly 2nd millennium CE.",
        geographic_origin="Indian subcontinent (Persian-influenced)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        cross_tradition_relationships=["persian_islamic:annual_revolutions"],
        limitations="This project DOES compute a basic solar-return/Varshaphal chart "
            "(Muntha, solar-return Ascendant -- see varshaphal.js in Kundli Studio) but "
            "does NOT implement the specific Tajika Sahams/annual-lord techniques that "
            "distinguish the Tajika school from a generic solar return.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Prashna (horary astrology)",
        concept="Prashna", definition="Answering a specific question via a chart cast for "
            "the moment the question is asked/received, rather than a birth moment.",
        historical_period="Attested across classical Jyotisha.", geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["horary"],
        limitations="Not implemented as a distinct mode -- this project's engine could "
            "technically compute a chart for 'now', but no Prashna-specific interpretation "
            "rules (which differ from natal rules) are encoded anywhere.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Muhurta (electional astrology)",
        concept="Muhurta", definition="Selecting an auspicious date/time to begin an "
            "undertaking, based on Panchanga and other classical criteria.",
        historical_period="Attested across classical Jyotisha; dedicated Muhurta texts exist.",
        geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["electional"],
        limitations="Not implemented -- no Muhurta rule-set is encoded in this project.",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Samhita (mundane astrology)",
        concept="Samhita literature", definition="The classical Jyotisha genre covering "
            "mundane/collective astrology -- omens, weather, agriculture, royal/political "
            "matters, war -- as opposed to individual natal astrology.",
        historical_period="Brihat Samhita (Varahamihira, 6th century CE) is the major "
            "surviving example.",
        geographic_origin="Indian subcontinent",
        primary_sources=["Brihat Samhita (Varahamihira)"],
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED, computed=False,
        prediction_domain=["mundane"],
        cross_tradition_relationships=["babylonian:royal_political_omens"],
        notes="This project's rule_registry.py already has REAL, cited rules extracted "
              "directly from N. Chidambaram Iyer's 1884 Brihat Samhita translation "
              "(chapters 16-20, 42) -- see that file for the actual machine-usable rule "
              "set (conjunction/defeat triggers, geography, timing, interpretation), not "
              "duplicated here.",
        limitations="Only a subset of Brihat Samhita's chapters have been extracted into "
            "machine rules (see rule_registry.py's COVERAGE dict for exactly which).",
    ),
    KnowledgeEntry(
        tradition="jyotisha", school="", technique="Shakuna / Nimitta (omens)",
        concept="Shakuna", definition="Interpretation of incidental omens (animal/bird "
            "behavior, physical events, chance occurrences) as predictive signs, a genre "
            "adjacent to but distinct from planetary/chart-based astrology.",
        historical_period="Attested in classical Indian omen literature.",
        geographic_origin="Indian subcontinent",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM, computed=False,
        limitations="Reference-only; not astronomical, not computed, no rules encoded.",
    ),
]
