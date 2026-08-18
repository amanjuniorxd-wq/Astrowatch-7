"""
Astrowatch — UCDP (Uppsala Conflict Data Program) ingestion adapter.

STATUS: INTERFACE ONLY, NOT EXECUTED THIS PASS.
UCDP publishes bulk downloads (ucdp.uu.se/downloads) and a REST API
(ucdpapi.pcr.uu.se). Both domains returned "connection failed" from this sandbox's
own network stack (blocked by the same proxy allowlist documented in
docs/ASTRONOMY_VALIDATION_REPORT.md Phase 11 and historical/ingestion/base.py), and
were not reachable via the agent's web_fetch tool either when tried this pass.
UCDP's Georeferenced Event Dataset (GED) would be a genuinely strong TIER 2 source
for this project's MILITARY category (battle/invasion/major_military_crisis) with
real date-precision and geo-precision fields already built into its schema -- worth
prioritizing in a future pass if network access allows.
"""

from typing import List

from .base import IngestionAdapter, NormalizedEventRecord


class UCDPAdapter(IngestionAdapter):
    source_id = "SRC-UCDP"

    def retrieve(self) -> str:
        raise NotImplementedError(
            "ucdp.uu.se and ucdpapi.pcr.uu.se are both unreachable from this "
            "sandbox (network egress blocked) and were not reachable via web_fetch "
            "either when tried this pass. Not executed."
        )

    def parse(self, raw: str) -> List[dict]:
        raise NotImplementedError("depends on retrieve()")

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        raise NotImplementedError("depends on parse()")
