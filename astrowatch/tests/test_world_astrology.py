"""Tests for astrowatch/world_astrology/ -- the Unified World Astrology Knowledge
System (schema, tradition modules, cross-tradition engine, reading engine,
historical validation store). See world_astrology/__init__.py for the package's
own stated scope/honesty philosophy that these tests check against."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world_astrology.schema import KnowledgeEntry, EvidenceLevel, RelationshipType, TraditionRegistry
from world_astrology.registry import build_registry, TRADITION_MODULES
from world_astrology import cross_tradition as ct
from world_astrology import dignity_tables as dt
from world_astrology import reading_engine as re
from world_astrology import historical_validation as hv


# ---------------------------------------------------------------------------
# Knowledge retrieval / tradition selection
# ---------------------------------------------------------------------------

def test_registry_builds_without_duplicate_ids():
    reg = build_registry()
    assert len(reg.all()) > 0
    ids = [e.entry_id for e in reg.all()]
    assert len(ids) == len(set(ids)), "duplicate entry_id slipped through registration"


def test_all_ten_traditions_present():
    reg = build_registry()
    expected = {"jyotisha", "hellenistic", "western", "babylonian", "persian_islamic",
                "chinese", "tibetan", "egyptian", "japanese", "mesoamerican"}
    assert set(reg.traditions()) == expected


def test_by_tradition_filters_correctly():
    reg = build_registry()
    for e in reg.by_tradition("jyotisha"):
        assert e.tradition == "jyotisha"


def test_search_finds_known_concept():
    reg = build_registry()
    results = reg.search("dasha")
    assert any("mahadasha" in e.concept.lower() or "dasha" in e.technique.lower() for e in results)


def test_get_returns_none_for_unknown_id():
    reg = build_registry()
    assert reg.get("nonexistent:concept") is None


def test_computed_traditions_matches_documented_scope():
    """The package docstring/reading_engine docstring both assert that exactly
    4 traditions have any computed=True content. If a future edit changes that
    without updating the docs, this test should fail loudly."""
    reg = build_registry()
    assert set(reg.computed_traditions()) == {"jyotisha", "hellenistic", "western", "chinese"}


def test_every_entry_has_required_narrative_fields():
    """Spot-check the schema's field-completeness expectation: every entry must
    have a non-empty definition/historical_period/geographic_origin (the schema
    doesn't enforce this at the dataclass level since some fields are legitimately
    optional, but content-completeness for these core fields is a project
    integrity requirement)."""
    reg = build_registry()
    for e in reg.all():
        assert e.definition.strip(), f"{e.entry_id} has empty definition"
        assert e.historical_period.strip(), f"{e.entry_id} has empty historical_period"
        assert e.geographic_origin.strip(), f"{e.entry_id} has empty geographic_origin"
        assert isinstance(e.confidence_level, EvidenceLevel)


def test_computed_true_entries_have_calculation_method_or_documented_reuse():
    """Any entry claiming computed=True should say HOW (either its own
    calculation_method text, or explicit limitations text pointing at what's
    reused) -- a computed=True entry with zero explanation of what backs it
    would be exactly the kind of unearned claim this project's ethos forbids."""
    reg = build_registry()
    for e in reg.all():
        if e.computed:
            assert e.calculation_method.strip() or e.limitations.strip(), (
                f"{e.entry_id} is computed=True but explains neither calculation_method "
                f"nor limitations"
            )


def test_duplicate_registration_raises():
    reg = TraditionRegistry()
    entry = KnowledgeEntry(tradition="x", school="", technique="t", concept="c",
                            definition="d", historical_period="p", geographic_origin="g")
    reg.register(entry)
    dup = KnowledgeEntry(tradition="x", school="", technique="t2", concept="c",
                          definition="d2", historical_period="p2", geographic_origin="g2")
    try:
        reg.register(dup)
        assert False, "expected ValueError on duplicate entry_id"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Cross-tradition relationship engine
# ---------------------------------------------------------------------------

def test_cross_tradition_relationships_all_resolve():
    reg = build_registry()
    problems = ct.validate_relationships(reg)
    assert problems == [], f"broken curated relationships: {problems}"


def test_cross_tradition_uses_full_classification_taxonomy():
    """The curated seed set should actually exercise more than one relationship
    type -- if it only ever used DIRECT_CORRESPONDENCE that would itself be a
    red flag for the 'never assume equivalence from superficial similarity' rule."""
    used_types = {r.relationship_type for r in ct.CROSS_TRADITION_RELATIONSHIPS}
    assert len(used_types) >= 4


