"""
Astrowatch World Astrology -- cross-tradition relationship engine.

Two different things live in this module and they must not be confused:

1. CROSS_TRADITION_RELATIONSHIPS -- a small, curated, hand-reviewed list of
   CrossTraditionRelationship records below. Each one names two REAL,
   REGISTERED KnowledgeEntry ids (validated against the live registry by
   validate_relationships()) and classifies how they relate using
   RelationshipType. This list is the only place this project formally
   asserts that two traditions' concepts relate in a specific, defensible
   way, and every record carries a `reasoning` string explaining *why* that
   specific classification (not a stronger one) was chosen.

   The governing rule, repeated because it is the whole point of this module:
   superficial similarity (same number of divisions, same general topic,
   "both use planets") is NEVER enough on its own for anything stronger than
   FUNCTIONAL_ANALOGY. DIRECT_CORRESPONDENCE and HISTORICAL_INFLUENCE are only
   used where a documented transmission chain, shared terminology of common
   origin, or explicit scholarly consensus supports it -- and even then the
   reasoning field says what that evidence actually is, not just "obviously."

2. Every individual KnowledgeEntry (in traditions/*.py) also carries its own
   free-text `cross_tradition_relationships` list -- informal notes written
   while researching that specific entry, meant for a human reader, NOT a
   resolved foreign key into the registry. Several of those hints point at
   concepts this project only ever describes in prose (e.g. "the Babylonian
   origin of the 12-sign zodiac" is mentioned in multiple entries' notes, but
   no babylonian.py entry with its own KnowledgeEntry id was written for it).
   unresolved_hint_references() below finds every such dangling hint and
   reports it explicitly, rather than letting the gap pass silently -- this is
   a known, disclosed limitation of the current content, not a bug to hide.
"""
from dataclasses import dataclass
from typing import List

from .schema import RelationshipType, EvidenceLevel, TraditionRegistry


@dataclass
class CrossTraditionRelationship:
    entry_id_a: str
    entry_id_b: str
    relationship_type: RelationshipType
    reasoning: str                        # why THIS classification, not a stronger one
    evidence_level: EvidenceLevel = EvidenceLevel.HISTORICALLY_DOCUMENTED
    scholarly_notes: str = ""             # caveats, live scholarly debate, etc.


