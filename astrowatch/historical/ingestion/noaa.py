"""
Astrowatch — NOAA NGDC significant tsunami/earthquake database ingestion adapter.

STATUS: REAL DATA, REAL EXECUTION (upgraded this pass -- see
docs/ASTRONOMY_VALIDATION_REPORT.md-style honesty: the previous pass's version of
this file was interface-only, documented as untried. This pass actually tried it
via the agent's web_fetch tool and it worked: `www.ngdc.noaa.gov/hazel/hazard-
service/api/v1/tsunamis/events` returns real, structured, Tier-1 data including
exact death tolls, coordinates, and origin times for significant historical
tsunamis. It is NOT reachable from inside this sandbox's own network stack (same
proxy-allowlist block as every other external domain -- see historical/ingestion/
base.py) -- retrieve() documents this and raises rather than pretending to succeed.

The raw response actually used this pass was saved verbatim to
data/raw/noaa_tsunamis_1880_2025_deaths1000plus_raw.json (a 6-event subset --
tsunamis with 1000+ recorded deaths, 1880-2025 -- of a real query result).
parse()/normalize() below are executed for real against that real file.
"""

import json
from typing import List

from .base import IngestionAdapter, NormalizedEventRecord

RAW_FILE_RELATIVE = "data/raw/noaa_tsunamis_1880_2025_deaths1000plus_raw.json"


class NOAATsunamiAdapter(IngestionAdapter):
    source_id = "SRC-NOAA-TSUNAMI"

    def retrieve(self) -> str:
        raise RuntimeError(
            "This adapter's own retrieve() cannot reach www.ngdc.noaa.gov from "
            "inside this sandbox (outbound proxy allowlist blocks it). The raw "
            "response used this pass was fetched via the agent's web_fetch tool "
            "and saved to data/raw/noaa_tsunamis_1880_2025_deaths1000plus_raw.json "
            "-- call parse()/normalize() directly against that file instead."
        )

    def parse(self, raw: str) -> List[dict]:
        return json.loads(raw)["items"]

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        out = []
        for r in raw_records:
            hour = r.get("hour")
            minute = r.get("minute")
            start_time = f"{hour:02d}:{minute:02d}" if hour is not None and minute is not None else None
            out.append(NormalizedEventRecord(
                event_name=f"Tsunami — {r['locationName'].title()}, {r['country'].title()} "
                           f"({r['deathsTotal']:,} deaths)",
                event_type="NATURAL_DISASTER",
                event_subtype="tsunami",
                start_date=f"{r['year']:04d}-{r['month']:02d}-{r['day']:02d}",
                start_time=start_time,
                timezone="UTC" if start_time else None,
                description=(
                    f"Tsunami originating near {r['locationName'].title()}, {r['country'].title()}"
                    + (f" (triggering earthquake magnitude {r['eqMagnitude']})" if r.get("eqMagnitude") else "")
                    + f". Max recorded wave height {r.get('maxWaterHeight', 'unknown')} m. "
                      f"NOAA-recorded total deaths: {r['deathsTotal']:,}."
                ),
                date_confidence="EXACT",
                time_confidence="EXACT" if start_time else "UNKNOWN",
                location_confidence="EXACT",
                location_precision="EXACT",
                source_quality_tier=1,
                latitude=r["latitude"],
                longitude=r["longitude"],
                location_name=r["locationName"].title(),
                country=r["country"].title(),
                source_record_id=str(r["id"]),
                source_url=f"https://www.ngdc.noaa.gov/hazel/view/hazards/tsunami/event-more-info/{r['id']}",
            ))
        return out
