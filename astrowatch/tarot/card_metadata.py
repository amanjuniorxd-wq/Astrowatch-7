"""
Astrowatch -- Tarot card metadata (structure, not interpretive prose)
=====================================================================
Defines the 78-card structure of a standard Rider-Waite-Smith-pattern tarot deck: names,
arcana, suit, rank, and the traditional Golden Dawn astrological/elemental correspondences
used across virtually all modern tarot literature (these are standard classification
attributions -- e.g. "The Emperor = Aries, Fire" -- not any single author's protected
creative expression, and appear consistently across dozens of independent tarot sources).

Interpretive upright/reversed meanings live separately in original_meanings.py, written
in Astrowatch's own words (see that module's docstring for why).

SOURCING NOTE: this module's card structure and correspondences were cross-checked this
session against a real reference book the user uploaded -- Liz Dean, "The Ultimate Guide
to Tarot" (Fair Winds Press, 2015) -- to confirm accuracy and completeness (all 78 cards
present, correct suit/rank/arcana structure, correspondences consistent with that source).
No prose text from that book is reproduced in this repository.
"""

MAJOR_ARCANA = [
    ("The Fool", 0, "Uranus", "Air", ["innocence", "risk", "new beginnings"]),
    ("The Magician", 1, "Mercury", "Air", ["willpower", "manifestation", "resourcefulness"]),
    ("The High Priestess", 2, "The Moon", "Water", ["intuition", "secrets", "the unconscious"]),
    ("The Empress", 3, "Venus", "Earth", ["abundance", "nurturing", "creativity"]),
    ("The Emperor", 4, "Aries", "Fire", ["authority", "structure", "control"]),
    ("The Hierophant", 5, "Taurus", "Earth", ["tradition", "belief", "conformity"]),
    ("The Lovers", 6, "Gemini", "Air", ["love", "choice", "alignment of values"]),
    ("The Chariot", 7, "Cancer", "Water", ["willpower", "victory", "determination"]),
    ("Strength", 8, "Leo", "Fire", ["courage", "patience", "inner strength"]),
    ("The Hermit", 9, "Virgo", "Earth", ["introspection", "solitude", "guidance"]),
    ("The Wheel of Fortune", 10, "Jupiter", "Fire", ["fate", "cycles", "turning points"]),
    ("Justice", 11, "Libra", "Air", ["fairness", "truth", "accountability"]),
    ("The Hanged Man", 12, "Neptune", "Water", ["surrender", "new perspective", "pause"]),
    ("Death", 13, "Scorpio", "Water", ["transformation", "endings", "release"]),
    ("Temperance", 14, "Sagittarius", "Fire", ["balance", "moderation", "synthesis"]),
    ("The Devil", 15, "Capricorn", "Earth", ["bondage", "temptation", "attachment"]),
    ("The Tower", 16, "Mars", "Fire", ["upheaval", "revelation", "collapse"]),
    ("The Star", 17, "Aquarius", "Air", ["hope", "healing", "inspiration"]),
    ("The Moon", 18, "Pisces", "Water", ["illusion", "intuition", "uncertainty"]),
    ("The Sun", 19, "The Sun", "Fire", ["joy", "vitality", "success"]),
    ("Judgment", 20, "Pluto", "Fire", ["reckoning", "renewal", "self-assessment"]),
    ("The World", 21, "Saturn", "Earth", ["completion", "fulfillment", "wholeness"]),
]

SUITS = ["Cups", "Pentacles", "Swords", "Wands"]
SUIT_ELEMENT = {"Cups": "Water", "Pentacles": "Earth", "Swords": "Air", "Wands": "Fire"}
SUIT_DOMAIN = {
    "Cups": "emotion, relationships, and intuition",
    "Pentacles": "material life, work, money, and the body",
    "Swords": "the mind, communication, and conflict",
    "Wands": "energy, ambition, and creativity",
}

RANKS = [
    ("Ace", 1), ("Two", 2), ("Three", 3), ("Four", 4), ("Five", 5),
    ("Six", 6), ("Seven", 7), ("Eight", 8), ("Nine", 9), ("Ten", 10),
    ("Page", None), ("Knight", None), ("Queen", None), ("King", None),
]

COURT_ASTROLOGY = {
    # Traditional court-card zodiac triplicate assignments (element-of-suit convention),
    # kept simple/consistent rather than asserting a single disputed sign per card --
    # court cards are more commonly read as *people/energies* than as a fixed zodiac sign
    # in most modern practice, so no single sign is forced here.
}


def build_all_cards():
    """Returns a list of card dicts for all 78 cards, structure + correspondences only
    (no interpretive text -- that's merged in from original_meanings.MEANINGS by the
    database builder)."""
    cards = []
    for name, number, astrology, element, keywords in MAJOR_ARCANA:
        cards.append({
            "name": name,
            "arcana": "major",
            "suit": None,
            "number": number,
            "rank_name": None,
            "astrology": astrology,
            "element": element,
            "keywords": keywords,
        })
    for suit in SUITS:
        for rank_name, number in RANKS:
            cards.append({
                "name": f"{rank_name} of {suit}",
                "arcana": "minor",
                "suit": suit,
                "number": number,
                "rank_name": rank_name,
                "astrology": None,
                "element": SUIT_ELEMENT[suit],
                "keywords": [SUIT_DOMAIN[suit]],
            })
    return cards


if __name__ == "__main__":
    all_cards = build_all_cards()
    print(f"{len(all_cards)} cards defined (expect 78)")
    assert len(all_cards) == 78
    assert len({c["name"] for c in all_cards}) == 78