CROSS_TRADITION_RELATIONSHIPS: List[CrossTraditionRelationship] = [
    CrossTraditionRelationship(
        entry_id_a="hellenistic:lots",
        entry_id_b="persian_islamic:sahams_/_arabic_parts",
        relationship_type=RelationshipType.DIRECT_CORRESPONDENCE,
        reasoning="Arabic 'Saham' (pl. Sahams, Latinized as Pars/Parts) is a literal "
            "terminological and technical continuation of the Hellenistic Lot (kleros) "
            "system -- the calculation formulas (day/night variants of the Lot of "
            "Fortune, etc.) and the underlying concept were transmitted essentially "
            "intact via Persian Pahlavi intermediary sources into Arabic astrology, not "
            "independently reinvented. This is one of the best-documented cases of "
            "direct technical continuity across these traditions.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="persian_islamic:translation_movement",
        entry_id_b="western:medieval_western_astrology",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="The 12th-century Latin translation movement (Toledo school and "
            "others) took Arabic astrological texts -- themselves already syntheses of "
            "Hellenistic, Persian, and Indian material -- directly into Latin, shaping "
            "medieval Western astrology's technical vocabulary and available "
            "techniques. Documented via named translators (e.g. John of Seville, "
            "Hermann of Carinthia) and surviving Latin translations of named Arabic "
            "authors also catalogued in this system (Abu Ma'shar, al-Biruni).",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="persian_islamic:tahwil_al-sana_/_annual_revolution",
        entry_id_b="western:solar_and_lunar_returns",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="The modern Western 'solar return' technique is substantively the "
            "same core method (a chart cast for the moment the Sun returns to its "
            "natal longitude) as the medieval Islamic tahwil al-sana, transmitted via "
            "the same translation-movement channel documented above -- not an "
            "independent modern invention, though modern Western practice has since "
            "developed its own interpretive conventions layered on top of the shared core.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="persian_islamic:indian_astronomical/astrological_influence",
        entry_id_b="jyotisha:rashi",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="Early Abbasid-era astrology/astronomy (8th century Baghdad) drew "
            "documented influence from Sanskrit astronomical texts (e.g. via the "
            "Zij al-Sindhind), alongside its larger Hellenistic/Persian inheritance -- "
            "a real but partial channel of influence, not the dominant one, which is "
            "why this is marked HISTORICAL_INFLUENCE rather than a stronger category.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="jyotisha:mahadasha_/_antardasha",
        entry_id_b="hellenistic:zodiacal_releasing",
        relationship_type=RelationshipType.FUNCTIONAL_ANALOGY,
        reasoning="Both are 'time-lord' techniques that assign rulership of "
            "sequential life periods to planets for timing predictions -- but the "
            "mechanics are genuinely different (Vimshottari Dasha: a fixed 120-year "
            "sequence with fixed per-planet year-lengths keyed to natal Moon's "
            "Nakshatra; Zodiacal Releasing: a sign-based, Lot-of-Fortune/Spirit-driven "
            "branching L1-L4 period structure of variable length). No documented "
            "textual transmission links the two systems to each other specifically; "
            "the resemblance is in *purpose* (life-period timing via planetary rulers), "
            "not in shared method or origin, which is exactly what FUNCTIONAL_ANALOGY "
            "(as opposed to PARTIAL_CORRESPONDENCE) is for.",
        evidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        scholarly_notes="Some historians of astrology argue both ultimately draw on a "
            "shared, older Hellenistic-Babylonian planetary-period concept that reached "
            "India and was reworked there independently of what became Hellenistic "
            "releasing; this is a live, unsettled question, not treated as resolved here.",
    ),
    CrossTraditionRelationship(
        entry_id_a="jyotisha:uchcha_/_neecha_/_swakshetra_(exaltation/debilitation/own-sign)",
        entry_id_b="hellenistic:essential_dignity",
        relationship_type=RelationshipType.PARTIAL_CORRESPONDENCE,
        reasoning="Both systems assign planets sign-based 'strength' states "
            "(exaltation, debilitation/detriment, own sign/domicile) using overlapping "
            "but not identical sign assignments and different additional layers "
            "(Hellenistic dignity also scores triplicity/term/face; Jyotisha adds "
            "moolatrikona and divisional-chart dignity). The core exaltation/"
            "debilitation degree list for several planets is close enough between the "
            "two traditions that a shared ancient (likely Babylonian-linked) source is "
            "plausible, but this project has not independently verified a full "
            "degree-by-degree match this session, so PARTIAL_CORRESPONDENCE (not "
            "DIRECT_CORRESPONDENCE) is used.",
        evidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        scholarly_notes="The question of a common Hellenistic-Babylonian source for "
            "the exaltation degrees used in both Jyotisha and Hellenistic astrology is "
            "discussed in the history-of-astrology literature but is not settled "
            "consensus; treated cautiously here.",
    ),
    CrossTraditionRelationship(
        entry_id_a="jyotisha:nakshatra",
        entry_id_b="chinese:xiu_(lunar_mansions)",
        relationship_type=RelationshipType.PARTIAL_CORRESPONDENCE,
        reasoning="Both are systems of ~27-28 unequal sky divisions used for "
            "calendrical/astrological timing tied to the Moon's motion, and both "
            "predate clear evidence of contact between the two regions by the time "
            "of their earliest attestation -- whether they share a common ancient "
            "origin (a once-popular 'lunar zodiac' diffusion hypothesis) or developed "
            "independently is a genuinely disputed question among historians of "
            "astronomy, not a settled DIRECT_CORRESPONDENCE.",
        evidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        scholarly_notes="The 'common origin vs. independent invention' debate for "
            "Nakshatras, Xiu, and the Arabic Manazil al-Qamar is a long-standing, "
            "unresolved topic in comparative history of astronomy; this project takes "
            "no side and reports the dispute rather than a conclusion.",
    ),
    CrossTraditionRelationship(
        entry_id_a="chinese:xiu_(lunar_mansions)",
        entry_id_b="japanese:shukuyodo_(lunar-mansion_astrology)",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="Shukuyodo is documented as reaching Japan through Chinese Buddhist "
            "translation/transmission (notably associated with the monk Kukai, "
            "9th century), carrying the lunar-mansion concept onward -- but Shukuyodo's "
            "own mansion count/terminology descends most directly from the Indian "
            "Nakshatra concept AS FILTERED through Chinese Buddhist texts, not as a "
            "separate borrowing straight from the native Chinese Xiu system, so this is "
            "marked as influence via a shared transmission channel, not a claim that "
            "Xiu and Shukuyodo are the same system.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="jyotisha:nakshatra",
        entry_id_b="japanese:shukuyodo_(lunar-mansion_astrology)",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="A documented chained transmission: the Indian Nakshatra concept "
            "passed into Chinese Buddhist astrological/astronomical texts, which were "
            "then carried to Japan and adapted into Shukuyodo. This is HISTORICAL_"
            "INFLUENCE across two transmission hops, explicitly not DIRECT_"
            "CORRESPONDENCE, since centuries of independent Chinese Buddhist "
            "reinterpretation separate the Indian source from the Japanese result.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="chinese:yin-yang",
        entry_id_b="japanese:onmyodo_(the_way_of_yin_and_yang)",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="Onmyodo is Japan's direct historical adaptation of Chinese Yin-Yang "
            "cosmology (its very name, 'onmyo,' is the Japanese reading of the same "
            "characters as 'yin-yang'), formalized as a Japanese court bureau (the "
            "Onmyoryo) from the late 7th century CE under the Ritsuryo legal system -- "
            "a clear, well-documented transmission, not independent development.",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="chinese:wu_xing",
        entry_id_b="japanese:gogyo",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="Gogyo is the direct Japanese transmission of the Chinese Wu Xing "
            "five-element framework (again, the same characters, Japanese reading), "
            "carried into Japan alongside Onmyodo's formalization.",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="chinese:qi_men_dun_jia",
        entry_id_b="japanese:kyusei_nine_star_ki",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="Nine Star Ki's 9-number/Bagua-grid structure is historically and "
            "conceptually rooted in the same Chinese numerological/Bagua-based "
            "divinatory tradition family as Qi Men Dun Jia (both use a 3x3 Magic "
            "Square/Later Heaven Bagua arrangement and Wu Xing element assignment), "
            "though Nine Star Ki as practiced in modern Japan is a distinct, later "
            "popularized system, not identical in method to Qi Men Dun Jia -- so this "
            "is influence from a shared root tradition, not correspondence between "
            "the two named systems themselves.",
        evidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        scholarly_notes="The precise lineage connecting historical Chinese Bagua-"
            "based numerology to the specific modern Japanese Kyusei Kigaku system "
            "popularized in the 20th century has not been independently verified "
            "against a primary source this session.",
    ),
    CrossTraditionRelationship(
        entry_id_a="tibetan:60-year_rabjung_cycle",
        entry_id_b="chinese:ganzhi_(stems_and_branches)",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="The Tibetan 60-year animal-element cycle shares the Chinese "
            "system's animal names and 60-term cycle length, indicating clear "
            "historical influence, but Tibet adapted it into its own Rabjung epoch "
            "(beginning 1027 CE, tied to the Kalachakra's introduction) and combined "
            "it with the Kalachakra's elemental framework rather than importing "
            "China's Wu Xing generative/controlling-cycle logic wholesale -- an "
            "adapted borrowing, not an identical system.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="tibetan:60-year_rabjung_cycle",
        entry_id_b="chinese:12_zodiac_animals",
        relationship_type=RelationshipType.HISTORICAL_INFLUENCE,
        reasoning="The 12 animals used in the Tibetan cycle are the same 12 animals "
            "(same names/order) as the Chinese zodiac -- direct borrowing of the "
            "animal-naming layer specifically, distinct from the separately-assessed "
            "influence on the cycle's overall structure above.",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="chinese:12_zodiac_animals",
        entry_id_b="jyotisha:rashi",
        relationship_type=RelationshipType.INDEPENDENT_DEVELOPMENT,
        reasoning="Both are 12-category cyclical symbolic systems applied to time, but "
            "the Chinese 12-animal year cycle and the 12-sign ecliptic zodiac (Rashi, "
            "itself sharing origin with the Babylonian/Hellenistic 12-sign zodiac -- "
            "see notes on jyotisha:rashi) are historically UNRELATED systems that "
            "happen to both use the number 12: one tracks a lunar-linked animal-year "
            "count with no reference to ecliptic star positions, the other divides the "
            "ecliptic itself into 30-degree bands. This pairing is deliberately "
            "included as an explicit negative example -- the kind of superficial "
            "similarity (same number, both called a 'zodiac' in casual English) that "
            "this engine exists specifically to NOT overclaim.",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="egyptian:decans_(36_ten-day_star_groups)",
        entry_id_b="jyotisha:navamsa_(d9)_and_other_vargas",
        relationship_type=RelationshipType.INDEPENDENT_DEVELOPMENT,
        reasoning="Both techniques subdivide zodiacal/stellar space into smaller "
            "symbolic sub-units for added interpretive nuance (Egyptian decans: 3 "
            "roughly-10-degree divisions per 30-degree sign, tied to specific "
            "constellations/deities and originally an independent nighttime-"
            "timekeeping system before later Hellenistic-era zodiac integration; "
            "Jyotisha Navamsa: 9 equal divisions of 3-degree-20-minute each per sign, "
            "an entirely different mathematical scheme with no shared origin or "
            "historical contact documented). Included specifically as a FUNCTIONAL-"
            "level structural analogy that this engine explicitly does NOT upgrade to "
            "any correspondence or influence category, since no transmission evidence "
            "exists connecting the two techniques to each other.",
        evidence_level=EvidenceLevel.ESTABLISHED,
    ),
    CrossTraditionRelationship(
        entry_id_a="egyptian:decans_(36_ten-day_star_groups)",
        entry_id_b="babylonian:star_catalog_/_astronomical_compendium",
        relationship_type=RelationshipType.INDEPENDENT_DEVELOPMENT,
        reasoning="Egyptian decans (attested from Middle Kingdom coffin-lid diagonal "
            "star clocks, c. 2100-1700 BCE) and the Babylonian MUL.APIN star catalog "
            "(compiled later, c. 1000 BCE surviving copies, though it may reflect "
            "older observational material) are both native star-cataloguing/"
            "timekeeping systems that developed within their own civilizations before "
            "the much later Hellenistic-era synthesis that eventually merged decans "
            "into the 12-sign zodiac framework (see the separate egyptian:egyptian_"
            "adoption... entry for that later, well-documented merger). Treated as "
            "independent development at the point of origin, not confused with the "
            "genuine later Hellenistic-era integration.",
        evidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
    ),
    CrossTraditionRelationship(
        entry_id_a="babylonian:royal/political_omen_interpretation",
        entry_id_b="jyotisha:samhita_literature",
        relationship_type=RelationshipType.INDEPENDENT_DEVELOPMENT,
        reasoning="Both are substantial traditions of mundane/political astral omen "
            "literature covering kings, harvests, war, and state affairs (Babylonian: "
            "Enuma Anu Enlil's ~70 tablets of omens; Indian: Samhita literature such as "
            "the Brihat Samhita). Some historians have proposed early Mesopotamian-"
            "Indian astral-omen contact given trade links, but this is a genuinely "
            "disputed and not a mainstream-consensus claim for the omen-literature "
            "content specifically (as opposed to later, better-documented Hellenistic-"
            "into-India transmission of horoscopic astrology itself) -- treated here as "
            "independent development of a similar genre, not asserted transmission.",
        evidence_level=EvidenceLevel.SCHOLARLY_DISPUTED,
        scholarly_notes="Distinguish this cautious call from the much better "
            "documented later transmission of Hellenistic horoscopic techniques into "
            "India (2nd-4th century CE Yavanajataka etc.) -- that later transmission is "
            "a separate, more firmly established topic not asserted by this entry.",
    ),
]


