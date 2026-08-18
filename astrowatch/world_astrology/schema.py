"""
Astrowatch World Astrology -- knowledge-entry schema and evidence taxonomy.
Every fact this package asserts about any tradition lives in a KnowledgeEntry with
this shape (per the spec's field list) -- there is no other, looser way to add
"knowledge" to this system. Nothing here is executable astrology; it is the
structured record of what a tradition claims, how well documented that claim is,
and what (if anything) this project can actually compute for it.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EvidenceLevel(str, Enum):
    """How well-documented a given knowledge claim is. Assigned per-entry, not
    per-tradition -- a single tradition can (and usually does) mix levels."""
    ESTABLISHED = "established"                    # academic/historical consensus fact
    HISTORICALLY_DOCUMENTED = "historically_documented"  # attested in primary sources
    SCHOLARLY_DISPUTED = "scholarly_disputed"       # real scholarly disagreement exists
    TRADITIONAL_CLAIM = "traditional_claim"         # claimed within the tradition itself,
                                                     # not independently verified historically
    MODERN_INTERPRETATION = "modern_interpretation" # post-traditional reinterpretation
    UNVERIFIED = "unverified"                       # not checked this session; treat with caution


class RelationshipType(str, Enum):
    """How two concepts from different traditions actually relate -- used by
    cross_tradition.py. Superficial similarity is NEVER enough on its own for
    anything stronger than FUNCTIONAL_ANALOGY without real historical evidence."""
    DIRECT_CORRESPONDENCE = "direct_correspondence"
    PARTIAL_CORRESPONDENCE = "partial_correspondence"
    FUNCTIONAL_ANALOGY = "functional_analogy"
    HISTORICAL_INFLUENCE = "historical_influence"
    INDEPENDENT_DEVELOPMENT = "independent_development"
    NO_ESTABLISHED_CORRESPONDENCE = "no_established_correspondence"


@dataclass
class KnowledgeEntry:
    tradition: str                       # e.g. "jyotisha", "hellenistic", "babylonian"
    school: str                          # e.g. "Parashari", "Whole Sign", "" if tradition-wide
    technique: str                       # e.g. "Vimshottari Dasha"
    concept: str                         # short concept name, e.g. "Mahadasha"
    definition: str                      # plain-language definition
    historical_period: str               # e.g. "c. 1st century BCE - present"
    geographic_origin: str
    primary_sources: List[str] = field(default_factory=list)
    secondary_sources: List[str] = field(default_factory=list)
    calculation_method: str = ""         # prose description; NOT the code itself
    required_astronomical_inputs: List[str] = field(default_factory=list)
    interpretation_rules: str = ""
    prediction_domain: List[str] = field(default_factory=list)  # e.g. ["natal","mundane"]
    example: str = ""
    confidence_level: EvidenceLevel = EvidenceLevel.UNVERIFIED
    historical_evidence: str = ""        # prose: what attests this, and how strongly
    cross_tradition_relationships: List[str] = field(default_factory=list)  # concept keys
    notes: str = ""
    limitations: str = ""
    computed: bool = False               # True only if this project has real, tested code
                                          # that actually calculates this technique's output
    entry_id: str = ""                   # unique key, set by the module that defines it

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = f"{self.tradition}:{self.concept}".lower().replace(" ", "_")


class TraditionRegistry:
    """In-memory registry every tradition module populates via register(). Kept
    simple and dependency-free (no ORM/db needed for this scale of content) --
    if this grows past a few hundred entries, migrating to a real sqlite table
    (schema is a 1:1 mapping of KnowledgeEntry's fields) is straightforward."""

    def __init__(self):
        self._entries: dict[str, KnowledgeEntry] = {}

    def register(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        if entry.entry_id in self._entries:
            raise ValueError(f"duplicate knowledge entry_id: {entry.entry_id!r}")
        self._entries[entry.entry_id] = entry
        return entry

    def register_all(self, entries: List[KnowledgeEntry]) -> None:
        for e in entries:
            self.register(e)

    def get(self, entry_id: str) -> Optional[KnowledgeEntry]:
        return self._entries.get(entry_id)

    def all(self) -> List[KnowledgeEntry]:
        return list(self._entries.values())

    def by_tradition(self, tradition: str) -> List[KnowledgeEntry]:
        return [e for e in self._entries.values() if e.tradition == tradition]

    def traditions(self) -> List[str]:
        return sorted(set(e.tradition for e in self._entries.values()))

    def computed_traditions(self) -> List[str]:
        """Traditions with at least one entry this project can actually calculate,
        as opposed to reference-only knowledge."""
        return sorted(set(e.tradition for e in self._entries.values() if e.computed))

    def search(self, query: str) -> List[KnowledgeEntry]:
        q = query.lower()
        return [e for e in self._entries.values()
                if q in e.concept.lower() or q in e.technique.lower() or q in e.definition.lower()]