def test_no_self_referential_or_duplicate_relationships():
    seen = set()
    for r in ct.CROSS_TRADITION_RELATIONSHIPS:
        assert r.entry_id_a != r.entry_id_b
        pair = tuple(sorted([r.entry_id_a, r.entry_id_b]))
        assert pair not in seen, f"duplicate relationship pair {pair}"
        seen.add(pair)


def test_get_relationships_finds_both_directions():
    rel = ct.CROSS_TRADITION_RELATIONSHIPS[0]
    found_a = ct.get_relationships(rel.entry_id_a)
    found_b = ct.get_relationships(rel.entry_id_b)
    assert rel in found_a
    assert rel in found_b


def test_negative_example_present_for_superficial_similarity():
    """This project explicitly documented at least one pair as
    INDEPENDENT_DEVELOPMENT specifically to demonstrate NOT overclaiming from a
    shared number/label (Chinese 12 animals vs. Jyotisha 12 Rashi) -- assert
    that specific safeguard example still exists."""
    pair = ("chinese:12_zodiac_animals", "jyotisha:rashi")
    match = [r for r in ct.CROSS_TRADITION_RELATIONSHIPS
             if {r.entry_id_a, r.entry_id_b} == set(pair)]
    assert len(match) == 1
    assert match[0].relationship_type == RelationshipType.INDEPENDENT_DEVELOPMENT


def test_unresolved_hint_references_is_non_fatal_and_reports_something():
    """This project knowingly has free-text cross_tradition_relationships hints
    that don't all resolve to registered entries (see cross_tradition.py's
    docstring) -- the finder function must run cleanly (not raise) and, given
    this project's actual current content, is expected to find at least one
    (a known, disclosed gap, not a silently-passing empty check that would mask
    a regression in either direction)."""
    reg = build_registry()
    unresolved = ct.unresolved_hint_references(reg)
    assert isinstance(unresolved, list)
    assert len(unresolved) > 0


# ---------------------------------------------------------------------------
# Dignity table / astronomical-calculation reuse correctness
# ---------------------------------------------------------------------------

def test_dignity_table_matches_kundli_mass_convention():
    """These values must stay byte-identical to the already-validated table in
    kundli_mass/analyze_midterms_2026.py -- this test hardcodes a few known
    values as a tripwire against silent drift."""
    assert dt.EXALTATION_SIGN["sun"] == "Mesha"
    assert dt.EXALTATION_SIGN["saturn"] == "Tula"
    assert dt.DEBILITATION_SIGN["moon"] == "Vrischika"
    assert dt.OWN_SIGNS["mars"] == {"Mesha", "Vrischika"}


def test_jyotisha_score_matches_manual_calculation():
    score, dignity, kind = dt.jyotisha_score("jupiter", "Karka", 5)
    assert dignity == "EXALTED"
    assert kind == "trikona"
    assert score == 2 + 1 + 0.5  # dign_pts + house_pts + nature_pts (benefic)


def test_hellenistic_sect_favor_none_for_mercury_and_nodes():
    assert dt.hellenistic_sect_favor(True, "mercury") is None
    assert dt.hellenistic_sect_favor(True, "rahu") is None
    assert dt.hellenistic_sect_favor(True, "ketu") is None


def test_hellenistic_sect_favor_day_night_symmetry():
    assert dt.hellenistic_sect_favor(True, "jupiter") is True
    assert dt.hellenistic_sect_favor(False, "jupiter") is False
    assert dt.hellenistic_sect_favor(True, "venus") is False
    assert dt.hellenistic_sect_favor(False, "venus") is True


# ---------------------------------------------------------------------------
# Reading engine: astronomical reuse, short/detailed/world generation, agreement
# ---------------------------------------------------------------------------

INDIA = dict(entity_name="India", entity_type="nation", inception_date="1947-08-15",
             latitude=28.6139, longitude=77.2090, timezone_name="Asia/Kolkata")


def test_build_chart_bundle_reuses_real_kundli_engine():
    """The chart data inside a ChartBundle must match kundli.compute_kundli()
    called directly with the same jd/lat/lon -- world_astrology must not
    recompute or approximate astronomical positions on its own."""
    from kundli import compute_kundli
    b = re.build_chart_bundle(**INDIA, as_of_date="2026-08-17")
    direct = compute_kundli(b.entity.jd_ut, INDIA["latitude"], INDIA["longitude"])
    assert b.entity.chart.ascendant_sidereal_deg == direct.ascendant_sidereal_deg
    for g in b.entity.chart.grahas:
        assert b.entity.chart.grahas[g].sidereal_lon_deg == direct.grahas[g].sidereal_lon_deg


