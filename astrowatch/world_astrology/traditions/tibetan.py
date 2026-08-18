"""Astrowatch World Astrology -- Tibetan astrology module (SEED-LEVEL, reference
only, no computation). Tibetan astrology (Kartsi/Nagtsi complex) is itself a
composite of Indian (Kalachakra-derived) and Chinese (Bon/elemental-divination)
strands -- this module intentionally keeps entries narrow and well-sourced rather
than attempting a synthetic overview."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="tibetan", school="Kalachakra (shared root)",
        technique="White/Elemental astrology divide",
        concept="Kartsi and Nagtsi", definition="Tibetan astrology is traditionally "
            "divided into 'Kartsi' (white/celestial calculation, derived from the "
            "Kalachakra Tantra's Indian-origin astronomical/astrological system) and "
            "'Nagtsi' (black/elemental calculation, derived from Chinese-origin "
            "elemental and divinatory systems, sometimes linked to Bon tradition). "
            "The two strands are used together in practice (e.g. for a full natal "
            "reading or for determining an auspicious date).",
        historical_period="Kalachakra Tantra transmitted to Tibet by the 11th century CE; "
            "elemental/Nagtsi strand's Chinese-linked origins are older by local tradition "
            "but precise dating is less firmly established in Western scholarship.",
        geographic_origin="Tibet (via India for Kartsi, via China/Bon for Nagtsi)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:kalachakra_root", "chinese:wu_xing_five_elements"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="tibetan", school="Tsurphu (Tsur-luk)",
        technique="Tsur-luk calculation lineage",
        concept="Tsurphu (Karma Kagyu) astrological lineage", definition="One of the two "
            "major living Tibetan calculation systems, founded by the 3rd Karmapa "
            "Rangjung Dorje (1284-1339) and further developed by Pawo Tsuklak Trengwa "
            "(1504-1566); still used within Karmapa/Karma Kagyu monastic institutions. "
            "Uses a distinct ('precise') system for Sun/Moon longitude calculation and "
            "the full traditional system for the other planets.",
        historical_period="14th century founding, 16th century further systematization.",
        geographic_origin="Tibet (Tsurphu Monastery / Karma Kagyu lineage)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        secondary_sources=["Web-verified via general reference search, 2026 session; "
            "not independently cross-checked against a primary Tibetan-language source"],
        computed=False,
        limitations="Reference fact only -- no calculation engine of any kind implemented; "
            "verified via a single round of web research this session, not a primary source.",
    ),
    KnowledgeEntry(
        tradition="tibetan", school="Phugpa (Phug-luk)",
        technique="Phug-luk calculation lineage",
        concept="Phugpa astrological lineage", definition="The second major living "
            "Tibetan calculation system, founded by Phugpa Lhundrub Gyatso (15th century) "
            "and Norzang Gyatso (1423-1513), developed specifically to reconcile "
            "discrepancies between the Kalachakra's Indian-derived solar-longitude "
            "calculations and observed positions in Tibet. This is the lineage "
            "officially used by the institution of the Dalai Lama.",
        historical_period="15th-16th century.", geographic_origin="Tibet",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        secondary_sources=["Web-verified via general reference search, 2026 session"],
        computed=False,
        cross_tradition_relationships=["jyotisha:kalachakra_root"],
        notes="Phugpa and Tsurphu differ in solar/lunar calculation precision and in "
              "seasonal/month-numbering conventions -- they are two calculation "
              "traditions within one broader system, not two unrelated traditions; "
              "marked PARTIAL_CORRESPONDENCE to each other in cross_tradition.py, "
              "not INDEPENDENT_DEVELOPMENT.",
    ),
    KnowledgeEntry(
        tradition="tibetan", school="", technique="Tibetan animal-element year cycle",
        concept="60-year Rabjung cycle", definition="A 60-year cycle combining 12 animals "
            "(shared naming with the Chinese zodiac) with 5 elements (Wood, Fire, Earth, "
            "Iron/Metal, Water), each element spanning 2 consecutive years (one 'male,' "
            "one 'female'), used for both yearly designation and natal-year assignment.",
        historical_period="Tied to the Kalachakra's introduction (11th century) and its "
            "own Rabjung ('fine grade') 60-year count starting 1027 CE.",
        geographic_origin="Tibet", confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["chinese:heavenly_stems_earthly_branches",
                                        "chinese:chinese_zodiac"],
        notes="Structurally a clear HISTORICAL_INFLUENCE relationship from the Chinese "
              "sexagenary/zodiac system (shared animal names, 60-term cycle length), "
              "adapted into a distinct Tibetan epoch (Rabjung, starting 1027 CE) and "
              "combined with the Kalachakra's own elemental framework rather than "
              "China's Wu Xing generative/controlling cycle logic directly.",
        computed=False,
    ),
    KnowledgeEntry(
        tradition="tibetan", school="", technique="Mewa and Parkha (Nagtsi elements)",
        concept="Mewa (9 magic numbers) and Parkha (8 trigrams)", definition="Elemental-"
            "divinatory tools used in the Nagtsi strand: 9 numbered 'Mewa' and 8 'Parkha' "
            "trigrams (structurally related to the Chinese Bagua/I Ching trigram system), "
            "combined with birth-year animal/element data for compatibility and "
            "life-event timing analysis.",
        historical_period="Associated with the Nagtsi/elemental strand's Chinese-linked "
            "origins; precise dating not independently verified this session.",
        geographic_origin="Tibet (via Chinese-linked transmission)",
        confidence_level=EvidenceLevel.TRADITIONAL_CLAIM,
        cross_tradition_relationships=["chinese:yin_yang"],
        computed=False,
        limitations="Seed-level, unverified beyond general reference-level description; "
            "no primary source consulted this session.",
    ),
]
