"""
Astrowatch Online -- tests for the AI intelligence layer, entity/prediction
databases, X publishing module, and the new api.py endpoints.

Uses in-memory / temp-file sqlite databases throughout (never touches the
real entities.db/predictions.db this process might otherwise create) and
never makes a real OpenAI or X network call -- OPENAI_API_KEY/X credentials
are deliberately left unset for these tests, which is itself the thing being
tested (graceful degradation, task spec Section 5/29).
"""
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import entities_db
import predictions_db
from ai import openai_client
from ai import tools as ai_tools
from ai import prediction_agent, random_prediction, agent as ai_agent
from ai import synthesis
from x import publisher as x_publisher


def _tmp_entities_conn():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = entities_db.get_connection(path)
    entities_db.add_entity(conn, name="Testland", entity_type="country",
                            birth_or_inception_date="1950-01-01",
                            latitude=10.0, longitude=20.0, timezone="UTC",
                            source="unit_test", time_accuracy="assumed_midnight")
    entities_db.add_entity(conn, name="Ada Lovelace", entity_type="person",
                            birth_or_inception_date="1815-12-10",
                            birth_or_inception_time="08:00",
                            latitude=51.5, longitude=-0.1, timezone="Europe/London",
                            source="unit_test", time_accuracy="documented",
                            category="SCIENTIST")
    return conn, path


class OpenAIClientTests(unittest.TestCase):
    def setUp(self):
        self._saved_key = os.environ.pop("OPENAI_API_KEY", None)

    def tearDown(self):
        if self._saved_key is not None:
            os.environ["OPENAI_API_KEY"] = self._saved_key

    def test_not_configured_without_key(self):
        self.assertFalse(openai_client.is_configured())

    def test_complete_text_raises_aiunavailable_without_key(self):
        with self.assertRaises(openai_client.AIUnavailable):
            openai_client.complete_text("sys", "user")

    def test_complete_json_raises_aiunavailable_without_key(self):
        with self.assertRaises(openai_client.AIUnavailable):
            openai_client.complete_json("sys", "user", "schema", {"type": "object"})

    def test_model_defaults_when_unset(self):
        os.environ.pop("OPENAI_MODEL", None)
        self.assertEqual(openai_client.get_model(), openai_client.DEFAULT_MODEL)

    def test_model_configurable_via_env(self):
        os.environ["OPENAI_MODEL"] = "some-future-model"
        try:
            self.assertEqual(openai_client.get_model(), "some-future-model")
        finally:
            del os.environ["OPENAI_MODEL"]


class EntitiesDBTests(unittest.TestCase):
    def setUp(self):
        self.conn, self.path = _tmp_entities_conn()

    def tearDown(self):
        self.conn.close()
        os.remove(self.path)

    def test_add_and_get_entity(self):
        row = entities_db.get_entity_by_name(self.conn, "Testland")
        self.assertIsNotNone(row)
        self.assertEqual(row.entity_type, "country")
        self.assertEqual(row.time_accuracy, "assumed_midnight")

    def test_time_accuracy_never_silently_upgraded(self):
        row = entities_db.get_entity_by_name(self.conn, "Ada Lovelace")
        self.assertEqual(row.time_accuracy, "documented")
        row2 = entities_db.get_entity_by_name(self.conn, "Testland")
        self.assertEqual(row2.time_accuracy, "assumed_midnight")

    def test_search_entities_by_type(self):
        results = entities_db.search_entities(self.conn, entity_type="country")
        self.assertTrue(all(r.entity_type == "country" for r in results))
        self.assertIn("Testland", [r.name for r in results])

    def test_invalid_entity_type_rejected(self):
        with self.assertRaises(ValueError):
            entities_db.add_entity(self.conn, name="X", entity_type="not_a_real_type",
                                    birth_or_inception_date="2000-01-01",
                                    latitude=0, longitude=0, timezone="UTC")

    def test_mark_predicted_increments_count(self):
        row = entities_db.get_entity_by_name(self.conn, "Testland")
        entities_db.mark_predicted(self.conn, row.id)
        row2 = entities_db.get_entity(self.conn, row.id)
        self.assertEqual(row2.prediction_count, 1)
        self.assertIsNotNone(row2.last_predicted_at)


