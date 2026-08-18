# Astrowatch Historical Event Dataset — Freeze Record

Every field below is copied directly from the actual `dataset_versions` row in
`historical_events.db` (queried live to write this document — not hand-typed).

```text
dataset_version:   ASTROWATCH-HIST-001
created_date:      2026-08-14
frozen:            1 (TRUE)
frozen_at:         2026-08-14T15:54:15+00:00
event_count:       136
source_count:      5
checksum_sha256:   70e189ceed08dc784e9c4ff391313f980fd270f6b659aebdad01190bb66c0245
```

## Coverage

136 events across 6 categories (see `HISTORICAL_DATA_QUALITY_REPORT.md` for the
full, live-generated breakdown by category/subtype/region/country/decade/century):
MILITARY (25), POLITICAL (24), ECONOMIC (15), NATURAL_DISASTER (34),
SOCIAL_PUBLIC_HEALTH (18), SCIENCE_TECHNOLOGY (20). Spans roughly 79 CE (Vesuvius)
to 2025 (Kamchatka earthquake), with deliberate effort toward non-US/non-European
geography (China, Japan, India, Pakistan, Bangladesh, Indonesia, Philippines,
Myanmar, Rwanda, South Africa, Egypt, Iran, Iraq, Israel, Cuba, Argentina,
Venezuela, Zimbabwe, Haiti, Chile, Kazakhstan, Australia) alongside the US and
Europe.

## Known limitations (verbatim from the frozen row)

136 events total, far below the 500-2000 target (quality over quantity, per spec
item 20). 117/136 events (86%) are UNVERIFIED (general reference knowledge, not
independently re-checked via a live source this session) — see
`HISTORICAL_DATA_QUALITY_REPORT.md`. Only USGS earthquake events (16) carry
machine-precision date/time/location; nearly everything else has time_confidence
UNKNOWN or APPROXIMATE and no coordinates. UCDP/ACLED/GDELT/EM-DAT/NOAA
integrations are interface-only, not executed (network/credential constraints —
see `historical/ingestion/*.py`). Deduplication is heuristic, not exhaustive. 3
events carry DISPUTED date_confidence with the specific source disagreement
documented in `manual_review.csv`.

## Immutability

As of the `frozen_at` timestamp above, `historical_events_schema.sql`'s
`BEFORE UPDATE`/`BEFORE DELETE` triggers reject any edit or delete to this
version's `events` or `control_dates` rows — confirmed by actually attempting an
edit after freezing and observing the rejection (see
`tests/historical/test_dedup_controls_versioning.py::VersioningTests`).

## Future changes

Any correction, addition, or re-sourcing effort (e.g. resolving the 3 DISPUTED
events, integrating UCDP once network access allows, expanding past 136 events)
must create `ASTROWATCH-HIST-002` via `scripts/ingest_historical_data.py` +
`scripts/freeze_historical_dataset.py --version ASTROWATCH-HIST-002` against a
fresh database (or a new dataset_version row within the same database) — never a
silent edit to `001`.

## Reproducing the checksum

```bash
python3 -c "from historical.versioning import compute_db_checksum; print(compute_db_checksum('historical_events.db'))"
```

Should print `70e189ceed08dc784e9c4ff391313f980fd270f6b659aebdad01190bb66c0245` if
the database file is byte-identical to what was frozen. (Regenerating the dataset
from scratch via `ingest_historical_data.py` will NOT reproduce this exact checksum
— it depends on SQLite's internal page layout, not just logical content — but
re-running `validate_historical_db.py` against a freshly regenerated database should
still report 0 FATAL issues.)

---

## ASTROWATCH-HIST-002 (quality-improvement pass, this session)

Built in a **separate database file**, `historical_events_v2.db`, specifically so
`historical_events.db`'s frozen `ASTROWATCH-HIST-001` rows are never touched.
Confirmed unchanged: `ASTROWATCH-HIST-001`'s checksum in `historical_events.db` is
still `70e189ceed08dc784e9c4ff391313f980fd270f6b659aebdad01190bb66c0245` (identical
to the value recorded above), verified by direct query after this pass completed.

```text
dataset_version:   ASTROWATCH-HIST-002
created_date:      2026-08-14
frozen:            1 (TRUE)
frozen_at:         2026-08-14T16:11:09+00:00
event_count:       140
source_count:      30
checksum_sha256:   c785728c4cc2ad0f1de03a2a0bcb8585cead24726c408e3cfc71ddb2c2a96938
```

