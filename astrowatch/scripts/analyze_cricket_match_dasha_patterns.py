"""
Astrowatch -- pattern analysis over kundli_mass/cricket_match_dasha_dataset.csv.
===================================================================
Computes REAL, from-data win-rate breakdowns by Dasha/dignity feature over
the 806 real, eligible ODI matches (2015-2023) in
kundli_mass/cricket_match_dasha_dataset.csv (itself built by
scripts/build_cricket_match_dasha_dataset.py from the user-supplied real
match-result corpus, via this project's existing, unmodified Vimshottari
Dasha + dignity calculation pipeline).

NO FABRICATION: every number below is computed directly from the CSV. No
result is invented, rounded to a "nicer" figure, or omitted for not matching
expectation. Sample sizes are reported alongside every rate; per this
project's standing convention (see world_astrology/backtesting.py's
MIN_SAMPLE_SIZE_FOR_RATE), a subgroup below MIN_SAMPLE_FOR_CLAIM is reported
as raw counts only, with no "win rate" framing implied to be reliable.

SCIENTIFIC STATUS (read before citing any number from this script's output):
this is an OBSERVATIONAL, POST-HOC correlation over a fixed historical
dataset -- it is NOT a held-out, hindsight-protected backtest (that is
event_backtest/'s job, tested on the 6 World Cup finals specifically). A
correlation found here should be treated as a hypothesis worth testing on
new/held-out data, not as validated predictive signal, and never as evidence
astrology is scientifically predictive of cricket outcomes -- see
BACKTEST.md's disclaimer section.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_CSV = os.path.join(HERE, "kundli_mass", "cricket_match_dasha_dataset.csv")
MIN_SAMPLE_FOR_CLAIM = 20


def load_rows():
    with open(INPUT_CSV) as f:
        return list(csv.DictReader(f))


def _winner_is_team1(row) -> bool:
    return row["winner"].strip() == row["team1"].strip()


def analyze_score_comparison(rows, team1_field, team2_field, label):
    """Compares team1's score to team2's score (numeric fields, some rows
    have '' for None -- skipped).

    IMPORTANT: the raw source CSV has a strong Team-1-listing bias (Team 1
    wins 59.1% of matches overall in this corpus -- see baseline check below
    -- almost certainly because Team 1 is more often the home/host side, not
    because of anything astrological). A naive "team1_higher_score ->
    team1_won" breakdown would be CONFOUNDED by that listing bias. So this
    function reports the listing-order-INVARIANT rate: regardless of which
    side is labeled team1/team2, did the side with the HIGHER dignity score
    actually win the match? Ties (equal score) are reported separately and
    excluded from the rate."""
    higher_won, higher_total = 0, 0
    ties, tie_team1_won = 0, 0
    skipped = 0
    for r in rows:
        s1_raw, s2_raw = r[team1_field], r[team2_field]
        if s1_raw in ("", "None") or s2_raw in ("", "None"):
            skipped += 1
            continue
        s1, s2 = float(s1_raw), float(s2_raw)
        t1_won = _winner_is_team1(r)
        if s1 == s2:
            ties += 1
            tie_team1_won += 1 if t1_won else 0
            continue
        higher_total += 1
        higher_is_team1 = s1 > s2
        if higher_is_team1 == t1_won:
            higher_won += 1

    print(f"\n--- {label} ---")
    print(f"(skipped {skipped} rows with missing score on either side)")
    print(f"  ties (equal score, excluded from rate below): n={ties}, team1_won={tie_team1_won} ({tie_team1_won/ties:.1%} if ties>0 else 'n/a')" if ties else "  ties: n=0")
    if higher_total < MIN_SAMPLE_FOR_CLAIM:
        print(f"  higher-dignity-score side: n={higher_total} (below MIN_SAMPLE_FOR_CLAIM -- raw counts only: {higher_won} wins)")
    else:
        print(f"  higher-dignity-score side (listing-order-invariant): n={higher_total}, won {higher_won}/{higher_total} = {higher_won/higher_total:.1%}")


def analyze_dignity_category(rows, field, label):
    """Win rate for the team OWNING that dignity category (any team, either
    side of a match), regardless of opponent's dignity."""
    counts = defaultdict(lambda: {"won": 0, "total": 0})
    for r in rows:
        t1_won = _winner_is_team1(r)
        counts[r[f"team1_{field}"]]["total"] += 1
        counts[r[f"team1_{field}"]]["won"] += 1 if t1_won else 0
        counts[r[f"team2_{field}"]]["total"] += 1
        counts[r[f"team2_{field}"]]["won"] += 1 if not t1_won else 0

    print(f"\n--- {label} ---")
    for dignity, c in sorted(counts.items(), key=lambda kv: -kv[1]["total"]):
        if c["total"] < MIN_SAMPLE_FOR_CLAIM:
            print(f"  {dignity!r}: n={c['total']} (below MIN_SAMPLE_FOR_CLAIM -- raw counts only: {c['won']} wins)")
            continue
        print(f"  {dignity!r}: n={c['total']}, win rate {c['won']}/{c['total']} = {c['won']/c['total']:.1%}")


def main():
    rows = load_rows()
    print(f"Loaded {len(rows)} real, eligible matches from {INPUT_CSV}")

    analyze_score_comparison(rows, "team1_antardasha_lord_score", "team2_antardasha_lord_score",
                              "Antardasha-lord dignity score: higher side vs actual winner")
    analyze_score_comparison(rows, "team1_mahadasha_lord_score", "team2_mahadasha_lord_score",
                              "Mahadasha-lord dignity score: higher side vs actual winner")

    analyze_dignity_category(rows, "mahadasha_lord_dignity", "Win rate by own Mahadasha-lord dignity category")
    analyze_dignity_category(rows, "antardasha_lord_dignity", "Win rate by own Antardasha-lord dignity category")

    # Baseline: overall team1 win rate (sanity check for any systematic bias
    # in how the source CSV orders Team 1 / Team 2 -- e.g. home team listed first).
    t1_wins = sum(1 for r in rows if _winner_is_team1(r))
    print(f"\n--- Baseline ---")
    print(f"Team 1 (as listed in source CSV) won {t1_wins}/{len(rows)} = {t1_wins/len(rows):.1%} "
          f"(sanity check for listing-order bias; NOT an astrological finding)")


if __name__ == "__main__":
    main()
