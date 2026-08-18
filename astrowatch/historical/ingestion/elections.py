"""
Astrowatch — national election-results ingestion adapter.

STATUS: INTERFACE ONLY, NOT EXECUTED THIS PASS.
"Elections" is not one API but hundreds of national electoral-authority archives
with no unified schema -- no single source was attempted this pass. A handful of
major elections ARE included in this pilot's events_seed data, but sourced from
general historical reference knowledge (see manual_review.csv / data_dictionary.md
for the honest verification_status this implies), not through this adapter.
"""

from typing import List

from .base import IngestionAdapter, NormalizedEventRecord


class ElectionsAdapter(IngestionAdapter):
    source_id = "SRC-ELECTIONS"

    def retrieve(self) -> str:
        raise NotImplementedError(
            "No unified elections API exists to query -- would require per-country "
            "electoral-authority integration, not attempted this pass. Not executed."
        )

    def parse(self, raw: str) -> List[dict]:
        raise NotImplementedError("depends on retrieve()")

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        raise NotImplementedError("depends on parse()")
