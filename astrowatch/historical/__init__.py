"""
Astrowatch — historical event database package.

ARCHITECTURAL BOUNDARY (read this before touching anything in this package):
This package is constructed and populated WITHOUT any dependency on Astrowatch's
astrology code. It must never import ayanamsha, panchang, rashi_nakshatra,
rule_registry, aspects, engines, forecast, or rule_matcher -- and none of those
modules may import from this package either. The dependency direction is:

    historical event (researched independently)
            |
            v
    historical_events.db   <-- THIS PACKAGE (read/write boundary)
            |
            v
    [future, not built here] backtest engine reads via repository.get_events()
            |
            v
    astronomical engine (ephemeris_client.py, ayanamsha.py, panchang.py,
    rashi_nakshatra.py, rule_registry.py) -- all pre-existing, untouched by this
    package

If you find yourself importing anything astrology-related into this package, or
selecting/filtering/removing events based on whether a rule "predicts" them, stop --
that is exactly the failure mode this package's tests
(tests/historical/test_astrological_independence.py) are designed to catch.
"""
