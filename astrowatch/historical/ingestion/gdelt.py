"""
Astrowatch — GDELT Project ingestion adapter.

STATUS: INTERFACE ONLY, NOT EXECUTED THIS PASS.
GDELT's raw event data is enormous (daily files with hundreds of thousands of
machine-coded, unreviewed news-derived event mentions) and its own documentation
cautions that individual records are not curated for accuracy -- appropriate at
best as a Tier 4 discovery source requiring independent confirmation per record,
not something to bulk-import into this project's Tier-1..4 schema. Not attempted
this pass given the network constraint (GDELT's endpoints were not tried against
web_fetch either, given this quality caveat made it a low priority relative to the
sources actually pursued -- USGS, and well-established general reference knowledge).
"""

from typing import List

from .base import IngestionAdapter, NormalizedEventRecord


class GDELTAdapter(IngestionAdapter):
    source_id = "SRC-GDELT"

    def retrieve(self) -> str:
        raise NotImplementedError(
            "Not attempted this pass -- GDELT's raw event stream is machine-coded "
            "and explicitly not curated for per-record accuracy by GDELT's own "
            "documentation, making it Tier 4 at best; deprioritized versus USGS "
            "given this session's time and network constraints. Not executed."
        )

    def parse(self, raw: str) -> List[dict]:
        raise NotImplementedError("depends on retrieve()")

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        raise NotImplementedError("depends on parse()")