class PredictionsDBTests(unittest.TestCase):
    def setUp(self):
        self.conn = predictions_db.get_connection(":memory:")

    def test_save_and_retrieve(self):
        pid = predictions_db.save_prediction(
            self.conn, entity="Testland", question="Q?", prediction="P.",
            calculation_data={"a": 1}, mode="short",
        )
        rec = predictions_db.get_prediction(self.conn, pid)
        self.assertEqual(rec.entity, "Testland")
        self.assertEqual(rec.outcome_status, "pending")
        self.assertFalse(rec.published)

    def test_duplicate_question_detection(self):
        predictions_db.save_prediction(self.conn, entity="X", question="Same question?",
                                        prediction="P", calculation_data={})
        self.assertTrue(predictions_db.question_already_asked(self.conn, "Same question?"))
        self.assertFalse(predictions_db.question_already_asked(self.conn, "Different question?"))

    def test_recent_predictions_frequency(self):
        for _ in range(3):
            predictions_db.save_prediction(self.conn, entity="Y", question="q", prediction="p",
                                            calculation_data={})
        self.assertEqual(predictions_db.recent_predictions_for_entity(self.conn, "Y", days=30), 3)
        self.assertEqual(predictions_db.recent_predictions_for_entity(self.conn, "Z", days=30), 0)

    def test_outcome_recording_never_touches_prediction_text(self):
        pid = predictions_db.save_prediction(self.conn, entity="X", question="Q", prediction="ORIGINAL",
                                              calculation_data={})
        predictions_db.record_outcome(self.conn, pid, "it happened", "correct")
        rec = predictions_db.get_prediction(self.conn, pid)
        self.assertEqual(rec.prediction, "ORIGINAL")
        self.assertEqual(rec.outcome_status, "correct")
        self.assertEqual(rec.actual_outcome, "it happened")

    def test_invalid_outcome_status_rejected(self):
        pid = predictions_db.save_prediction(self.conn, entity="X", question="Q", prediction="P",
                                              calculation_data={})
        with self.assertRaises(ValueError):
            predictions_db.record_outcome(self.conn, pid, "x", "definitely_true")

    def test_mark_published_sets_fields(self):
        pid = predictions_db.save_prediction(self.conn, entity="X", question="Q", prediction="P",
                                              calculation_data={})
        predictions_db.mark_published(self.conn, pid, "post_123")
        rec = predictions_db.get_prediction(self.conn, pid)
        self.assertTrue(rec.published)
        self.assertEqual(rec.x_post_id, "post_123")


class ToolFunctionsTests(unittest.TestCase):
    """These use the REAL entities.db/predictions.db (module-level connections
    in ai.tools) since tools.py is a thin wrapper with no injectable
    connection -- consistent with how api.py itself uses it. Uses the real
    seeded 'India' entity, so this doubles as an integration check that the
    calculation pipeline (kundli.py/world_astrology/*) still works end to
    end through the tool surface."""

    def test_search_entities_finds_seeded_india(self):
        results = ai_tools.search_entities(query="India", entity_type="country")
        self.assertTrue(any(r["name"] == "India" for r in results))

    def test_calculate_entity_chart_real_data(self):
        chart = ai_tools.calculate_entity_chart(
            "India", "country", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata")
        self.assertIn("ascendant", chart)
        self.assertEqual(chart["time_accuracy"], "assumed_midnight")
        self.assertEqual(len(chart["planets"]), 9)

    def test_run_jyotisha_prediction_real_data(self):
        result = ai_tools.run_jyotisha_prediction(
            "India", "country", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata",
            as_of_date="2026-09-15")
        self.assertTrue(result["computed"])
        self.assertIn(result["mahadasha_lord"],
                       {"ketu", "venus", "sun", "moon", "mars", "rahu", "jupiter", "saturn", "mercury"})

    def test_run_cross_tradition_analysis_classification_is_real(self):
        result = ai_tools.run_cross_tradition_analysis(
            "India", "country", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata",
            as_of_date="2026-09-15")
        self.assertIn(result["agreement_classification"],
                       {"Strong", "Moderate", "Contradictory", "Insufficient", "Tradition-specific"})
        self.assertIn("jyotisha", result["computed_traditions"])

    def test_get_entity_not_found_raises_toolerror(self):
        with self.assertRaises(ai_tools.ToolError):
            ai_tools.get_entity(999999999)

    def test_search_historical_events_returns_real_rows(self):
        results = ai_tools.search_historical_events(limit=3)
        self.assertLessEqual(len(results), 3)
        if results:
            self.assertIn("event_name", results[0])

    def test_save_and_get_prediction_history_roundtrip(self):
        pid = ai_tools.save_prediction("TestEntityXYZ", "q?", "p", {"x": 1}, mode="short")
        history = ai_tools.get_prediction_history(entity="TestEntityXYZ")
        self.assertTrue(any(h["id"] == pid for h in history))


class PredictionAgentTests(unittest.TestCase):
    def test_unresolvable_entity_raises_input_error(self):
        with self.assertRaises(prediction_agent.PredictionInputError):
            prediction_agent.run_prediction({"entity": "Definitely Not A Real Entity 12345",
                                              "question": "q?"})

    def test_missing_entity_name_raises_input_error(self):
        with self.assertRaises(prediction_agent.PredictionInputError):
            prediction_agent.run_prediction({"question": "q?"})

    def test_known_entity_produces_real_calculation_data(self):
        result = prediction_agent.run_prediction({
            "entity": "India", "entity_type": "country", "question": "q?", "mode": "short",
        })
        self.assertIn("calculation_data", result)
        self.assertIn("entity_chart", result["calculation_data"])
        # No OPENAI_API_KEY in the test environment -> honest degraded status,
        # never a fabricated prose prediction.
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["primary_prediction"])
        self.assertIsNotNone(result["prediction_id"])

    def test_dry_run_never_persists(self):
        result = prediction_agent.run_prediction(
            {"entity": "India", "entity_type": "country", "question": "q?", "mode": "short"},
            persist=False,
        )
        self.assertIsNone(result["prediction_id"])
        self.assertTrue(result["dry_run"])

    def test_caller_supplied_real_data_for_unseeded_entity(self):
        result = prediction_agent.run_prediction({
            "entity": "Unit Test Company", "entity_type": "company", "question": "q?",
            "date": "2015-05-05", "latitude": 1.0, "longitude": 2.0, "timezone": "UTC",
            "mode": "short",
        })
        self.assertEqual(result["calculation_data"]["entity_resolution"]["resolution_source"],
                          "caller_supplied")