### What changed versus HIST-001

1. **12 events independently re-verified via WebSearch this pass** (not general
   model knowledge) and upgraded from `UNVERIFIED` to `MULTI_SOURCE_CONFIRMED`,
   each with 2 real, independently-fetched, non-mirror sources cited — see
   `data/verification_updates.py` for the exact sources and notes, including 2
   real precision corrections (Pearl Harbor's attack time; Mandela's and the
   Bangladesh surrender's exact local times) found through this verification, not
   assumed.
2. **6 real NOAA tsunami records added** (Tier 1, exact date/time/location,
   including real recorded death tolls) via `historical/ingestion/noaa.py`, now
   upgraded from interface-only to an actually-executed adapter.
3. **2 placeholder tsunami entries dropped** ("2004 Indian Ocean tsunami", "2011
   Tōhoku tsunami") in favor of the NOAA-sourced versions of the same real events
   — avoiding duplication while upgrading source tier and precision.
4. **Deduplication re-run with an expanded signal set** (fuzzy name similarity,
   source_record_id matching, date-range overlap, description overlap — see
   `historical/deduplication.py`). Result: 0 candidates flagged in the 140-event
   set.
5. Net result: verified-event count rose from 19/136 (14%) to 37/140 (26%);
   unverified fell from 117 (86%) to 103 (74%). Still a minority-verified dataset —
   stated plainly, not overstated.

### Known limitations (verbatim, this version)

140 events, still far short of any 500+ target — deliberately not pursued this
pass, per explicit instruction to prioritize verified quality over raw count. 103
events (74%) remain UNVERIFIED. UCDP and ACLED remain inaccessible (network-blocked
/ API-key-gated respectively). World Bank and WHO GHO APIs were newly confirmed
reachable this pass but are indicator time series, not discrete historical events,
so were not force-fit into this schema. No backtest engine exists; this dataset is
not yet ready for genuine hypothesis testing against Astrowatch's rules.

### Future changes

Any further correction/expansion must create `ASTROWATCH-HIST-003` — never a
silent edit to `001` or `002`.

---

## CORRECTION (found via this pass's own re-verification): the in-DB checksum was wrong

Re-running `compute_db_checksum()` against both frozen databases as part of this
pass's final validation produced values that did **not** match either
`dataset_versions.checksum_sha256` value recorded above. Investigated rather than
dismissed — see the full diagnosis and fix in `historical/versioning.py`.

**Root cause:** `freeze_dataset_version()` computed the SHA-256 of the `.db` file,
then wrote that checksum value back INTO the same file (the `dataset_versions` row).
Writing the checksum necessarily changes the file's bytes, so the recorded value
can never equal the file's true final on-disk hash — a self-reference problem, not
a data-integrity problem (no event content was affected; `git diff` and `git show`
both confirm neither `.db` file's bytes have changed since their original commit).

**Fix, going forward:** `freeze_dataset_version()` now leaves
`dataset_versions.checksum_sha256` `NULL` and instead writes the checksum to an
external sidecar file (`{db_path}.sha256`) as the *last* operation, with nothing
else touching the `.db` file afterward. Regression-tested in
`tests/historical/test_dedup_controls_versioning.py`
(`test_sidecar_checksum_file_matches_actual_file_after_freeze`).

**For the two already-frozen versions** (`ASTROWATCH-HIST-001` and
`ASTROWATCH-HIST-002`, both frozen before this fix): their `dataset_versions.
checksum_sha256` values are left as-is rather than silently edited — updating them
after the fact, even to correct an error, would cut against the same
"don't silently modify a frozen version" principle this mechanism exists to
protect. Instead, sidecar files were generated this pass, reflecting the files'
actual current (unchanged since original commit) state:

```text
historical_events.db.sha256:     92f03da4fe644bb6bde44320ba41c2b3bb9cec7ec555446f9dbe5dac9f243c6e
historical_events_v2.db.sha256:  e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa
```

These are the TRUE, reproducible checksums for both files as committed. Treat the
`checksum_sha256` values printed earlier in this document (`70e189...` for
HIST-001, `c785728...` for HIST-002) as historical artifacts of the bug, not
verifiable values.
