"""
Astrowatch — historical event ingestion adapter interface.

Every adapter implements: retrieve raw data -> parse raw records -> normalize into
NormalizedEventRecord -> (caller assigns provenance separately via event_sources).
No adapter may import anything astrology-related (see historical/__init__.py).

IMPORTANT, stated once for every adapter in this package: this sandbox's outbound
network is restricted to an allowlist that does not include any of these sources'
domains (confirmed via direct curl tests -- see docs/ASTRONOMY_VALIDATION_REPORT.md
Phase 11 for the identical diagnosis against astro.com/JPL). Where a source WAS
actually reachable via the agent's own web_fetch tool (a separate path, outside this
sandbox), the raw response was saved to data/raw/ and the adapter's parse/normalize
functions are exercised for real against that saved file -- see usgs.py. Where a
source could not be reached by any available tool, or requires an API key, the
adapter defines the interface and documents the limitation instead of fabricating
data (spec item 33's "adapter interface = okay, fake downloaded data = NOT okay").
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class NormalizedEventRecord:
    """Adapter output -- not yet a full historical.models.Event (event_id/
    canonical_event_id/dataset_version get assigned at load time by
    scripts/ingest_historical_data.py, not by the adapter itself)."""
    event_name: str
    event_type: str
    event_subtype: str
    start_date: str
    description: str
    date_confidence: str
    time_confidence: str
    location_confidence: str
    location_precision: str
    source_quality_tier: int
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_record_id: Optional[str] = None   # the source dataset's own native ID,
                                              # preserved for provenance/traceability
    source_url: Optional[str] = None


class IngestionAdapter:
    """Base interface. Subclasses implement retrieve()/parse()/normalize()."""

    source_id: str = "UNSET"

    def retrieve(self) -> str:
        """Returns raw text/bytes from the source, or raises NotImplementedError /
        a documented exception if unavailable in the current environment."""
        raise NotImplementedError

    def parse(self, raw: str) -> List[dict]:
        """Raw source-native records -> list of dicts, still in the source's own
        field names/units."""
        raise NotImplementedError

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        """Source-native records -> NormalizedEventRecord, preserving uncertainty
        rather than inventing precision (spec item 19/34)."""
        raise NotImplementedError
