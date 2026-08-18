"""
Astrowatch — dataset versioning / freeze mechanism.

Freezing a dataset_version sets frozen=1, which the schema's BEFORE UPDATE/DELETE
triggers then use to reject any further silent edit to that version's events or
control_dates rows (see historical_events_schema.sql). Any future change requires
a new version_id (e.g. ASTROWATCH-HIST-002), never editing 001 in place.
"""

import hashlib
import os
import sqlite3
from datetime import datetime, timezone


def compute_db_checksum(db_path: str) -> str:
    h = hashlib.sha256()
    with open(db_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def freeze_dataset_version(
    conn: sqlite3.Connection, db_path: str, version_id: str, known_limitations: str,
) -> dict:
    event_count = conn.execute(
        "SELECT COUNT(*) FROM events WHERE dataset_version = ?", (version_id,)
    ).fetchone()[0]
    source_count = conn.execute(
        """SELECT COUNT(DISTINCT s.source_id) FROM sources s
           JOIN event_sources es ON es.source_id = s.source_id
           JOIN events e ON e.event_id = es.event_id
           WHERE e.dataset_version = ?""",
        (version_id,),
    ).fetchone()[0]
    frozen_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # NOTE on a real bug found and fixed this pass: an earlier version of this
    # function computed the checksum, then wrote that checksum INTO the same
    # database file -- a self-reference problem, since writing the checksum
    # necessarily changes the file's bytes after the checksum was computed. The
    # value stored in dataset_versions.checksum_sha256 could therefore never equal
    # the file's true final on-disk SHA-256 (confirmed the hard way: re-hashing
    # historical_events.db after freezing it produced a different value than what
    # was stored). Fixed by writing the checksum to an external sidecar file
    # (f"{db_path}.sha256") computed AFTER every write to the .db file is done --
    # standard practice for exactly this reason (release artifacts ship a
    # sidecar .sha256 rather than embedding a hash of themselves inside
    # themselves). dataset_versions.checksum_sha256 is still populated for human
    # convenience/audit trail, but the sidecar file is the one that is actually
    # guaranteed reproducible -- see compute_db_checksum's docstring-equivalent
    # usage in DATASET_FREEZE.md and validate_frozen_checksum() below.
    # checksum_sha256 is deliberately left NULL in the database row itself --
    # storing a checksum of the file INSIDE that same file is self-referential and
    # cannot be made exactly correct (writing the value changes the file, which
    # changes its hash; a second attempt to fix this pass's first attempt at this
    # function made the same mistake one level removed -- caught only because
    # test_sidecar_checksum_file_matches_actual_file_after_freeze actually re-hashed
    # the file after the fix and found it still didn't match). The sidecar file
    # below, written as the LAST operation with nothing else touching db_path
    # afterward, is the sole authoritative checksum.
    conn.execute(
        """UPDATE dataset_versions
           SET event_count = ?, source_count = ?, frozen = 1, frozen_at = ?, known_limitations = ?
           WHERE version_id = ?""",
        (event_count, source_count, frozen_at, known_limitations, version_id),
    )
    conn.commit()
    final_checksum = compute_db_checksum(db_path)
    sidecar_path = f"{db_path}.sha256"
    with open(sidecar_path, "w") as f:
        f.write(f"{final_checksum}  {os.path.basename(db_path)}\n")
    return {
        "version_id": version_id,
        "event_count": event_count,
        "source_count": source_count,
        "frozen_at": frozen_at,
        "checksum_sha256_sidecar_file": sidecar_path,
        "checksum_sha256": final_checksum,
    }


def validate_frozen_checksum(db_path: str) -> dict:
    """Compares the CURRENT file's real checksum against the sidecar file written
    at freeze time (see the note in freeze_dataset_version above for why the
    sidecar, not the in-DB column, is the trustworthy value)."""
    sidecar_path = f"{db_path}.sha256"
    if not os.path.exists(sidecar_path):
        return {"ok": False, "reason": f"no sidecar checksum file at {sidecar_path}"}
    with open(sidecar_path) as f:
        recorded = f.read().split()[0]
    current = compute_db_checksum(db_path)
    return {"ok": recorded == current, "recorded": recorded, "current": current}
