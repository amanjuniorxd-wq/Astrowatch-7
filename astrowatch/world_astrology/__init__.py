"""
Astrowatch -- World Astrology Knowledge System.
=================================================
A modular knowledge architecture for studying, organizing, comparing, and applying
knowledge from multiple independent world astrological/celestial-divination
traditions, built on top of (not replacing) this project's existing, already-
validated astronomical/Jyotisha engine (kundli.py, mahadasha.py, rashi_nakshatra.py,
mundane/entity_chart.py) and existing cited-rule registry (rule_registry.py).

SCOPE HONESTY (read before extending or trusting any tradition module's depth):
This package treats each tradition as a distinct knowledge domain (schema.py) and
provides a real, working cross-tradition comparison + reading engine (cross_tradition.py,
reading_engine.py). But the DEPTH of populated content is intentionally uneven and
explicitly labeled per module:
  - Jyotisha (Indian) and, to a lesser extent, Hellenistic: substantial, because this
    project already has a real, tested, Swiss-Ephemeris-backed computational engine
    for them (whole-sign houses, sect, Vimshottari Dasha, Panchanga, etc.) built and
    validated in earlier phases of this project.
  - Western (modern): the concepts are documented but only the parts this project can
    actually compute (tropical placements) are wired to real numbers; transits/
    progressions/synastry/composite charts are catalogued as concepts, not computed.
  - Babylonian, Persian/Islamic, Chinese, Tibetan, Egyptian, Japanese, Mesoamerican:
    SEED-LEVEL only. A small number of well-established reference facts per
    tradition (spot-checked, not each individually re-verified against primary
    sources this session), explicitly NOT a full technique library, and with NO
    computational reading engine unless a specific calculation was verified correct
    (see each module's own docstring for exactly what is/isn't computed).
Building genuine, properly-sourced technique libraries for all 11 traditions at the
depth the original request describes is a multi-week scholarly research undertaking,
not something this session fabricates to appear complete -- every module here says,
in its own docstring, exactly how deep it actually goes.
"""
