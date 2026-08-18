"""
Astrowatch -- Tarot reading engine
====================================
Draws cards (with reversal) from tarot_deck.db and lays them out into named spreads.
This is a genuinely random draw (Python's `random` module) -- there is no astrological
or predictive "calculation" involved in tarot the way there is in the rest of Astrowatch;
a tarot reading is a randomized prompt for reflection, not a computed forecast. This
module does not blend tarot draws with the kundli/Mahadasha engines elsewhere in the
project -- it is an independent, additive mode.
"""

import os
import random
import sqlite3
from dataclasses import dataclass
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "tarot_deck.db")

REVERSAL_PROBABILITY = 0.5


@dataclass
class DrawnCard:
    position_label: str
    name: str
    arcana: str
    suit: Optional[str]
    number: Optional[int]
    rank_name: Optional[str]
    astrology: Optional[str]
    element: str
    keywords: str
    reversed: bool
    meaning: str  # upright_meaning or reversed_meaning, whichever applies


SPREADS = {
    "single_card": ["The card"],
    "three_card": ["Past", "Present", "Future"],
    "celtic_cross": [
        "1. The situation", "2. The challenge", "3. The foundation (past)",
        "4. The recent past", "5. What crowns you (best outcome)",
        "6. The near future", "7. Your stance", "8. External influences",
        "9. Hopes and fears", "10. The final outcome",
    ],
}


def load_deck(db_path: str = DB_PATH) -> List[dict]:
    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"tarot_deck.db not found at {db_path} -- run build_tarot_deck.py first."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM tarot_cards").fetchall()
    conn.close()
    deck = [dict(r) for r in rows]
    if len(deck) != 78:
        raise ValueError(f"Expected 78 cards in tarot_deck.db, found {len(deck)}")
    return deck


def draw_spread(spread_name: str, rng: Optional[random.Random] = None,
                 db_path: str = DB_PATH) -> List[DrawnCard]:
    """Draws len(SPREADS[spread_name]) unique cards from the deck, each independently
    reversed with probability REVERSAL_PROBABILITY, and returns them labeled by position."""
    if spread_name not in SPREADS:
        raise ValueError(f"Unknown spread '{spread_name}'. Valid: {list(SPREADS)}")
    positions = SPREADS[spread_name]
    deck = load_deck(db_path)
    rng = rng or random.Random()

    chosen = rng.sample(deck, k=len(positions))
    results = []
    for position_label, card in zip(positions, chosen):
        is_reversed = rng.random() < REVERSAL_PROBABILITY
        meaning = card["reversed_meaning"] if is_reversed else card["upright_meaning"]
        results.append(DrawnCard(
            position_label=position_label,
            name=card["name"],
            arcana=card["arcana"],
            suit=card["suit"],
            number=card["number"],
            rank_name=card["rank_name"],
            astrology=card["astrology"],
            element=card["element"],
            keywords=card["keywords"],
            reversed=is_reversed,
            meaning=meaning,
        ))
    return results


def describe_spread(spread_name: str, drawn: List[DrawnCard]) -> str:
    lines = [f"Tarot reading -- {spread_name.replace('_', ' ').title()}", ""]
    for card in drawn:
        orientation = "Reversed" if card.reversed else "Upright"
        lines.append(f"{card.position_label}: {card.name} ({orientation})")
        lines.append(f"  {card.meaning}")
        lines.append("")
    lines.append(
        "Astrological calculation only note does not apply here -- tarot is a randomized "
        "reflective prompt, not a computed forecast. For entertainment and self-reflection."
    )
    return "\n".join(lines)


if __name__ == "__main__":
    for spread in SPREADS:
        drawn = draw_spread(spread, rng=random.Random(42))
        print(describe_spread(spread, drawn))
        print("=" * 60)
