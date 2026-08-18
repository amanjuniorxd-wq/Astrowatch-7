import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from historical import database, models, repository  # noqa: E402


def make_dv(vid="V1"):
    return models.DatasetVersion(version_id=vid, created_date="2026-08-14", description="test")


def make_source(sid="SRC-1"):
    return models.Source(sid, "Test Source", "Org", "encyclopedia", 3, "http://x", "2026-08-14", "cov", None)


def make_event(eid="EVENT-1900-001", dv="V1", **overrides):
    base = dict(
        event_id=eid, canonical_event_id=eid, event_name="Test Event",
        event_type="MILITARY", event_subtype="war_start", start_date="1900-01-01",
        date_confidence="EXACT", time_confidence="UNKNOWN", location_confidence="COUNTRY",
        location_precision="COUNTRY", description="desc", source_quality_tier=3,
        verification_status="SINGLE_SOURCE", dataset_version=dv,
        created_at="2026-08-14T00:00:00", updated_at="2026-08-14T00:00:00",
        country="Testland", country_code="TST", region="Testregion", verification_count=1,
    )
    base.update(overrides)
    return models.Event(**base)


class DatabaseCreationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)

    def tearDown(self):
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_initialize_db_creates_all_tables(self):
        conn = database.initialize_db(self.tmp.name)
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        for t in ("events", "sources", "event_sources", "control_dates", "dataset_versions"):
            self.assertIn(t, tables)
        conn.close()

    def test_initialize_db_refuses_overwrite_by_default(self):
        database.initialize_db(self.tmp.name).close()
        with self.assertRaises(FileExistsError):
            database.initialize_db(self.tmp.name)

    def test_initialize_db_overwrite_flag_works(self):
        database.initialize_db(self.tmp.name).close()
        conn = database.initialize_db(self.tmp.name, overwrite=True)
        conn.close()  # should not raise

    def test_foreign_keys_enforced(self):
        conn = database.initialize_db(self.tmp.name)
        with self.assertRaises(Exception):
            conn.execute(
                "INSERT INTO events (event_id, canonical_event_id, event_name, event_type, "
                "event_subtype, start_date, location_precision, description, "
                "source_quality_tier, date_confidence, time_confidence, location_confidence, "
                "verification_status, verification_count, dataset_version, created_at, updated_at) "
                "VALUES ('E1','E1','n','MILITARY','war_start','1900-01-01','COUNTRY','d',3,"
                "'EXACT','UNKNOWN','COUNTRY','SINGLE_SOURCE',1,'NONEXISTENT-VERSION','x','x')"
            )
        conn.close()


class RepositoryInsertRetrieveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = database.initialize_db(self.tmp.name)
        repository.create_dataset_version(self.conn, make_dv())
        repository.insert_source(self.conn, make_source())
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_insert_and_get_event(self):
        repository.insert_event(self.conn, make_event())
        self.conn.commit()
        row = repository.get_event(self.conn, "EVENT-1900-001")
        self.assertEqual(row["event_name"], "Test Event")

    def test_get_events_category_filter(self):
        repository.insert_event(self.conn, make_event("EVENT-1900-001", event_type="MILITARY"))
        repository.insert_event(self.conn, make_event("EVENT-1900-002", event_type="ECONOMIC",
                                                        event_subtype="market_crash"))
        self.conn.commit()
        rows = repository.get_events(self.conn, category="MILITARY")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_id"], "EVENT-1900-001")

    def test_get_events_region_and_date_filters(self):
        repository.insert_event(self.conn, make_event("EVENT-1900-001", start_date="1900-06-01"))
        repository.insert_event(self.conn, make_event("EVENT-1950-001", start_date="1950-06-01"))
        self.conn.commit()
        rows = repository.get_events(self.conn, start_date="1940-01-01")
        self.assertEqual([r["event_id"] for r in rows], ["EVENT-1950-001"])

    def test_get_events_source_quality_filter(self):
        repository.insert_event(self.conn, make_event("EVENT-1900-001", source_quality_tier=1))
        repository.insert_event(self.conn, make_event("EVENT-1900-002", source_quality_tier=4))
        self.conn.commit()
        rows = repository.get_events(self.conn, min_source_quality=2)
        self.assertEqual([r["event_id"] for r in rows], ["EVENT-1900-001"])

    def test_get_events_deterministic_ordering(self):
        repository.insert_event(self.conn, make_event("EVENT-1900-002", start_date="1900-01-01"))
        repository.insert_event(self.conn, make_event("EVENT-1900-001", start_date="1900-01-01"))
        self.conn.commit()
        rows1 = repository.get_events(self.conn)
        rows2 = repository.get_events(self.conn)
        self.assertEqual([r["event_id"] for r in rows1], [r["event_id"] for r in rows2])

    def test_event_source_link_and_get_event_sources(self):
        repository.insert_event(self.conn, make_event())
        repository.insert_event_source(self.conn, models.EventSource(
            "EVENT-1900-001", "SRC-1", "CONFIRMED", created_at="2026-08-14T00:00:00",
        ))
        self.conn.commit()
        links = repository.get_event_sources(self.conn, "EVENT-1900-001")
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["source_id"], "SRC-1")

    def test_missing_provenance_is_possible_at_repository_level(self):
        # repository itself does not enforce provenance -- that's validate()'s job.
        # confirm insert succeeds with zero sources so the validation test elsewhere
        # can prove it's actually validation.py catching this, not a DB constraint.
        repository.insert_event(self.conn, make_event())
        self.conn.commit()
        self.assertEqual(len(repository.get_event_sources(self.conn, "EVENT-1900-001")), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
