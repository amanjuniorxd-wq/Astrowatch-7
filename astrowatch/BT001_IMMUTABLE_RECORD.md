# ASTROWATCH-BT-001 — Immutable Record

This file is a point-in-time snapshot of everything needed to prove what
ASTROWATCH-BT-001 actually was, generated as Phase 2 of the "VALIDATION HARDENING
BEFORE BT-002" pass. It exists so that all subsequent work in this pass (implementing
missing rule detectors, hardening the astronomy path, redesigning sampling fairness,
etc.) can be independently verified to have left BT-001 untouched.

**This record does not modify `backtest_results.db`, `historical_events_v2.db`, or
`BACKTEST_REPORT_ASTROWATCH_BT001.md` in any way — it only reads and reports on them.**
Re-generate the values below at any time with `historical.versioning.compute_db_checksum`
and Python's `hashlib.sha256` to independently confirm nothing has drifted.

## Experiment identity (from `backtest_results.db`, `experiments` table)

| Field | Value |
|---|---|
| experiment_id | `ASTROWATCH-BT-001` |
| dataset_version | `ASTROWATCH-HIST-002` |
| rule_registry_version (hash) | `94dc2ebb02b1928fb44950f6a2464404bc730bef3e960908b48d38a43b2c59a7` |
| astronomy_version (hash) | `6ee2e17f6dfaf579527c59f3133418f96f9ab9f5d4ce30528f3329f8933db6c2` |
| astrowatch_version | `0.1.0-experimental` |
| configuration_hash | `bca4be94cf19eff054619fef7ab3f6040521150c62ad221ec7d62ae5a0a834f3` |
| random_seed | `20260814` |
| sampling_method | `FULL_DATASET` |
| control_method | `EXISTING_CONTROL_DATES_REUSED` |
| region_used | `GLOBAL` |
| allow_ayanamsha_fallback | `True` |
| dataset_checksum_before | `e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa` |
| dataset_checksum_after | `e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa` |
| dataset_integrity | `UNCHANGED` |
| status | `COMPLETED` |
| frozen | `1` (true) |
| frozen_at | `2026-08-14T16:47:10+00:00` |

## Artifact checksums, re-verified at the start of this hardening pass

| Artifact | SHA-256 |
|---|---|
| `historical_events_v2.db` (live file, via sidecar `historical_events_v2.db.sha256`) | `e5cabbe5115c7d115eb0ec56ae18083db028e2579b6f4b7daf2680a143dc30fa` — **MATCH** |
| `historical_events.db` (HIST-001, via sidecar) | `92f03da4fe644bb6bde44320ba41c2b3bb9cec7ec555446f9dbe5dac9f243c6e` — **MATCH** |
| `backtest_results.db` (live file, via sidecar `backtest_results.db.ASTROWATCH-BT-001.sha256`) | `3bf8d1d48b08014cfe15c329c2707890ad8e57ff8f9cb2c488115753a47805db` — **MATCH** |
| `BACKTEST_REPORT_ASTROWATCH_BT001.md` (recorded here, first time; no prior sidecar existed for this file) | `e80b81c3ebfbc974e325b52f0ed57d8ca6b2c05936ee5a3c8ef536733ba60619` |

## Enforcement mechanism

- `historical_events_v2.db` and `historical_events.db`: protected by their own
  `dataset_versions.frozen=1` + `BEFORE UPDATE`/`BEFORE DELETE` triggers
  (`historical_events_schema.sql`), independently re-verified via sidecar checksum
  above. Nothing in this hardening pass writes to either file — enforced by the same
  static test used in the BT-001 pass (`tests/backtest/test_immutability.py::
  NoWriteSQLAgainstHistoricalTablesTests`), re-run as part of Phase 18 below.
- `backtest_results.db`'s `experiments` row for `ASTROWATCH-BT-001`: protected by
  `trg_experiments_immutable_after_freeze` / `trg_experiments_no_unfreeze`
  (`backtest_results_schema.sql`) — any `UPDATE` against a frozen experiment row
  raises `sqlite3.IntegrityError`. A new experiment (`ASTROWATCH-BT-002`) gets a new
  row; BT-001's row is never edited in place.
- `BACKTEST_REPORT_ASTROWATCH_BT001.md`: not database-protected (it's a plain file),
  so its checksum is recorded here as the enforcement mechanism — any future
  re-generation of a BT-001 report would need to reuse this exact filename over an
  already-committed, already-hashed file, which `git diff` and this record together
  make immediately visible. `scripts/generate_backtest_report.py` was not re-run
  against `ASTROWATCH-BT-001` during this hardening pass; it will only ever be
  pointed at `ASTROWATCH-BT-002`'s (or later) experiment_id going forward.

## Verification command

```bash
cd astrowatch
python3 -c "
from historical.versioning import validate_frozen_checksum, compute_db_checksum
import hashlib
print('HIST-002:', validate_frozen_checksum('historical_events_v2.db'))
print('HIST-001:', validate_frozen_checksum('historical_events.db'))
print('backtest_results.db == sidecar:',
      compute_db_checksum('backtest_results.db') ==
      open('backtest_results.db.ASTROWATCH-BT-001.sha256').read().split()[0])
print('report sha256:', hashlib.sha256(open('BACKTEST_REPORT_ASTROWATCH_BT001.md','rb').read()).hexdigest())
"
```

Expected output: both `validate_frozen_checksum` calls return `{'ok': True, ...}`,
`backtest_results.db == sidecar` is `True`, and the report hash equals
`e80b81c3ebfbc974e325b52f0ed57d8ca6b2c05936ee5a3c8ef536733ba60619`.
