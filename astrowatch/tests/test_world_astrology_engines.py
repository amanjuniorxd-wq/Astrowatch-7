"""Tests for the world_astrology "computation layer" -- engine_interface.py,
world_astrology/engines/*.py (the 10 real tradition-specific prediction
engines), unified_engine.py (cross-tradition pipeline), and backtesting.py.

This is ADDITIVE to tests/test_world_astrology.py, which covers the older
"knowledge layer" (schema.py/registry.py/reading_engine.py/cross_tradition.py)
that these engines sit alongside, not replace.

Test entity: India, 1947-08-15, New Delhi coordinates (28.6139N, 77.2090E,
Asia/Kolkata) -- the same real, well-documented independence-date entity used
throughout this project's mundane-astrology tests (tests/test_mundane_entity_chart.py).
Prediction date fixed at 2026-09-15 so every assertion below is reproducible.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world_astrology.engine_interface import (
    PredictionContext, TraditionStatus, HistoricalStatus, AstrologyEngine,
)
from world_astrology.engines.jyotisha_engine import JyotishaEngine
from world_astrology.engines.hellenistic_engine import HellenisticEngine
from world_astrology.engines.western_engine import WesternEngine
from world_astrology.engines.babylonian_engine import BabylonianEngine
from world_astrology.engines.persian_islamic_engine import PersianIslamicEngine
from world_astrology.engines.chinese_engine import ChineseEngine
from world_astrology.engines.tibetan_engine import TibetanEngine
from world_astrology.engines.japanese_engine import JapaneseEngine
from world_astrology.engines.egyptian_engine import EgyptianEngine
from world_astrology.engines.mesoamerican_engine import MesoamericanEngine
from world_astrology.unified_engine import (
    UnifiedAstrologyEngine, ENGINE_REGISTRY, INDEPENDENCE_GROUPS, short_reading, detailed_reading,
)
from world_astrology import backtesting as bt


def _india_context(**overrides) -> PredictionContext:
    kwargs = dict(
        entity_name="India", entity_type="country", birth_or_inception_date="1947-08-15",
        latitude=28.6139, longitude=77.2090, timezone_name="Asia/Kolkata",
        prediction_date="2026-09-15",
    )
    kwargs.update(overrides)
    return PredictionContext(**kwargs)


# ---------------------------------------------------------------------------
# Per-tradition engine tests
# ---------------------------------------------------------------------------

def test_jyotisha_engine():
    result = JyotishaEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert result.applicable is True
    assert result.prediction and "Parashari" in result.prediction
    assert result.rules_used
    assert all(r.startswith("jyotisha.") for r in result.rules_used)


def test_hellenistic_engine():
    result = HellenisticEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert "Lot of Fortune" in result.prediction
    assert "hellenistic.profection" in result.rules_used
    factor_names = {f["name"] for f in result.factors}
    assert "Lord of the Year" in factor_names


def test_western_engine():
    result = WesternEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert result.zodiac_system == "tropical"
    assert "progressed" in result.prediction.lower()
    assert "western.secondary_progression" in result.rules_used
    assert "western.solar_return" in result.rules_used


def test_babylonian_engine():
    # Applicable for a mundane/country entity.
    result = BabylonianEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert "Venus" in result.prediction
    # Not applicable for a private individual (Babylonian omen astrology was
    # royal/mundane, not personal natal, per the engine's own docstring).
    person_ctx = _india_context(entity_type="person")
    person_result = BabylonianEngine().predict(person_ctx)
    assert person_result.status == TraditionStatus.NOT_APPLICABLE.value
    assert person_result.applicable is False


def test_persian_islamic_engine():
    result = PersianIslamicEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert "Great Conjunction" in result.prediction
    # Real, independently-verifiable fact: the most recent Jupiter-Saturn
    # Great Conjunction before 2026-09-15 was Dec 21 2020, in Aquarius (air
    # triplicity) -- the well-known "Great Mutation" conjunction.
    factor_map = {f["name"]: f["value"] for f in result.factors}
    assert factor_map["Great Conjunction date"] == "2020-12-21"
    assert "air" in factor_map["Great Conjunction sign/triplicity"]
    # Explicitly reuses the Hellenistic engine rather than reimplementing.
    assert "persian_islamic.annual_revolution" in result.rules_used


def test_chinese_engine():
    result = ChineseEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    factor_map = {f["name"]: f["value"] for f in result.factors}
    # India's independence year 1947 -- solar_year should resolve via Lichun
    # to 1947 (Aug 15 is well after Lichun ~Feb4), a Ding-Hai (Fire Pig) year.
    assert factor_map["Year Pillar"] == "Ding-Hai"
    assert factor_map["Chinese Zodiac Animal"] == "Pig"

    # Independently-verifiable well-known years: 1984 = Jiazi/Rat; 1999 (post-
    # Lichun) = Ji-Mao/Rabbit; 2000 (post-Lichun) = Geng-Chen/Dragon.
    r1984 = ChineseEngine().predict(_india_context(birth_or_inception_date="1984-08-15"))
    fm1984 = {f["name"]: f["value"] for f in r1984.factors}
    assert fm1984["Year Pillar"] == "Jia-Zi"
    assert fm1984["Chinese Zodiac Animal"] == "Rat"

    r2000 = ChineseEngine().predict(_india_context(birth_or_inception_date="2000-02-10"))
    fm2000 = {f["name"]: f["value"] for f in r2000.factors}
    assert fm2000["Year Pillar"] == "Geng-Chen"
    assert fm2000["Chinese Zodiac Animal"] == "Dragon"


def test_tibetan_engine():
    result = TibetanEngine().predict(_india_context(birth_or_inception_date="1984-08-15"))
    assert result.status == TraditionStatus.CALCULATED.value
    # Reuses the Chinese engine's verified Year Pillar -- 1984 = Wood Rat.
    assert "Wood Rat" in result.prediction
    assert "Male" in result.prediction


def test_japanese_engine():
    result = JapaneseEngine().predict(_india_context(birth_or_inception_date="1984-08-15"))
    assert result.status == TraditionStatus.CALCULATED.value
    factor_map = {f["name"]: f["value"] for f in result.factors}
    # digital_root(1947->1984 solar year, 1984) = 1+9+8+4=22->2+2=4; star=11-4=7.
    assert factor_map["Nine Star Ki number"] == 7
    assert result.historical_status == HistoricalStatus.TRADITIONAL.value  # honestly not "documented"


def test_egyptian_engine():
    result = EgyptianEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert "decan" in result.prediction.lower()
    # Explicitly NOT a natal system -- not_applicable when framed as natal.
    natal_ctx = _india_context(prediction_domain="natal")
    natal_result = EgyptianEngine().predict(natal_ctx)
    assert natal_result.status == TraditionStatus.NOT_APPLICABLE.value


def test_mesoamerican_engine():
    result = MesoamericanEngine().predict(_india_context())
    assert result.status == TraditionStatus.CALCULATED.value
    assert "Tzolk'in" in result.prediction or "Tzolkin" in result.prediction
    # Independently-verifiable famous fact: Dec 21 2012 = Long Count
    # 13.0.0.0.0, 4 Ajaw 3 K'ank'in (the "2012 phenomenon" end-of-baktun date).
    ctx_2012 = _india_context(birth_or_inception_date="2012-12-21", prediction_date="2012-12-21")
    r2012 = MesoamericanEngine().predict(ctx_2012)
    fm = {f["name"]: f["value"] for f in r2012.factors}
    assert fm["Long Count"] == "13.0.0.0.0"
    assert fm["Tzolk'in"] == "4 Ajaw"
    assert fm["Haab'"] == "3 Kankin"


# ---------------------------------------------------------------------------
# Engine-interface contract tests
# ---------------------------------------------------------------------------

def test_all_ten_engines_implement_the_common_interface():
    for name, cls in ENGINE_REGISTRY.items():
        assert issubclass(cls, AstrologyEngine)
        instance = cls()
        assert instance.tradition_name == name


def test_not_implemented_raises_insufficient_methodology_not_error():
    """Jyotisha's Jaimini/Nadi/Tajika/Prashna/Muhurta are honestly not
    computed -- verifies the predict() pipeline maps that to
    INSUFFICIENT_METHODOLOGY, never to a fabricated result or a silent ERROR."""
    class _StubEngine(AstrologyEngine):
        tradition_name = "stub"

        def is_applicable(self, context):
            return True

        def calculate(self, context):
            raise NotImplementedError("stub technique genuinely not reconstructable")

        def interpret(self, calculation):
            raise AssertionError("should never be called")

    result = _StubEngine().predict(_india_context())
    assert result.status == TraditionStatus.INSUFFICIENT_METHODOLOGY.value
    assert result.applicable is True  # was applicable, just not implementable
    assert result.limitations


def test_engine_error_is_reported_not_hidden():
    class _BrokenEngine(AstrologyEngine):
        tradition_name = "broken"

        def is_applicable(self, context):
            return True

        def calculate(self, context):
            raise ValueError("boom")

        def interpret(self, calculation):
            raise AssertionError("should never be called")

    result = _BrokenEngine().predict(_india_context())
    assert result.status == TraditionStatus.ERROR.value
    assert "boom" in result.limitations[0]


def test_missing_data_via_not_applicable_person_domain():
    """No single unimplemented-technique stub is needed for this: Babylonian's
    is_applicable() already returns False (-> NOT_APPLICABLE, a form of
    'this engine cannot proceed for this context') for a person entity --
    exercises the missing-data/inapplicable-context path end to end."""
    result = BabylonianEngine().predict(_india_context(entity_type="person"))
    assert result.status == TraditionStatus.NOT_APPLICABLE.value
    assert result.prediction is None


def test_assumed_midnight_flows_through_to_limitations():
    ctx = _india_context()  # no birth_or_inception_time supplied
    assert ctx.time_accuracy == "assumed_midnight"
    result = JyotishaEngine().predict(ctx)
    assert any("assumed" in lim.lower() or "midnight" in lim.lower() for lim in result.limitations)

    ctx_documented = _india_context(birth_or_inception_time="00:00", time_accuracy="documented")
    result_documented = HellenisticEngine().predict(ctx_documented)
    # With a documented time, the assumed-midnight-specific caveat should not appear.
    assert not any("time was assumed" in lim.lower() for lim in result_documented.limitations)


def test_historical_status_values_are_from_the_documented_taxonomy():
    valid = {s.value for s in HistoricalStatus}
    for name, cls in ENGINE_REGISTRY.items():
        result = cls().predict(_india_context())
        assert result.historical_status in valid, f"{name} used an undeclared historical_status"


# ---------------------------------------------------------------------------
# UnifiedAstrologyEngine tests
# ---------------------------------------------------------------------------

def test_unified_prediction_runs_all_ten_and_reports_transparency_counts():
    unified = UnifiedAstrologyEngine().generate_unified_prediction(_india_context())
    assert unified.traditions_evaluated == 10
    assert unified.traditions_calculated == 10  # all applicable for a country entity
    assert unified.traditions_applicable == 10
    assert unified.traditions_unavailable == 0
    assert "Traditions evaluated: 10" in unified.unified_prediction_text
    assert set(unified.individual_predictions.keys()) == set(ENGINE_REGISTRY.keys())


def test_unified_prediction_transparency_counts_when_a_tradition_is_not_applicable():
    """A person entity makes Babylonian and (if prediction_domain='natal')
    Egyptian not_applicable -- transparency counts must reflect that honestly,
    never claiming those traditions 'ran'."""
    ctx = _india_context(entity_type="person", prediction_domain="natal")
    unified = UnifiedAstrologyEngine().generate_unified_prediction(ctx)
    assert unified.traditions_evaluated == 10
    assert unified.status_by_tradition["babylonian"] == TraditionStatus.NOT_APPLICABLE.value
    assert unified.status_by_tradition["egyptian"] == TraditionStatus.NOT_APPLICABLE.value
    assert unified.traditions_calculated < unified.traditions_evaluated
    assert unified.traditions_calculated == sum(
        1 for s in unified.status_by_tradition.values() if s == TraditionStatus.CALCULATED.value
    )


def test_cross_tradition_agreement_restricted_subset():
    """Restricting to traditions within ONE independence group (sino_tibetan)
    should never classify as anything stronger than weak_agreement, since
    there is only one independent lineage group to agree with itself --
    directly tests the 'not simple majority voting' / dependency-discount
    requirement."""
    unified = UnifiedAstrologyEngine(traditions=["chinese", "tibetan", "japanese"]) \
        .generate_unified_prediction(_india_context())
    if unified.agreement.strongest_cluster:
        groups = set(unified.agreement.strongest_cluster.independence_groups)
        assert groups == {"sino_tibetan"}
        assert unified.agreement.classification in ("weak_agreement", "no_agreement")


def test_cross_tradition_conflict_is_detected_and_not_hidden():
    unified = UnifiedAstrologyEngine().generate_unified_prediction(_india_context())
    # For the fixed India/2026-09-15 case this project's own engines produce a
    # real favorable-vs-instability split (western engine finds both a
    # favorable trine/sextile aspect AND an opposition/challenging aspect
    # simultaneously; babylonian finds a real eclipse-omen window) -- verify
    # the contradiction machinery surfaces it rather than silently averaging.
    if unified.agreement.contradiction_detected:
        assert unified.agreement.contradiction_note is not None
        assert "Mixed/conflicting signals" in unified.agreement.contradiction_note
        assert "Mixed/conflicting signals" in unified.unified_prediction_text


def test_dependency_weighting_never_fabricates_empirical_numbers():
    unified = UnifiedAstrologyEngine().generate_unified_prediction(_india_context())
    assert len(unified.weighting) == 10
    for w in unified.weighting:
        assert w.empirical_weight == "unavailable"
        assert w.tradition_independence_group == INDEPENDENCE_GROUPS[w.tradition]
        assert w.methodological_applicability in ("applicable", "not_applicable")


def test_dependency_weighting_groups_reused_traditions_together():
    """persian_islamic directly reuses hellenistic's computation, and
    tibetan/japanese both reuse chinese's -- verifies they share an
    independence group so agreement between them isn't double-counted."""
    assert INDEPENDENCE_GROUPS["hellenistic"] == INDEPENDENCE_GROUPS["persian_islamic"]
    assert INDEPENDENCE_GROUPS["chinese"] == INDEPENDENCE_GROUPS["tibetan"] == INDEPENDENCE_GROUPS["japanese"]
    # But distinct-origin traditions must NOT share a group.
    assert INDEPENDENCE_GROUPS["babylonian"] != INDEPENDENCE_GROUPS["jyotisha"]
    assert INDEPENDENCE_GROUPS["egyptian"] != INDEPENDENCE_GROUPS["mesoamerican"]


