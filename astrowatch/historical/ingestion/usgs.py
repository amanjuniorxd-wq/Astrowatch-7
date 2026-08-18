"""
Astrowatch — USGS earthquake catalog ingestion adapter.

STATUS: REAL DATA, REAL EXECUTION. The USGS FDSNWS event API
(earthquake.usgs.gov/fdsnws/event/1/query) was actually reached this session via the
agent's own web_fetch tool (this sandbox's own network egress is blocked by a proxy
allowlist that excludes earthquake.usgs.gov -- same diagnosed limitation as
ephemeris_client.py; retrieve() below documents this and raises rather than
pretending to succeed). The raw GeoJSON response was saved verbatim to
data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json (16 of the 31 M>=8.3
earthquakes 1900-2026 returned by the real query -- a representative subset kept
for the pilot, not the full result). parse()/normalize() below are executed for
real against that real file.

USGS is a TIER 1 (primary/official) source. Its catalog gives exact epoch-millisecond
origin times and exact hypocenter coordinates -- both are used here with EXACT
date/time/location confidence, which is honest for this specific source (unlike
most other events in this pilot dataset, which lack this level of source precision).
"""

import json
from datetime import datetime, timezone
from typing import List

from .base import IngestionAdapter, NormalizedEventRecord

RAW_FILE_RELATIVE = "data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json"


class USGSEarthquakeAdapter(IngestionAdapter):
    source_id = "SRC-USGS-EARTHQUAKE"

    def retrieve(self) -> str:
        raise RuntimeError(
            "This adapter's own retrieve() cannot reach earthquake.usgs.gov from "
            "inside this sandbox (outbound proxy allowlist blocks it -- confirmed "
            "via curl, same diagnosis as ephemeris_client.py in "
            "docs/ASTRONOMY_VALIDATION_REPORT.md Phase 11). The raw response used by "
            "this pass was fetched via the agent's separate web_fetch tool and saved "
            "to data/raw/usgs_earthquakes_m8.3plus_1900_2026_raw.json -- call "
            "parse()/normalize() directly against that file instead of retrieve()."
        )

    def parse(self, raw: str) -> List[dict]:
        data = json.loads(raw)
        return data["features"]

    def normalize(self, raw_records: List[dict]) -> List[NormalizedEventRecord]:
        out = []
        for feat in raw_records:
            props = feat["properties"]
            lon, lat = feat["geometry"]["coordinates"][0], feat["geometry"]["coordinates"][1]
            dt = datetime.fromtimestamp(props["time"] / 1000.0, tz=timezone.utc)
            place = props.get("place", "unknown location")
            mag = props["mag"]
            out.append(NormalizedEventRecord(
                event_name=f"M{mag} earthquake — {place}",
                event_type="NATURAL_DISASTER",
                event_subtype="earthquake",
                start_date=dt.strftime("%Y-%m-%d"),
                start_time=dt.strftime("%H:%M"),
                timezone="UTC",
                description=(
                    f"Magnitude {mag} ({props.get('magType', 'unknown scale')}) earthquake, "
                    f"{place}. Tsunami generated: {'yes' if props.get('tsunami') else 'no (per USGS flag)'}."
                ),
                date_confidence="EXACT",
                time_confidence="EXACT",
                location_confidence="EXACT",
                location_precision="EXACT",
                source_quality_tier=1,
                latitude=round(lat, 4),
                longitude=round(lon, 4),
                location_name=place,
                source_record_id=feat.get("id"),
                source_url=f"https://earthquake.usgs.gov/earthquakes/eventpage/{feat.get('id')}",
            ))
        return out
