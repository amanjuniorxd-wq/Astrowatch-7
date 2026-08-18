import glob
import os
import re
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import historical.database as hdb
import historical.versioning as hversioning
from backtest import sampler, controls, engine, database as bdb, repository as brepo, predictor

ASTROWATCH_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HIST_DB = os.path.join(ASTROWATCH_DIR, "historical_events_v2.db")


class Hist002FileImmutabilityTests(unittest.TestCase):
    def test_checksum_unchanged_by_sampling_and_prediction(self):
        before = hversioning.compute_db_checksum(HIST_DB)
        conn = hdb.connect(HIST_DB)
        cases = sampler.sample_full_dataset(conn, "ASTROWATCH-HIST-002", "EXP-IMMUT")
        ctrl_cases = controls.sample_existing_control_dates(conn, "ASTROWATCH-HIST-002", "EXP-IMMUT")
        for tc in cases[:5] + ctrl_cases[:5]:
            predictor.predict(tc.to_blind_input(), "EXP-IMMUT", f"PRED-{tc.test_case_id}")
        conn.close()
        after = hversioning.compute_db_checksum(HIST_DB)
        self.assertEqual(before, after)

    def test_sidecar_checksum_still_matches_file(self):
        result = hversioning.validate_frozen_checksum(HIST_DB)
        self.assertTrue(result["ok"], msg=result)


class NoWriteSQLAgainstHistoricalTablesTests(unittest.TestCase):
    """Static scan: no file in backtest/ contains SQL that would write to any
    historical_events_v2.db table. repository.py's write statements (INSERT INTO
    experiments/test_cases/predictions/...) all target backtest_results.db's OWN
    schema -- verified here by table-name allowlist."""

    HISTORICAL_TABLES = {"events", "event_sources", "control_dates", "sources", "dataset_versions"}
    WRITE_VERB_RE = re.compile(r"\b(INSERT INTO|UPDATE|DELETE FROM)\s+(\w+)", re.IGNORECASE)

    def test_no_write_statements_target_historical_tables(self):
        backtest_dir = os.path.join(ASTROWATCH_DIR, "backtest")
        offenders = []
        for path in glob.glob(os.path.join(backtest_dir, "*.py")):
            with open(path) as f:
                source = f.read()
            for match in self.WRITE_VERB_RE.finditer(source):
                table = match.group(2).lower()
                if table in self.HISTORICAL_TABLES:
                    offenders.append(f"{path}: {match.group(0)}")
        self.assertEqual(offenders, [], msg=f"Found write SQL against historical tables: {offenders}")


class ExperimentFreezeImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        os.remove(self.tmp.name)
        self.conn = bdb.initialize_db(self.tmp.name)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.tmp.name):
            os.remove(self.tmp.name)

    def test_frozen_experiment_rejects_further_update(self):
        exp = engine.build_experiment(
            experiment_id="EXP-FREEZE-TEST", dataset_version="ASTROWATCH-HIST-002",
            hist_db_path=HIST_DB, astrowatch_dir=ASTROWATCH_DIR, random_seed=1,
            sampling_method="FULL_DATASET", control_method="EXISTING_CONTROL_DATES",
            allow_ayanamsha_fallback=True, test_window_start=None, test_window_end=None,
        )
        brepo.insert_experiment(self.conn, exp)
        self.conn.commit()
        brepo.freeze_experiment(self.conn, exp.experiment_id, "2026-08-14T00:00:00")
        self.conn.commit()
        row = brepo.get_experiment(self.conn, exp.experiment_id)
        self.assertEqual(row["frozen"], 1)

        with self.assertRaises(Exception):
            self.conn.execute(
                "UPDATE experiments SET notes = 'tampered' WHERE experiment_id = ?",
                (exp.experiment_id,),
            )
            self.conn.commit()

    def test_checksum_mismatch_raises_and_stops(self):
        import shutil
        tmp_hist = self.tmp.name + ".histcopy.db"
        shutil.copy(HIST_DB, tmp_hist)
        shutil.copy(HIST_DB + ".sha256", tmp_hist + ".sha256")
        try:
            with open(tmp_hist, "ab") as f:
                f.write(b"\x00tamper")  # corrupt the copy, sidecar now stale
            with self.assertRaises(engine.ChecksumMismatchError):
                engine.verify_hist002_checksum(tmp_hist)
        finally:
            for p in (tmp_hist, tmp_hist + ".sha256"):
                if os.path.exists(p):
                    os.remove(p)


if __name__ == "__main__":
    unittest.main()