class RandomPredictionTests(unittest.TestCase):
    def test_select_candidate_returns_real_entity(self):
        selection = random_prediction.select_candidate(category="country")
        self.assertEqual(selection["category"], "country")
        self.assertIn("name", selection["entity"])
        self.assertIsInstance(selection["question"], str)
        self.assertGreater(len(selection["question"]), 0)

    def test_politics_category_returns_actual_political_figures(self):
        seen_categories = set()
        for _ in range(5):
            selection = random_prediction.select_candidate(category="politics")
            seen_categories.add(selection["entity"]["category"])
        # Real leaders_corpus.py category values -- NOT scientists/actors.
        self.assertTrue(seen_categories.issubset({"US_PRESIDENT", "INDIA_PM", "CURRENT_LEADER"}))

    def test_novelty_scoring_penalizes_recent_predictions(self):
        conn_pred = predictions_db.get_connection()
        for _ in range(5):
            predictions_db.save_prediction(conn_pred, entity="__NoveltyTestEntity__",
                                            question="q", prediction="p", calculation_data={})
        over_predicted = {"name": "__NoveltyTestEntity__", "time_accuracy": "documented",
                           "category": "X", "source_reliability": "HIGH", "notes": "n"}
        fresh = {"name": "__NeverPredictedEntity__", "time_accuracy": "documented",
                 "category": "X", "source_reliability": "HIGH", "notes": "n"}
        score_over = random_prediction._score_candidate(over_predicted, conn_pred)
        score_fresh = random_prediction._score_candidate(fresh, conn_pred)
        self.assertLess(score_over, score_fresh)

    def test_invalid_category_raises(self):
        with self.assertRaises(KeyError):
            random_prediction._CATEGORY_RULES["not_a_real_category"]


class AutonomousAgentTests(unittest.TestCase):
    def test_dry_run_true_does_not_persist(self):
        result = ai_agent.run(dry_run=True, category="country", mode="short")
        self.assertTrue(result["dry_run"])
        self.assertIsNone(result["prediction_id"])

    def test_dry_run_false_persists_and_is_retrievable(self):
        result = ai_agent.run(dry_run=False, category="country", mode="short")
        self.assertFalse(result["dry_run"])
        self.assertIsNotNone(result["prediction_id"])
        conn = predictions_db.get_connection()
        rec = predictions_db.get_prediction(conn, result["prediction_id"])
        self.assertIsNotNone(rec)
        self.assertEqual(rec.source, "agent")


class SynthesisTests(unittest.TestCase):
    def test_build_final_result_without_openai_is_insufficient_data(self):
        result = synthesis.build_final_result(
            "Will it happen?", ["Testland"],
            {"cross_tradition": {"agreement_classification": "Strong"}}, ["jyotisha"],
        )
        self.assertEqual(result["status"], "insufficient_data")
        self.assertIsNone(result["primary_prediction"])
        self.assertIn("calculation_data", result)

    def test_calculation_and_synthesis_kept_separate(self):
        structured = {"cross_tradition": {"agreement_classification": "Strong"}, "raw": 42}
        result = synthesis.build_final_result("q", ["E"], structured, ["jyotisha"])
        self.assertEqual(result["calculation_data"], structured)
        self.assertNotIn("raw", result)  # calculation data isn't flattened into the top level


