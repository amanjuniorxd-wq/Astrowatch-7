import os
import sys
import sqlite3
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from historical import database, models, repository, validation  # noqa: E402


def make_dv(vid="V1"):
    return models.DatasetVersion(version_id=vid, created_date="2026-08-14")


def make_source(sid="SRC-1"):
    return models.Source(sid, "Test Source", "Org", "encyclopedia", 3, "http://x", "2026-08-14", "cov", None)


def base_event_kwargs(**overrides):
    base = dict(
        event_id="EVENT-1900-001", canonical_event_id="EVENT-1900-001", event_name="Test",
        event_type="MILITARY", event_subtype="war_start", start_date="1900-01-01",
        date_confidence="EXACT", time_confidence="UNKNOWN", location_confidence="COUNTRY",
        location_precision="COUNTRY", description="desc", source_quality_tier=3,
        verification_status="SINGLE_SOURCE", dataset_version="V1",
        created_at="x", updated_at="x", verification_count=1,
    )
    base.update(overrides)
    return base


class UncertaintyConstraintTests(unittest.TestCase):
    """These exercise the schema's CHECK constraints directly via repository.insert_event."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = database.initialize_db(self.tmp.name)
        repository.create_dataset_version(self.conn, make_dv())
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_exact_date_confidence_allowed(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs(date_confidence="EXACT")))
        self.conn.commit()  # should not raise

    def test_approximate_date_confidence_allowed(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs(date_confidence="APPROXIMATE")))
        self.conn.commit()

    def test_date_range_confidence_allowed_with_end_date(self):
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(date_confidence="DATE_RANGE", end_date="1901-01-01")))
        self.conn.commit()

    def test_disputed_date_confidence_allowed(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs(date_confidence="DISPUTED")))
        self.conn.commit()

    def test_unknown_date_confidence_allowed(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs(date_confidence="UNKNOWN")))
        self.conn.commit()

    def test_unknown_time_with_no_start_time_allowed(self):
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(time_confidence="UNKNOWN", start_time=None)))
        self.conn.commit()

    def test_exact_time_without_start_time_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            repository.insert_event(self.conn, models.Event(
                **base_event_kwargs(time_confidence="EXACT", start_time=None)))

    def test_exact_time_with_start_time_allowed(self):
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(time_confidence="EXACT", start_time="12:00")))
        self.conn.commit()

    def test_unknown_location_confidence_allowed(self):
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(location_confidence="UNKNOWN", location_precision="UNKNOWN")))
        self.conn.commit()

    def test_exact_location_without_coordinates_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            repository.insert_event(self.conn, models.Event(
                **base_event_kwargs(location_confidence="EXACT", location_precision="EXACT")))

    def test_exact_location_with_coordinates_allowed(self):
        # EXACT requires both coordinates AND a location_name/country (see the schema
        # comment on this pair of CHECK constraints) -- omitting country/location_name
        # here would (correctly) fail the second constraint, not this one's target.
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(location_confidence="EXACT", location_precision="EXACT",
                                 latitude=1.0, longitude=2.0, location_name="Somewhere")))
        self.conn.commit()

    def test_city_location_without_coordinates_allowed_if_location_name_present(self):
        repository.insert_event(self.conn, models.Event(
            **base_event_kwargs(location_confidence="CITY", location_precision="CITY",
                                 location_name="Somewhere")))
        self.conn.commit()


class ValidationScriptTests(unittest.TestCase):
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

    def _insert_with_source(self, **overrides):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs(**overrides)))
        repository.insert_event_source(self.conn, models.EventSource(
            overrides.get("event_id", "EVENT-1900-001"), "SRC-1", "CONFIRMED", created_at="x"))
        self.conn.commit()

    def test_clean_db_has_no_fatal_issues(self):
        self._insert_with_source()
        issues = validation.validate(self.conn)
        self.assertFalse(any(i.severity == "FATAL" for i in issues))

    def test_missing_provenance_detected(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs()))
        self.conn.commit()
        issues = validation.validate(self.conn)
        self.assertTrue(any(i.check == "missing_provenance" for i in issues))

    def test_exit_code_nonzero_on_fatal(self):
        repository.insert_event(self.conn, models.Event(**base_event_kwargs()))
        self.conn.commit()
        issues = validation.validate(self.conn)
        self.assertEqual(validation.exit_code_for(issues), 1)

    def test_exit_code_zero_when_clean(self):
        self._insert_with_source()
        issues = validation.validate(self.conn)
        self.assertEqual(validation.exit_code_for(issues), 0)

    def test_invalid_taxonomy_detected_via_direct_write(self):
        # bypass repository to simulate a corrupted row reaching validate()
        self.conn.execute("PRAGMA foreign_keys=OFF")
        self._insert_with_source()
        self.conn.execute(
            "UPDATE events SET event_subtype = 'not_real' WHERE event_id = 'EVENT-1900-001'"
        )
        self.conn.commit()
        issues = validation.validate(self.conn)
        self.assertTrue(any(i.check == "invalid_taxonomy" for i in issues))


if __name__ == "__main__":
    unittest.main(verbosity=2)