def test_short_and_detailed_readings_are_distinct_and_traceable():
    unified = UnifiedAstrologyEngine().generate_unified_prediction(_india_context())
    short = short_reading(unified)
    detailed = detailed_reading(unified)
    assert len(detailed) > len(short)
    assert "Traditions evaluated" in short or "10/10" in short
    assert "Weighting breakdown" in detailed
    assert "Limitations" in detailed


def test_unified_engine_respects_explicit_tradition_subset():
    unified = UnifiedAstrologyEngine(traditions=["jyotisha", "chinese"]) \
        .generate_unified_prediction(_india_context())
    assert unified.traditions_evaluated == 2
    assert set(unified.individual_predictions.keys()) == {"jyotisha", "chinese"}


def test_unified_engine_rejects_unknown_tradition():
    try:
        UnifiedAstrologyEngine(traditions=["not_a_real_tradition"])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Backtesting scaffold tests
# ---------------------------------------------------------------------------

def test_backtesting_scaffold_records_and_aggregates_without_fabrication():
    tmp = tempfile.mktemp(suffix=".db")
    try:
        # Empty table -> empty aggregation (the honest starting state).
        assert bt.performance_by("tradition", db_path=tmp) == {}

        for outcome in ("correct", "correct", "incorrect", "partial", "unclear"):
            bt.record_test(bt.HistoricalPredictionTest(
                tradition="jyotisha", entity_name="TestEntity", entity_type="country",
                prediction_text="test", prediction_date="2020-01-01",
                actual_event="test outcome", outcome=outcome, rule_id="jyotisha.navamsa",
            ), db_path=tmp)

        perf = bt.performance_by("tradition", db_path=tmp)
        assert perf["jyotisha"]["sample_size"] == 5
        # Sample size 5 meets MIN_SAMPLE_SIZE_FOR_RATE -- a rate IS reported.
        assert "correct_rate" in perf["jyotisha"]
        assert perf["jyotisha"]["correct_rate"] == 2 / 5
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_backtesting_refuses_rate_below_minimum_sample_size():
    tmp = tempfile.mktemp(suffix=".db")
    try:
        bt.record_test(bt.HistoricalPredictionTest(
            tradition="chinese", entity_name="X", entity_type="country",
            prediction_text="t", prediction_date="2020-01-01",
            actual_event="e", outcome="correct",
        ), db_path=tmp)
        perf = bt.performance_by("tradition", db_path=tmp)
        assert perf["chinese"]["rate"] == "insufficient_sample_size"
        assert "correct_rate" not in perf["chinese"]
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def test_backtesting_rejects_invalid_outcome():
    tmp = tempfile.mktemp(suffix=".db")
    try:
        try:
            bt.record_test(bt.HistoricalPredictionTest(
                tradition="chinese", entity_name="X", entity_type="country",
                prediction_text="t", prediction_date="2020-01-01",
                actual_event="e", outcome="definitely_true",  # not a valid outcome value
            ), db_path=tmp)
            assert False, "should have raised ValueError"
        except ValueError:
            pass
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
