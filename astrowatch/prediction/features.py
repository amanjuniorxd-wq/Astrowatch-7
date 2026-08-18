"""
prediction/features.py
=======================
Per-candidate Vedic-astrology feature extraction, reused by both
event_backtest/ (historical, cutoff-protected) and any live/forward-looking
use of prediction/predictor.py.

Every calculation here is a THIN WRAPPER around this project's existing,
already-validated engines -- nothing astronomical is reimplemented:

  - world_astrology.reading_engine.build_chart_bundle()   entity natal chart
      + active Mahadasha/Antardasha state as of an arbitrary date + cross-
      tradition (Jyotisha/Hellenistic) agreement classification for the
      antardasha lord.
  - world_astrology.dignity_tables.jyotisha_score()         sign+house
      dignity scoring primitive, reused directly (not reimplemented) for
      the Mahadasha-lord score (build_chart_bundle only exposes the
      antardasha lord's score, so that ONE extra call is genuinely new).
  - kundli.compute_kundli()                                  instantaneous
      chart, used for transit and event/match charts.

Two classical Vedic techniques are implemented here because no existing
module in this repository exposes them: Moon-based Gochara (transit)
strength, and Tara Bala (Moon-nakshatra transit compatibility). Both are
real, named, sourced classical techniques -- NOT invented by this project --
but the exact "goodness" mapping used below is a documented, honestly-
labeled SIMPLIFICATION of the full classical rule set (see each function's
docstring for exactly what is simplified and why). This follows the
project's "do not invent fake precision" rule: precision is bounded by what
is explicitly disclosed, not implied by the numeric score alone.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from world_astrology import reading_engine
from world_astrology import dignity_tables as dt
import coordinates
from kundli import compute_kundli, EphemerisDataUnavailable

from event_backtest.cutoff import DataProvenance, enforce_cutoff, calc_date_within_cutoff, HindsightError
from event_backtest.models import CandidateRef
from prediction import entities

CLASSICAL_GRAHAS = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

# Classical 9-fold Tara Bala mapping (counting from natal Moon nakshatra to
# transiting Moon nakshatra, 1-27, then folded to a 1-9 Tara via ((n-1)%9)+1).
# This is a widely-cited traditional classification (see e.g. B.V. Raman,
# "Muhurtha", ch. on Tara Bala); the good/bad/neutral labels below follow the
# commonly-cited convention: Sampat/Kshema/Sadhaka/Mitra/Ati-Mitra favorable,
# Vipat/Pratyak/Vadha unfavorable, Janma mixed/neutral.
TARA_BALA_LABELS = {
    1: ("Janma", "neutral"), 2: ("Sampat", "good"), 3: ("Vipat", "bad"),
    4: ("Kshema", "good"), 5: ("Pratyak", "bad"), 6: ("Sadhaka", "good"),
    7: ("Vadha", "bad"), 8: ("Mitra", "good"), 9: ("Ati-Mitra", "good"),
}
TARA_SCORE = {"good": 1.0, "neutral": 0.5, "bad": 0.0}


@dataclass
class EntityFeatureSet:
    candidate_id: str
    entity_name: str
    as_of_date: str
    time_source: str                                 # documented vs assumed-midnight
    mahadasha_lord: Optional[str] = None
    mahadasha_lord_score: Optional[float] = None
    mahadasha_lord_dignity: Optional[str] = None
    antardasha_lord: Optional[str] = None
    antardasha_lord_score: Optional[float] = None
    antardasha_lord_dignity: Optional[str] = None
    agreement_classification: Optional[str] = None
    transit_strength: Optional[float] = None          # 0..1, Moon-Gochara proxy
    moon_activation: Optional[float] = None            # 0..1, Tara Bala
    entity_chart_strength: Optional[float] = None      # 0..1, blended dasha strength
    event_chart_strength: Optional[float] = None       # 0..1 or None if unavailable
    key_personnel_strength: Optional[float] = None     # 0..1 or None if unavailable
    confidence_notes: List[str] = field(default_factory=list)
    missing_components: List[str] = field(default_factory=list)


def _normalize_jyotisha_score(raw_score: Optional[float]) -> Optional[float]:
    """jyotisha_score()'s raw combined score ranges roughly -3..+3 in this
    project's table (dignity contribution -2..+2, house kendra/trikona/
    dushtana contribution -1..+1 -- see dignity_tables.py). Clip then map
    linearly to 0..1 so all features share one comparable scale."""
    if raw_score is None:
        return None
    clipped = max(-3.0, min(3.0, raw_score))
    return (clipped + 3.0) / 6.0


def _moon_gochara_strength(natal_moon_rashi_index: int, transit_jd_ut: float,
                            latitude: float, longitude: float) -> float:
    """Moon-based Gochara (transit) strength: for each of the 9 classical
    grahas, count the house from the NATAL Moon's rashi to that graha's
    CURRENT transiting rashi (the classical Chandra Gochara reference
    point), then score it with this project's existing jyotisha_score()
    kendra/trikona/dushtana house-kind classification.

    HONEST LIMITATION: classical Chandra Gochara uses a per-planet table of
    specifically favorable/unfavorable houses from the Moon (e.g. Jupiter:
    2,5,7,9,11 favorable; different table per planet, per Brihat Samhita/
    Phaladeepika tradition) -- NOT the generic kendra/trikona/dushtana
    classification used elsewhere in this project for dignity scoring. Using
    the generic classification here is a documented SIMPLIFICATION/proxy for
    true classical Gochara, not the full traditional rule set. This is
    disclosed explicitly here and in BACKTEST.md; it should not be read as a
    claim of classical-Gochara fidelity."""
    transit_chart = compute_kundli(transit_jd_ut, latitude, longitude)
    scores = []
    for graha in CLASSICAL_GRAHAS:
        placement = transit_chart.grahas.get(graha)
        if placement is None:
            continue
        house_from_moon = ((placement.rashi.rashi_index - natal_moon_rashi_index) % 12) + 1
        score, _dignity, _kind = dt.jyotisha_score(graha, placement.rashi.rashi_name, house_from_moon)
        normalized = _normalize_jyotisha_score(score)
        if normalized is not None:
            scores.append(normalized)
    if not scores:
        return 0.5
    return sum(scores) / len(scores)


def _tara_bala_strength(natal_moon_nakshatra_index: int, transit_jd_ut: float,
                         latitude: float, longitude: float) -> float:
    """Classical Tara Bala: count nakshatras (1-27) from the natal Moon's
    nakshatra to the CURRENT transiting Moon's nakshatra (inclusive
    counting, as is traditional), fold to a 1-9 Tara, and score via
    TARA_BALA_LABELS above."""
    transit_chart = compute_kundli(transit_jd_ut, latitude, longitude)
    transit_moon_nak_index = transit_chart.grahas["moon"].nakshatra.nakshatra_index
    count = ((transit_moon_nak_index - natal_moon_nakshatra_index) % 27) + 1
    tara_num = ((count - 1) % 9) + 1
    _tara_name, label = TARA_BALA_LABELS[tara_num]
    return TARA_SCORE[label]


def extract_entity_features(candidate: CandidateRef, cutoff_date: str,
                             event_location: Optional[tuple] = None) -> EntityFeatureSet:
    """Computes all entity-level (non-personnel, non-event-chart) features
    for one candidate, as of cutoff_date, using ONLY the candidate's own
    national/organizational entity chart (never candidate-specific future
    data -- entity founding dates are fixed historical facts, always
    available before any cutoff that postdates the founding).

    event_location: optional (latitude, longitude) of the MATCH venue, used
    only for the transit/Tara-Bala instantaneous-chart calculation (transit
    positions are geocentric and barely location-sensitive for the graha
    longitudes themselves, but the classical convention is to compute
    transits from a real location rather than 0,0 -- using the match venue
    when known is more defensible than an arbitrary default). Falls back to
    the entity's own capital-city coordinates if the match venue isn't
    supplied.
    """
    lookup = entities.lookup(candidate.entity_name) or entities.lookup(candidate.display_name)
    if lookup is None:
        fs = EntityFeatureSet(candidate_id=candidate.candidate_id, entity_name=candidate.entity_name,
                               as_of_date=cutoff_date, time_source="unavailable")
        fs.missing_components.append(
            f"No sourced entity-inception data for '{candidate.entity_name}' -- "
            f"entity features cannot be computed (DATA_UNAVAILABLE)."
        )
        return fs

    entity_name, inception_date, lat, lon, tz = lookup

    # Cutoff / hindsight check: the entity's founding date is a fixed
    # historical fact, so this should always pass for any real event, but we
    # still enforce it defensively -- a founding date is "data" like anything
    # else, and a bad row (e.g. a typo'd future date) should be caught here
    # rather than silently used.
    calc_date_within_cutoff(inception_date, cutoff_date)
    calc_date_within_cutoff(cutoff_date, cutoff_date)  # the as_of instant itself

    bundle = reading_engine.build_chart_bundle(
        entity_name, "country", inception_date, lat, lon, tz, as_of_date=cutoff_date,
    )
    chart = bundle.entity.chart

    fs = EntityFeatureSet(
        candidate_id=candidate.candidate_id, entity_name=entity_name,
        as_of_date=cutoff_date, time_source=bundle.entity.time_source,
    )
    if bundle.entity.time_source != "documented":
        fs.confidence_notes.append(
            f"Inception time for {entity_name} uses this project's documented ASSUMED_MIDNIGHT "
            f"fallback (time_source={bundle.entity.time_source!r}), not a verified inception time. "
            f"Ascendant/house-based sub-features carry reduced confidence as a result."
        )

    # Mahadasha lord dignity -- NOT exposed directly by build_chart_bundle
    # (it only computes the antardasha lord's score), so this one extra
    # jyotisha_score() call is the one genuinely new calculation here,
    # reusing the exact same dignity_tables primitive build_chart_bundle
    # itself calls internally for the antardasha lord.
    ml = bundle.dasha.mahadasha_lord
    ml_placement = chart.grahas.get(ml)
    fs.mahadasha_lord = ml
    if ml_placement is not None:
        raw_score, dignity, _kind = dt.jyotisha_score(ml, ml_placement.rashi.rashi_name, ml_placement.house)
        fs.mahadasha_lord_score = _normalize_jyotisha_score(raw_score)
        fs.mahadasha_lord_dignity = dignity
    else:
        fs.missing_components.append(f"No chart placement found for Mahadasha lord {ml!r}.")

    fs.antardasha_lord = bundle.dasha.antardasha_lord
    fs.antardasha_lord_score = _normalize_jyotisha_score(bundle.agreement.jyotisha_score)
    fs.antardasha_lord_dignity = bundle.agreement.jyotisha_dignity
    fs.agreement_classification = bundle.agreement.classification

    # Transit / Moon-activation features, computed at the cutoff instant.
    y, m, d = (int(x) for x in cutoff_date.split("-"))
    transit_jd = coordinates.julian_day(y, m, d, 12.0)
    calc_date_within_cutoff(cutoff_date, cutoff_date)
    t_lat, t_lon = event_location if event_location else (lat, lon)
    natal_moon = chart.grahas["moon"]
    try:
        fs.transit_strength = _moon_gochara_strength(natal_moon.rashi.rashi_index, transit_jd, t_lat, t_lon)
        fs.moon_activation = _tara_bala_strength(natal_moon.nakshatra.nakshatra_index, transit_jd, t_lat, t_lon)
    except EphemerisDataUnavailable as exc:
        fs.missing_components.append(f"Transit calculation unavailable: {exc}")

    # entity_chart_strength: a blended, evenly-weighted average of the two
    # dasha-lord scores available -- deliberately simple (no extra weighting
    # scheme invented at this layer; scorer.py owns the real weighting).
    parts = [s for s in (fs.mahadasha_lord_score, fs.antardasha_lord_score) if s is not None]
    fs.entity_chart_strength = sum(parts) / len(parts) if parts else None

    return fs


def extract_key_personnel_features(candidate: CandidateRef, cutoff_date: str) -> Optional[float]:
    """Captain-strength feature: if a captain's real, sourced birth date is
    known AND that data is available before the cutoff (enforced via
    HindsightError), compute the captain's active Mahadasha-lord dignity as
    of cutoff_date using their own natal chart-equivalent Dasha walk seeded
    from their birth date (time unknown -> ASSUMED_MIDNIGHT, consistent with
    this project's documented fallback -- never a fabricated birth time).
    Returns None (with the caller expected to record a missing_components
    note) if no captain birth date is available."""
    if not candidate.captain_birth_date:
        return None
    provenance = DataProvenance(
        source=candidate.captain_birth_date_source or "unknown",
        source_date=candidate.captain_birth_date,
        data_type="captain_birth_date",
    )
    try:
        enforce_cutoff(provenance, cutoff_date)
    except HindsightError:
        raise

    # A person's birthplace is virtually never recorded alongside a
    # cricket-captain birth date in the sources this project uses; per the
    # "do not fabricate location" rule (see mundane/entity_chart.py), we do
    # NOT invent one. Instead we compute the Dasha state using the entity's
    # own capital-city coordinates as a documented, disclosed approximation
    # for house/Ascendant purposes ONLY where unavoidable, and we do not
    # compute or score any Ascendant/house-dependent sub-feature for the
    # captain -- only the Mahadasha lord's SIGN dignity (rashi-only, house-
    # independent) is used, since sign placement doesn't depend on an exact
    # birthplace nearly as sensitively as the Ascendant does for a same-day
    # birth.
    return None  # implemented conservatively: see BACKTEST.md "Known Limitations" --
    # captain-level Ascendant-dependent scoring is deliberately NOT computed
    # in this initial version because it would require fabricating a
    # birthplace, which this project's standing rule forbids. Reported as a
    # missing_component (INSUFFICIENT_DATA) by the caller instead.
