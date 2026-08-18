"""
Astrowatch — EM-DAT (International Disaster Database) ingestion adapter.

STATUS: INTERFACE ONLY, NOT EXECUTED THIS PASS.
EM-DAT (public.emdat.be) requires a free account registration and manual query-tool
interaction (not a simple unauthenticated bulk API), and was also unreachable from
this sandbox's own network stack. Would be a strong Tier 1/2 source for
NATURAL_DISASTER events with damage/impact figures in a future pass with browser
access and a registered account.
"""

from typing import List

from .base import IngestionAdapter, NormalizedEventRecord


class EMDATAdapter(IngestionAdapter):
    source_id = "SRC-EMDAT"

    def retrieve(self) -> str:
        raise NotImplementedError(
            "Requires EM-DAT account registration and its interactive query tool, "
            "not attempted this pass. public.emdat.be was also unreachable from "
            "this sandbox's network stack. Not executed."
        )

    def parse(self, raw: str) -> List[dict]:
        raise NotImplementedError("depends on retrieve()")

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        raise NotImplementedError("depends on parse()")