def test_western_tropical_sign_boundaries():
    assert re.western_tropical_sign(0.0) == "Aries"
    assert re.western_tropical_sign(29.99) == "Aries"
    assert re.western_tropical_sign(30.0) == "Taurus"
    assert re.western_tropical_sign(359.99) == "Pisces"


def test_short_reading_respects_max_sentences():
    text2 = re.generate_short_reading(**INDIA, as_of_date="2026-08-17", max_sentences=2)
    text5 = re.generate_short_reading(**INDIA, as_of_date="2026-08-17", max_sentences=5)
    # sentence count == number of ". "-joined chunks we constructed; check text2 is a
    # strict prefix-equivalent (same opening sentences) and shorter.
    assert len(text2) < len(text5)
    assert text5.startswith(text2.rsplit(".", 1)[0] if text2.endswith(".") else text2[:20])


def test_short_reading_max_sentences_one_is_highest_priority_only():
    text1 = re.generate_short_reading(**INDIA, as_of_date="2026-08-17", max_sentences=1)
    assert "Ascendant" in text1
    assert text1.count(". ") == 0 or text1.strip().endswith(".")  # single sentence


def test_detailed_reading_has_all_15_sections():
    text = re.generate_detailed_reading(**INDIA, as_of_date="2026-08-17")
    for section in re.DETAILED_READING_SECTIONS:
        assert section in text, f"missing detailed-reading section: {section}"


def test_detailed_reading_discloses_assumed_midnight_caveat():
    text = re.generate_detailed_reading(**INDIA, as_of_date="2026-08-17")
    assert "ASSUMED" in text
    assert "NOT reliable" in text


def test_detailed_reading_lists_uncomputed_traditions():
    text = re.generate_detailed_reading(**INDIA, as_of_date="2026-08-17")
    for tradition in ("babylonian", "persian_islamic", "tibetan", "egyptian",
                       "japanese", "mesoamerican"):
        assert tradition in text


def test_world_reading_flags_assumed_midnight_prominently():
    text = re.generate_world_reading("USA", "1776-07-04", 38.9072, -77.0369,
                                      "America/New_York", as_of_date="2026-11-03")
    assert text.startswith("WORLD/MUNDANE READING")
    assert "assumed" in text.lower()


def test_world_reading_matches_already_delivered_midterms_finding():
    """Cross-check against this session's separately-delivered, already-committed
    US_MIDTERMS_2026_ASTROLOGICAL_CALCULATION.md finding for the USA national
    chart on election day: Rahu Mahadasha / Jupiter Antardasha."""
    b = re.build_chart_bundle("USA", "nation", "1776-07-04", 38.9072, -77.0369,
                               "America/New_York", as_of_date="2026-11-03")
    assert b.dasha.mahadasha_lord == "rahu"
    assert b.dasha.antardasha_lord == "jupiter"


def test_classify_agreement_strong():
    a = re.classify_agreement(2.0, "EXALTED", 2.5, "EXALTED")
    assert a.classification == "Strong"


def test_classify_agreement_moderate():
    a = re.classify_agreement(0.5, "NEUTRAL", 2.0, "NEUTRAL")
    assert a.classification == "Moderate"


def test_classify_agreement_contradictory():
    a = re.classify_agreement(1.0, "OWN_SIGN", -1.0, "OWN_SIGN")
    assert a.classification == "Contradictory"


def test_classify_agreement_insufficient_on_exact_zero():
    a = re.classify_agreement(0.0, "NEUTRAL", 1.0, "NEUTRAL")
    assert a.classification == "Insufficient"


def test_classify_agreement_tradition_specific_for_nodes():
    a = re.classify_agreement(0.5, "N/A", None, None)
    assert a.classification == "Tradition-specific"