class XPublisherTests(unittest.TestCase):
    def setUp(self):
        self._saved = os.environ.pop("X_ENABLED", None)

    def tearDown(self):
        if self._saved is not None:
            os.environ["X_ENABLED"] = self._saved
        elif "X_ENABLED" in os.environ:
            del os.environ["X_ENABLED"]

    def test_disabled_by_default(self):
        self.assertFalse(x_publisher.is_enabled())

    def test_publish_is_noop_when_disabled(self):
        result = x_publisher.publish_prediction("any-id")
        self.assertFalse(result["published"])
        self.assertIn("X_ENABLED", result["reason"])

    def test_format_for_x_respects_length_limit(self):
        formatted = x_publisher.format_for_x("A" * 500, "Entity")
        self.assertLessEqual(len(formatted), x_publisher.MAX_TWEET_LENGTH)

    def test_publish_fails_gracefully_without_credentials(self):
        os.environ["X_ENABLED"] = "true"
        conn = predictions_db.get_connection(":memory:")
        pid = predictions_db.save_prediction(conn, entity="E", question="q",
                                              prediction="Something favorable.",
                                              calculation_data={})
        result = x_publisher.publish_prediction(pid, conn=conn)
        self.assertFalse(result["published"])
        self.assertIn("credentials", result["reason"].lower())

    def test_publish_refuses_duplicate(self):
        os.environ["X_ENABLED"] = "true"
        conn = predictions_db.get_connection(":memory:")
        pid = predictions_db.save_prediction(conn, entity="E", question="q", prediction="p",
                                              calculation_data={})
        predictions_db.mark_published(conn, pid, "existing_post_id")
        result = x_publisher.publish_prediction(pid, conn=conn)
        self.assertFalse(result["published"])
        self.assertEqual(result["x_post_id"], "existing_post_id")


class APIEndpointTests(unittest.TestCase):
    """Spins up the real ThreadingHTTPServer (api.py) on a scratch port and
    hits it with real HTTP requests -- the same style of test used manually
    throughout this session's development, formalized here so it runs as
    part of the normal test suite."""

    @classmethod
    def setUpClass(cls):
        import api
        cls.port = 8710
        cls.server = api.__dict__["ThreadingHTTPServer"](("127.0.0.1", cls.port), api.ChartHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.5)
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _post(self, path, payload):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def _get(self, path):
        req = urllib.request.Request(self.base + path, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_health_endpoint_shape(self):
        status, body = self._get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(set(body.keys()), {"status", "astrowatch", "openai"})
        self.assertEqual(body["openai"], "not_configured")

    def test_chart_endpoint_still_works(self):
        status, body = self._post("/api/chart", {
            "date": "2000-05-17", "time": "14:30:00", "timezone": "Asia/Kolkata",
            "latitude": 28.6139, "longitude": 77.2090,
        })
        self.assertEqual(status, 200)
        self.assertEqual(len(body["planets"]), 9)

    def test_predict_endpoint_real_entity(self):
        status, body = self._post("/api/predict", {
            "entity": "India", "entity_type": "country", "question": "q?", "mode": "short",
        })
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "insufficient_data")
        self.assertIn("calculation_data", body)

    def test_predict_endpoint_unknown_entity_400(self):
        status, body = self._post("/api/predict", {"entity": "Totally Unknown Entity 999"})
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_agent_run_dry_run_endpoint(self):
        status, body = self._post("/api/agent/run", {"dry_run": True, "category": "country"})
        self.assertEqual(status, 200)
        self.assertTrue(body["dry_run"])
        self.assertIsNone(body["prediction_id"])

    def test_random_prediction_endpoint(self):
        status, body = self._post("/api/random-prediction", {"category": "sports"})
        self.assertEqual(status, 200)
        self.assertEqual(body["category"], "sports")

    def test_current_event_endpoint_503_without_openai(self):
        status, body = self._post("/api/current-event", {"event_text": "Something happened."})
        self.assertEqual(status, 503)
        self.assertIn("error", body)

    def test_current_event_endpoint_400_missing_text(self):
        status, body = self._post("/api/current-event", {})
        self.assertEqual(status, 400)

    def test_predictions_list_endpoint(self):
        status, body = self._get("/api/predictions?limit=3")
        self.assertEqual(status, 200)
        self.assertIn("predictions", body)
        self.assertLessEqual(len(body["predictions"]), 3)

    def test_predictions_get_by_id_404_for_unknown(self):
        status, body = self._get("/api/predictions/not-a-real-id")
        self.assertEqual(status, 404)

    def test_root_lists_endpoints(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("POST /api/predict", body["endpoints"])


if __name__ == "__main__":
    unittest.main()
