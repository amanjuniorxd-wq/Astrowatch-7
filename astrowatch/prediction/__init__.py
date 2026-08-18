"""
Astrowatch -- prediction package.
===================================================================
The Vedic-astrology-based candidate-ranking prediction engine used by
event_backtest/ (and reusable for live, non-backtest predictions). Every
astronomical/astrological calculation here is a THIN WRAPPER around this
project's existing, already-validated engines (kundli.py, mahadasha.py,
mundane/entity_chart.py, mundane/dasha_timeline.py,
world_astrology/dignity_tables.py, world_astrology/reading_engine.py) --
nothing in this package computes planetary positions, dignities, or Dasha
timing itself.
"""
