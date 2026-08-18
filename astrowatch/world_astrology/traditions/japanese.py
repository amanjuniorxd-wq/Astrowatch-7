"""Astrowatch World Astrology -- Japanese astrology module (SEED-LEVEL, reference
only). Primary content is Onmyodo, Japan's historical yin-yang/five-elements
divinatory system transmitted from China/Korea, plus the still-popular Kyusei
Nine Star Ki system."""
from ..schema import KnowledgeEntry, EvidenceLevel

ENTRIES = [
    KnowledgeEntry(
        tradition="japanese", school="", technique="Onmyodo",
        concept="Onmyodo (the way of Yin and Yang)", definition="Japan's historical "
            "cosmological/divinatory discipline, built on Yin-Yang (Onmyo) and Wu "
            "Xing/Gogyo (Five Elements) theory transmitted from China (via Korea), "
            "combined with native Japanese elements; practiced by a specialized court "
            "bureau (the Onmyoryo) for divination, calendar-making, and ritual timing.",
        historical_period="Formalized as a state bureau (Onmyoryo) under the Ritsuryo "
            "legal system from the late 7th century CE; most famously associated with "
            "the Heian-period onmyoji Abe no Seimei (921-1005 CE).",
        geographic_origin="Japan (via Chinese/Korean transmission)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["chinese:yin_yang", "chinese:wu_xing_five_elements"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="japanese", school="", technique="Gogyo (Five Elements in Japan)",
        concept="Gogyo", definition="The Japanese adaptation of the Chinese Wu Xing "
            "five-element framework (Wood/Moku, Fire/Ka, Earth/Do, Metal/Kin, Water/Sui), "
            "applied within Onmyodo's divinatory and calendrical practice.",
        historical_period="Transmitted alongside Onmyodo's formalization, 7th century CE.",
        geographic_origin="Japan (via China)", confidence_level=EvidenceLevel.ESTABLISHED,
        cross_tradition_relationships=["chinese:wu_xing_five_elements"],
        computed=False,
    ),
    KnowledgeEntry(
        tradition="japanese", school="", technique="Kyusei Kigaku (Nine Star Ki)",
        concept="Kyusei Nine Star Ki", definition="A still-popular natal/fortune system "
            "assigning one of 9 numbered 'stars' by birth year (with a secondary "
            "monthly star), each linked to a Wu-Xing element and a position in a "
            "3x3 Magic-Square-like grid (Ki-mon/Later Heaven Bagua arrangement) used to "
            "analyze yearly/directional fortune -- historically and structurally related "
            "to the Chinese Qi Men Dun Jia / Feng Shui Flying Star traditions.",
        historical_period="Popularized in Japan in the modern era (20th century), "
            "though its numerological/Bagua-grid roots are much older Chinese concepts.",
        geographic_origin="Japan (via Chinese-origin concepts)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["chinese:qi_men_dun_jia"],
        computed=False,
        limitations="Reference-only; no computation of a person's star number "
            "implemented (it requires a specific year-boundary convention -- Nine Star "
            "Ki years do not switch on Jan 1 -- that this project has not verified).",
    ),
    KnowledgeEntry(
        tradition="japanese", school="", technique="Shukuyodo",
        concept="Shukuyodo (lunar-mansion astrology)", definition="A Japanese "
            "astrological system based on 27 or 28 lunar mansions (Sukuyo), transmitted "
            "via esoteric Buddhist (Mikkyo) channels originating in Indian Nakshatra "
            "astrology as it passed through Chinese Buddhist translation.",
        historical_period="Introduced to Japan via Chinese Buddhist esoteric texts, "
            "notably associated with the monk Kukai (774-835 CE) and the Shingon school.",
        geographic_origin="Japan (via China, ultimate root in India)",
        confidence_level=EvidenceLevel.HISTORICALLY_DOCUMENTED,
        cross_tradition_relationships=["jyotisha:nakshatra", "chinese:twenty_eight_lunar_mansions"],
        notes="A clear real-world case of HISTORICAL_INFLUENCE chained across three "
              "traditions (India to China to Japan) -- documented here as such rather "
              "than collapsed into a false DIRECT_CORRESPONDENCE between Shukuyodo and "
              "Nakshatra astrology, since centuries of independent Chinese Buddhist "
              "transmission separate them.",
        computed=False,
    ),
]
