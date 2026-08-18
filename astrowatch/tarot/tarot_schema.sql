-- Astrowatch -- Tarot deck schema
-- One row per card in a standard 78-card Rider-Waite-Smith-pattern deck.
CREATE TABLE IF NOT EXISTS tarot_cards (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    arcana          TEXT NOT NULL CHECK (arcana IN ('major', 'minor')),
    suit            TEXT,                 -- NULL for major arcana; Cups/Pentacles/Swords/Wands for minor
    number          INTEGER,              -- 0-21 for major; 1-10 for minor pip cards; NULL for court cards
    rank_name       TEXT,                 -- NULL for major; Ace/Two/.../King for minor
    astrology       TEXT,                 -- traditional zodiac sign or planet correspondence
    element         TEXT NOT NULL,        -- Fire / Water / Air / Earth
    keywords        TEXT NOT NULL,        -- comma-separated short keyword list
    upright_meaning TEXT NOT NULL,
    reversed_meaning TEXT NOT NULL,
    source_note     TEXT NOT NULL         -- provenance/authorship disclosure
);

CREATE INDEX IF NOT EXISTS idx_tarot_arcana ON tarot_cards(arcana);
CREATE INDEX IF NOT EXISTS idx_tarot_suit ON tarot_cards(suit);
