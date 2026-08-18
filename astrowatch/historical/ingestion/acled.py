"""
Astrowatch — ACLED (Armed Conflict Location & Event Data) ingestion adapter.

STATUS: INTERFACE ONLY, NOT EXECUTED THIS PASS.
ACLED's API (api.acleddata.com) requires a registered API key/email pair (ACLED
Access system) -- credentials this session does not have and must not fabricate
(spec item 33: "If an API requires credentials that are not available: do not
fabricate credentials or data"). api.acleddata.com was also unreachable from this
sandbox's own network stack regardless. Documented, not executed.
"""

from typing import List

from .base import IngestionAdapter, NormalizedEventRecord


class ACLEDAdapter(IngestionAdapter):
    source_id = "SRC-ACLED"

    def retrieve(self) -> str:
        raise NotImplementedError(
            "Requires an ACLED Access API key, which is not available this "
            "session -- not fabricated. api.acleddata.com was also unreachable "
            "from this sandbox's network stack. Not executed."
        )

    def parse(self, raw: str) -> List[dict]:
        raise NotImplementedError("depends on retrieve()")

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        raise NotImplementedError("depends on parse()")