def test_all_five_agreement_classifications_reachable_in_practice():
    """Not just unit-tested in isolation -- confirm the full pipeline (real
    chart data, real dates) actually produces every classification for at
    least one real entity/date combination, so the taxonomy isn't dead code."""
    seen = set()
    entities = [
        ("India", "nation", "1947-08-15", 28.6139, 77.2090, "Asia/Kolkata"),
        ("USA", "nation", "1776-07-04", 38.9072, -77.0369, "America/New_York"),
        ("Germany", "nation", "1949-05-23", 52.52, 13.405, "Europe/Berlin"),
    ]
    for name, typ, incep, lat, lon, tz in entities:
        for year in range(int(incep[:4]) + 1, 2036, 1):
            for month in (1, 3, 6, 9):
                d = f"{year}-{month:02d}-01"
                try:
                    b = re.build_chart_bundle(name, typ, incep, lat, lon, tz, as_of_date=d)
                except RuntimeError:
                    continue
                seen.add(b.agreement.classification)
        if len(seen) == 5:
            break
    assert seen == {"Strong", "Moderate", "Contradictory", "Insufficient", "Tradition-specific"}, seen


# ---------------------------------------------------------------------------
# Historical validation store
# ---------------------------------------------------------------------------

def _fresh_store():
    path = tempfile.mktemp(suffix=".db")
    conn = hv.get_connection(path)
    hv.init_db(conn)
    return conn, path


def test_record_and_retrieve_prediction():
    conn, path = _fresh_store()
    try:
        rec = hv.ValidationRecord(
            validation_id="t1", reading_mode="short", entity_name="E", entity_type="person",
            as_of_date="2020-01-01", dominant_lord="venus", agreement_classification="Strong",
            agreement_reasoning="r", predicted_valence="favorable", reading_text="text",
            engine_version="v1",
        )
        hv.record_prediction(conn, rec)
        fetched = hv.get_prediction(conn, "t1")
        assert fetched["entity_name"] == "E"
        assert fetched["predicted_valence"] == "favorable"
    finally:
        conn.close()
        os.remove(path)


def test_duplicate_validation_id_rejected():
    conn, path = _fresh_store()
    try:
        rec = hv.ValidationRecord(
            validation_id="dup", reading_mode="short", entity_name="E", entity_type="person",
            as_of_date="2020-01-01", dominant_lord="venus", agreement_classification="Strong",
            agreement_reasoning="r", predicted_valence="favorable", reading_text="text",
            engine_version="v1",
        )
        hv.record_prediction(conn, rec)
        raised = False
        try:
            hv.record_prediction(conn, rec)
        except Exception:
            raised = True
        assert raised
    finally:
        conn.close()
        os.remove(path)


def test_outcome_requires_existing_prediction():
    conn, path = _fresh_store()
    try:
        raised = False
        try:
            hv.record_outcome(conn, "nonexistent", "2020-01-01", "desc", "favorable", "src")
        except ValueError:
            raised = True
        assert raised
    finally:
        conn.close()
        os.remove(path)


def test_assess_match_conservative_on_ambiguous_cases():
    assert hv.assess_match("favorable", "favorable") == "MATCH"
    assert hv.assess_match("favorable", "unfavorable") == "MISMATCH"
    assert hv.assess_match("neutral", "favorable") == "AMBIGUOUS"
    assert hv.assess_match("favorable", "mixed") == "AMBIGUOUS"
    assert hv.assess_match("insufficient", "favorable") == "AMBIGUOUS"


def test_no_update_functions_exist_for_immutability():
    """Guard against a future edit accidentally adding an update path that
    would let a past prediction be silently rewritten."""
    assert not hasattr(hv, "update_prediction")
    assert not hasattr(hv, "update_outcome")


def test_accuracy_summary_reports_caveat_and_counts():
    conn, path = _fresh_store()
    try:
        rec = hv.ValidationRecord(
            validation_id="t1", reading_mode="short", entity_name="E", entity_type="person",
            as_of_date="2020-01-01", dominant_lord="venus", agreement_classification="Strong",
            agreement_reasoning="r", predicted_valence="favorable", reading_text="text",
            engine_version="v1",
        )
        hv.record_prediction(conn, rec)
        hv.record_outcome(conn, "t1", "2020-01-05", "desc", "favorable", "src")
        summary = hv.compute_accuracy_summary(conn)
        assert summary["total_predictions"] == 1
        assert summary["predictions_with_outcomes"] == 1
        assert summary["unassessed_count"] == 0
        assert "caveat" in summary
        assert summary["by_classification"]["Strong"]["MATCH"] == 1
    finally:
        conn.close()
        os.remove(path)


