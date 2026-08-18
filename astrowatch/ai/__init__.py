"""
Astrowatch Online -- AI intelligence/orchestration/synthesis layer.
=====================================================================
This package NEVER computes astronomical or astrological data itself. It only:
  - understands natural-language prediction questions and current-event text
    (entity_resolver.py, event_scanner.py),
  - selects what to analyze next (random_prediction.py),
  - orchestrates calls into the existing, authoritative Astrowatch engine via
    a fixed tool surface (tools.py -- get_entity, calculate_entity_chart,
    run_jyotisha_prediction, run_cross_tradition_analysis, etc., each a thin
    wrapper around a real, pre-existing function in kundli.py, mahadasha.py,
    mundane/entity_chart.py, world_astrology/*, historical/*, forecast.py),
  - and turns the resulting STRUCTURED calculation output into natural-language
    prose (synthesis.py).

Every module in this package fails gracefully, not silently-wrong, when
OPENAI_API_KEY is unset or the openai package/API call is unavailable: pure
calculation endpoints (POST /api/chart and the tools.py wrappers themselves)
keep working; only the AI-synthesis-dependent paths return a clear
"ai_unconfigured" / "insufficient_data" response. See openai_client.py.
"""
