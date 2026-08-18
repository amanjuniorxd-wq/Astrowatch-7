"""
Astrowatch — end-to-end pipeline demo (MVP-1)
===========================================
ASTRONOMICAL DATA -> CONFIGURATION -> RULE REGISTRY SEARCH -> MATCHES -> report

This wires the other modules together and shows the intended call sequence for a
historical backtest. It is a DEMONSTRATION with hand-entered sample longitudes, not a
live run (no local execution environment this session -- see README.md). Replace the
SAMPLE_POSITIONS block with real ephemeris_client output + coordinates.py conversion
before treating any output as meaningful.

Usage (once you have a working Python environment):
    python pipeline.py
"""

from aspects import detect_aspects, classify_grahayuddha
from rule_matcher import match_grahayuddha_rules, format_match_report
from coordinates import ra_dec_to_ecliptic, julian_day


def demo_with_sample_positions():
    """
    SAMPLE / PLACEHOLDER longitudes -- NOT a real historical or current configuration.
    These exist only to prove the aspect-detection -> rule-matching wiring works.
    Do not read anything astrological into these numbers.
    """
    sample_ecliptic_longitudes = {
        "saturn": 10.0,
        "venus": 10.4,   # ~0.4 deg from Saturn -> should trip "bheda" (closest class)
        "mars": 95.0,
        "jupiter": 190.0,
    }

    grahayuddha_classes = classify_grahayuddha(sample_ecliptic_longitudes)
    print("Detected graha-yuddha classes (PLACEHOLDER thresholds -- see aspects.py):")
    for c in grahayuddha_classes:
        print(f"  {c.body_a} vs {c.body_b}: {c.conjunction_class} (sep={c.separation_deg:.3f} deg)")

    matches = match_grahayuddha_rules(
        grahayuddha_classes,
        defeated_body={"saturn_vs_venus": "saturn"},  # hand-asserted for demo purposes only
    )
    print("\nRule matches:\n")
    print(format_match_report(matches))

    print("\nPtolemaic-style aspects (default placeholder orbs):")
    aspects_found = detect_aspects(sample_ecliptic_longitudes)
    for a in aspects_found:
        print(f"  {a.body_a}-{a.body_b}: {a.aspect} (sep={a.actual_separation:.2f}, "
              f"orb {a.orb_used} via {a.orb_table_name})")


def demo_coordinate_conversion():
    # A single hand-worked example using approximate Sun RA/Dec for 12 Aug 2026,
    # taken from this session's earlier live theskylive.com fetch (09h26m35s, +15 03'07").
    ra = (9 + 26/60 + 35/3600) * 15.0
    dec = 15 + 3/60 + 7/3600
    jd = julian_day(2026, 8, 12, 12.0)
    pos = ra_dec_to_ecliptic(ra, dec, jd)
    print(f"\nSun on 2026-08-12 (from live R.A./Dec. fetched this session):")
    print(f"  ecliptic longitude = {pos.longitude_deg:.3f} deg  ->  {pos.sign} {pos.degree_in_sign:.2f} deg")
    print(f"  ecliptic latitude  = {pos.latitude_deg:.4f} deg  (expect ~0 for the Sun -- sanity check)")


if __name__ == "__main__":
    demo_coordinate_conversion()
    print()
    demo_with_sample_positions()