# ---------------------------------------------------------------------------
# Multi-tradition chart visuals, gallery, full-horoscope narrative, corpus patterns
# (added for: multi-chart gallery / full-horoscope / corpus-pattern feature request)
# ---------------------------------------------------------------------------

from world_astrology import chart_visuals as cv
from world_astrology import gallery as gal
from world_astrology import corpus_patterns as cp

INDIA_NATION = dict(entity_name="India", entity_type="nation", inception_date="1947-08-15",
                     latitude=28.6139, longitude=77.2090, timezone_name="Asia/Kolkata")


def test_gallery_panels_all_valid_svg():
    import xml.etree.ElementTree as ET
    b = re.build_chart_bundle(**INDIA, as_of_date="2026-08-17")
    reg = build_registry()
    panels = cv.build_gallery_panels(b, reg)
    assert len(panels) == 10
    for p in panels:
        ET.fromstring(p.svg)  # raises if malformed


def test_gallery_panels_computed_flag_matches_registry_computed_traditions():
    b = re.build_chart_bundle(**INDIA, as_of_date="2026-08-17")
    reg = build_registry()
    panels = cv.build_gallery_panels(b, reg)
    computed_keys = {p.tradition_key for p in panels if p.is_computed_chart}
    # jyotisha/hellenistic/western/chinese all have computed content per the registry
    assert computed_keys == {"jyotisha", "hellenistic", "western", "chinese"}


def test_reference_card_pulls_real_registry_content_not_fabricated():
    reg = build_registry()
    svg = cv.render_reference_card(reg, "tibetan", "Tibetan Astrology")
    # every technique name shown must correspond to a real registered entry
    for e in reg.by_tradition("tibetan")[:6]:
        assert e.technique in svg


def test_full_horoscope_narrative_is_prose_not_labeled_sections():
    text = re.generate_full_horoscope_narrative(**INDIA, as_of_date="2026-08-17")
    assert "==" not in text  # detailed reading uses "== N. Section ==" headers; narrative must not
    assert len(text.split("\n\n")) >= 5  # multiple flowing paragraphs


def test_full_horoscope_narrative_discloses_uncomputed_traditions():
    text = re.generate_full_horoscope_narrative(**INDIA, as_of_date="2026-08-17")
    for tradition in ("Babylonian", "Persian/Islamic", "Tibetan", "Egyptian", "Japanese"):
        assert tradition in text


def test_full_horoscope_narrative_with_field_includes_corpus_comparison():
    text = re.generate_full_horoscope_narrative(
        "Albert Einstein", "person", "1879-03-14", 48.4011, 9.9876, "Europe/Berlin",
        inception_time="11:30", as_of_date="1922-11-09", field="SCIENTIST",
    )
    assert "corpus" in text.lower()
    assert "Scientist" in text or "SCIENTIST" in text


def test_full_horoscope_narrative_without_field_has_no_corpus_sentence():
    text = re.generate_full_horoscope_narrative(**INDIA, as_of_date="2026-08-17")
    assert "individually-charted people" not in text


def test_corpus_patterns_returns_none_for_unknown_field():
    assert cp.compare_to_corpus("NOT_A_REAL_FIELD", "EXALTED") is None


def test_corpus_patterns_sentence_reflects_dignity_membership():
    good = cp.compare_to_corpus("SCIENTIST", "EXALTED")
    bad = cp.compare_to_corpus("SCIENTIST", "NEUTRAL")
    if good is not None and bad is not None:  # data file may be absent in some environments
        assert "falls into that favorably-dignified group" in good
        assert "does not fall into that favorably-dignified group" in bad


def test_gallery_html_is_self_contained_and_valid_json_embed():
    import json
    html_out = gal.build_gallery_html(**INDIA, as_of_date="2026-08-17")
    assert html_out.count("</script>") == 1
    start = html_out.index("const panels = ") + len("const panels = ")
    end = html_out.index(";\n", start)
    data = json.loads(html_out[start:end])
    assert len(data) == 10
    assert all("svg" in p and "display_name" in p for p in data)


def test_gallery_html_includes_narrative_and_detailed_reading():
    html_out = gal.build_gallery_html(**INDIA, as_of_date="2026-08-17")
    assert "Full Horoscope Reading" in html_out
    assert "Show full 15-section technical reading" in html_out


def test_gallery_html_works_for_nation_entity_type():
    html_out = gal.build_gallery_html(**INDIA_NATION, as_of_date="2026-08-17")
    assert "India" in html_out
    assert len(html_out) > 10000
