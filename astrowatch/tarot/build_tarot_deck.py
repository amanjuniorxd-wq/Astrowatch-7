"""
Astrowatch -- build tarot_deck.db
==================================
Assembles the 78-card tarot deck database from:
  - card_metadata.py    -- structure + traditional astrology/element/keyword correspondences
  - original_meanings.py -- Astrowatch's own original upright/reversed interpretive text

Run: python3 astrowatch/tarot/build_tarot_deck.py

PROVENANCE: card structure and correspondences were cross-checked against a real tarot
reference book supplied by the project owner (Liz Dean, "The Ultimate Guide to Tarot",
Fair Winds Press, 2015) for accuracy and completeness. No prose from that book is stored
in this database -- upright_meaning/reversed_meaning are original text written for this
project (see original_meanings.py docstring). Each row's source_note records this plainly.
"""

import os
import sqlite3

from card_metadata import build_all_cards
from original_meanings import MEANINGS

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "tarot_deck.db")
SCHEMA_PATH = os.path.join(HERE, "tarot_schema.sql")

SOURCE_NOTE = (
    "Card structure/correspondences cross-checked against Liz Dean, 'The Ultimate Guide "
    "to Tarot' (Fair Winds Press, 2015). Upright/reversed interpretive text is original, "
    "written for Astrowatch -- not reproduced from that or any other book."
)


def build(db_path: str = DB_PATH) -> int:
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())

    cards = build_all_cards()
    missing = [c["name"] for c in cards if c["name"] not in MEANINGS]
    if missing:
        raise SystemExit(f"Missing original meanings for: {missing}")

    rows = []
    for c in cards:
        upright, reversed_ = MEANINGS[c["name"]]
        rows.append((
            c["name"], c["arcana"], c["suit"], c["number"], c["rank_name"],
            c["astrology"], c["element"], ", ".join(c["keywords"]),
            upright, reversed_, SOURCE_NOTE,
        ))

    conn.executemany(
        """INSERT INTO tarot_cards
           (name, arcana, suit, number, rank_name, astrology, element, keywords,
            upright_meaning, reversed_meaning, source_note)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM tarot_cards").fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    n = build()
    print(f"Built {DB_PATH}: {n} cards inserted")
    assert n == 78
