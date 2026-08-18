import os
import random
import sqlite3
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TAROT_DIR = os.path.dirname(HERE)
sys.path.insert(0, TAROT_DIR)

from card_metadata import build_all_cards, MAJOR_ARCANA, SUITS, RANKS  # noqa: E402
from original_meanings import MEANINGS  # noqa: E402
import tarot_engine as engine  # noqa: E402

DB_PATH = os.path.join(TAROT_DIR, "tarot_deck.db")


class TestCardMetadata(unittest.TestCase):
    def test_78_cards_total(self):
        cards = build_all_cards()
        self.assertEqual(len(cards), 78)

    def test_22_major_56_minor(self):
        cards = build_all_cards()
        majors = [c for c in cards if c["arcana"] == "major"]
        minors = [c for c in cards if c["arcana"] == "minor"]
        self.assertEqual(len(majors), 22)
        self.assertEqual(len(minors), 56)

    def test_all_names_unique(self):
        cards = build_all_cards()
        names = [c["name"] for c in cards]
        self.assertEqual(len(names), len(set(names)))

    def test_four_suits_14_cards_each(self):
        cards = build_all_cards()
        for suit in SUITS:
            in_suit = [c for c in cards if c["suit"] == suit]
            self.assertEqual(len(in_suit), 14, f"{suit} should have 14 cards")

    def test_major_numbers_0_to_21(self):
        numbers = sorted(c[1] for c in MAJOR_ARCANA)
        self.assertEqual(numbers, list(range(22)))

    def test_every_card_has_element(self):
        for c in build_all_cards():
            self.assertIn(c["element"], {"Fire", "Water", "Air", "Earth"})


class TestOriginalMeanings(unittest.TestCase):
    def test_meanings_cover_all_78_card_names(self):
        card_names = {c["name"] for c in build_all_cards()}
        self.assertEqual(card_names, set(MEANINGS.keys()))

    def test_every_meaning_has_upright_and_reversed_text(self):
        for name, (upright, reversed_) in MEANINGS.items():
            self.assertTrue(upright and len(upright) > 20, f"{name} upright too short/empty")
            self.assertTrue(reversed_ and len(reversed_) > 20, f"{name} reversed too short/empty")

    def test_upright_and_reversed_are_distinct_text(self):
        for name, (upright, reversed_) in MEANINGS.items():
            self.assertNotEqual(upright, reversed_, f"{name} upright/reversed text identical")


class TestDeckDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(DB_PATH):
            raise unittest.SkipTest("tarot_deck.db not built -- run build_tarot_deck.py first")

    def test_78_rows(self):
        conn = sqlite3.connect(DB_PATH)
        n = conn.execute("SELECT COUNT(*) FROM tarot_cards").fetchone()[0]
        conn.close()
        self.assertEqual(n, 78)

    def test_no_null_required_fields(self):
        conn = sqlite3.connect(DB_PATH)
        for col in ("name", "arcana", "element", "keywords", "upright_meaning",
                    "reversed_meaning", "source_note"):
            n = conn.execute(f"SELECT COUNT(*) FROM tarot_cards WHERE {col} IS NULL OR {col} = ''").fetchone()[0]
            self.assertEqual(n, 0, f"{n} rows have empty {col}")
        conn.close()

    def test_arcana_split_matches(self):
        conn = sqlite3.connect(DB_PATH)
        majors = conn.execute("SELECT COUNT(*) FROM tarot_cards WHERE arcana='major'").fetchone()[0]
        minors = conn.execute("SELECT COUNT(*) FROM tarot_cards WHERE arcana='minor'").fetchone()[0]
        conn.close()
        self.assertEqual(majors, 22)
        self.assertEqual(minors, 56)

    def test_name_uniqueness_enforced_by_schema(self):
        conn = sqlite3.connect(DB_PATH)
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tarot_cards (name, arcana, element, keywords, upright_meaning, "
                "reversed_meaning, source_note) VALUES ('The Fool', 'major', 'Air', 'x', 'x', 'x', 'x')"
            )
        conn.close()


class TestReadingEngine(unittest.TestCase):
    def setUp(self):
        if not os.path.exists(DB_PATH):
            self.skipTest("tarot_deck.db not built -- run build_tarot_deck.py first")

    def test_single_card_spread_returns_one_card(self):
        drawn = engine.draw_spread("single_card", rng=random.Random(1))
        self.assertEqual(len(drawn), 1)

    def test_three_card_spread_returns_three_unique_cards(self):
        drawn = engine.draw_spread("three_card", rng=random.Random(2))
        self.assertEqual(len(drawn), 3)
        names = [c.name for c in drawn]
        self.assertEqual(len(names), len(set(names)), "three-card spread drew a duplicate card")
        self.assertEqual([c.position_label for c in drawn], ["Past", "Present", "Future"])

    def test_celtic_cross_returns_ten_unique_cards(self):
        drawn = engine.draw_spread("celtic_cross", rng=random.Random(3))
        self.assertEqual(len(drawn), 10)
        names = [c.name for c in drawn]
        self.assertEqual(len(names), len(set(names)), "celtic cross drew a duplicate card")

    def test_unknown_spread_raises(self):
        with self.assertRaises(ValueError):
            engine.draw_spread("not_a_real_spread")

    def test_meaning_matches_orientation(self):
        drawn = engine.draw_spread("celtic_cross", rng=random.Random(4))
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        for card in drawn:
            row = conn.execute("SELECT * FROM tarot_cards WHERE name=?", (card.name,)).fetchone()
            expected = row["reversed_meaning"] if card.reversed else row["upright_meaning"]
            self.assertEqual(card.meaning, expected)
        conn.close()

    def test_reversal_rate_roughly_half_over_many_draws(self):
        rng = random.Random(123)
        reversed_count = 0
        total = 0
        for _ in range(200):
            drawn = engine.draw_spread("single_card", rng=rng)
            total += 1
            if drawn[0].reversed:
                reversed_count += 1
        rate = reversed_count / total
        self.assertTrue(0.35 < rate < 0.65, f"reversal rate {rate} far from expected ~0.5")

    def test_same_seed_is_deterministic(self):
        drawn_a = engine.draw_spread("three_card", rng=random.Random(999))
        drawn_b = engine.draw_spread("three_card", rng=random.Random(999))
        self.assertEqual([c.name for c in drawn_a], [c.name for c in drawn_b])
        self.assertEqual([c.reversed for c in drawn_a], [c.reversed for c in drawn_b])


if __name__ == "__main__":
    unittest.main()