def validate_relationships(registry: TraditionRegistry) -> List[str]:
    """Returns a list of human-readable problem descriptions for any curated
    relationship whose entry_id_a/entry_id_b does not actually exist in the
    given registry. Empty list == every curated relationship is well-formed.
    Call this from a test, not at import time, so a future bad edit fails a
    test loudly instead of crashing unrelated imports."""
    problems = []
    known = set(e.entry_id for e in registry.all())
    seen_pairs = set()
    for rel in CROSS_TRADITION_RELATIONSHIPS:
        if rel.entry_id_a not in known:
            problems.append(f"unknown entry_id_a: {rel.entry_id_a!r}")
        if rel.entry_id_b not in known:
            problems.append(f"unknown entry_id_b: {rel.entry_id_b!r}")
        if rel.entry_id_a == rel.entry_id_b:
            problems.append(f"self-referential relationship: {rel.entry_id_a!r}")
        pair = tuple(sorted([rel.entry_id_a, rel.entry_id_b]))
        if pair in seen_pairs:
            problems.append(f"duplicate relationship pair: {pair}")
        seen_pairs.add(pair)
    return problems


def get_relationships(entry_id: str) -> List[CrossTraditionRelationship]:
    """All curated relationships touching this entry_id, from either side."""
    return [r for r in CROSS_TRADITION_RELATIONSHIPS
            if entry_id in (r.entry_id_a, r.entry_id_b)]


def relationships_between(tradition_a: str, tradition_b: str) -> List[CrossTraditionRelationship]:
    """All curated relationships whose two entries belong one to each of the
    given traditions (order-independent)."""
    out = []
    for r in CROSS_TRADITION_RELATIONSHIPS:
        pref_a, pref_b = r.entry_id_a.split(":", 1)[0], r.entry_id_b.split(":", 1)[0]
        if {pref_a, pref_b} == {tradition_a, tradition_b}:
            out.append(r)
    return out


def unresolved_hint_references(registry: TraditionRegistry) -> List[tuple]:
    """Finds every KnowledgeEntry.cross_tradition_relationships free-text hint
    that does not resolve to a real, registered entry_id. Returns a list of
    (source_entry_id, dangling_hint) tuples. This is NOT an error condition --
    it is a disclosed gap-finder: many hints point at concepts this project
    has described in prose but not yet turned into their own KnowledgeEntry.
    See this module's docstring, part 2, for why that's an intentional,
    tracked limitation rather than a silently swallowed bug."""
    known = set(e.entry_id for e in registry.all())
    unresolved = []
    for e in registry.all():
        for hint in e.cross_tradition_relationships:
            if hint not in known:
                unresolved.append((e.entry_id, hint))
    return unresolved
