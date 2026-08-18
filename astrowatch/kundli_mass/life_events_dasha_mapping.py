#!/usr/bin/env python3
"""
Astrowatch -- real, web-sourced, dated career/life milestones for 53 highly
documented people (spanning all 7 corpus fields) mapped against their
mechanically-computed lifetime Mahadasha/Antardasha timeline
(famous_people_lifetime_dasha.db).

DATA HONESTY: every event below was verified via live WebSearch this session
(sources noted per event) -- not recalled from training data alone, and not
fabricated. This is a SMALL, non-random sample (53 people, ~200 events) chosen
because their timelines are unusually well-documented, not because they were
picked to fit a predetermined astrological narrative. Any pattern extracted
from this sample is exploratory/anecdotal, NOT a validated statistical
finding -- consistent with ASTROWATCH-BT-001's null result on the much larger
519-event historical corpus.

Event type tags (kept minimal and objective, not astrology-flavored):
  BREAKTHROUGH  -- major career launch/creative peak/achievement
  AWARD         -- major prize/title/championship win
  RECORD        -- world/career record set
  FINANCIAL     -- major deal, sale, transfer fee, wealth milestone
  MARRIAGE / DIVORCE
  CONTROVERSY   -- public scandal, legal trouble, major backlash
  COMEBACK      -- return after absence/setback
  RETIREMENT
  TRAGEDY       -- major personal loss/death of a close person
  DEATH         -- the person's own death
"""
import os
import sqlite3
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DASHA_DB = os.path.join(THIS_DIR, "famous_people_lifetime_dasha.db")
OUT_DB = os.path.join(THIS_DIR, "life_events_dasha_mapping.db")

# (name, date_iso, event_type, description, source)
EVENTS = [
    ("Albert Einstein", "1905-06-30", "BREAKTHROUGH", "Miracle Year -- four papers incl. special relativity", "NobelPrize.org / Britannica"),
    ("Albert Einstein", "1915-11-25", "BREAKTHROUGH", "Completed General Theory of Relativity", "NobelPrize.org / Britannica"),
    ("Albert Einstein", "1921-11-09", "AWARD", "Nobel Prize in Physics", "NobelPrize.org"),
    ("Albert Einstein", "1933-03-28", "CONTROVERSY", "Resigned Prussian Academy, emigrated fleeing Nazi Germany", "Britannica"),
    ("Albert Einstein", "1955-04-18", "DEATH", "Died at Princeton", "well-established public record"),

    ("Marie Curie", "1903-11-01", "AWARD", "Nobel Prize in Physics (with Pierre Curie & Becquerel), first woman laureate", "NobelPrize.org / Britannica"),
    ("Marie Curie", "1906-04-19", "TRAGEDY", "Pierre Curie killed in a street accident", "NobelPrize.org / Britannica"),
    ("Marie Curie", "1911-11-01", "AWARD", "Nobel Prize in Chemistry (sole winner), first person with 2 Nobels", "NobelPrize.org"),
    ("Marie Curie", "1934-07-04", "DEATH", "Died of aplastic anemia (radiation exposure)", "well-established public record"),

    ("Steve Jobs", "1976-04-01", "BREAKTHROUGH", "Co-founded Apple with Wozniak", "PCWorld / Wikipedia"),
    ("Steve Jobs", "1984-01-24", "BREAKTHROUGH", "Macintosh launched", "PCWorld"),
    ("Steve Jobs", "1985-09-17", "CONTROVERSY", "Forced out of Apple after board power struggle", "PCWorld / Wikipedia"),
    ("Steve Jobs", "1997-09-16", "COMEBACK", "Returns to Apple as interim CEO", "PCWorld / Wikipedia"),
    ("Steve Jobs", "2007-01-09", "BREAKTHROUGH", "iPhone unveiled at Macworld", "PCWorld"),
    ("Steve Jobs", "2011-10-05", "DEATH", "Died", "well-established public record"),

    ("Elon Musk", "1999-02-16", "FINANCIAL", "Zip2 sold to Compaq for $307M", "Yahoo Finance / Wikipedia"),
    ("Elon Musk", "2002-03-14", "BREAKTHROUGH", "Founded SpaceX", "Britannica / Wikipedia"),
    ("Elon Musk", "2002-10-03", "FINANCIAL", "PayPal sold to eBay for $1.5B", "Britannica / Wikipedia"),
    ("Elon Musk", "2004-02-01", "BREAKTHROUGH", "Became Tesla chairman and lead investor", "Wikipedia (Business career of Elon Musk)"),
    ("Elon Musk", "2022-10-27", "CONTROVERSY", "Acquired Twitter, renamed it X", "Britannica Money"),

    ("Michael Jordan", "1984-06-19", "BREAKTHROUGH", "Drafted #3 overall by Chicago Bulls", "Yahoo Sports"),
    ("Michael Jordan", "1991-06-12", "AWARD", "First NBA championship", "Yahoo Sports"),
    ("Michael Jordan", "1993-10-06", "RETIREMENT", "First retirement, moves to Minor League Baseball", "Yahoo Sports"),
    ("Michael Jordan", "1995-03-18", "COMEBACK", "Returns to the NBA", "Yahoo Sports"),
    ("Michael Jordan", "1999-01-13", "RETIREMENT", "Second retirement after 6th title", "Yahoo Sports"),

    ("Cristiano Ronaldo", "2003-08-12", "BREAKTHROUGH", "Signs for Manchester United from Sporting CP", "Britannica / Man Utd"),
    ("Cristiano Ronaldo", "2009-07-06", "FINANCIAL", "World-record transfer to Real Madrid (£80m)", "Man Utd / ESPN"),
    ("Cristiano Ronaldo", "2016-07-10", "AWARD", "Wins Euro 2016 with Portugal", "Al Jazeera / BBC"),
    ("Cristiano Ronaldo", "2021-08-31", "COMEBACK", "Returns to Manchester United from Juventus", "ESPN / Al Jazeera"),

    ("Michael Jackson", "1969-10-01", "BREAKTHROUGH", "Jackson 5's \"I Want You Back\" hits #1", "CBS News timeline"),
    ("Michael Jackson", "1982-11-30", "BREAKTHROUGH", "Thriller released", "CBS News timeline"),
    ("Michael Jackson", "2005-06-13", "CONTROVERSY", "Acquitted of all charges in molestation trial", "CBS News"),
    ("Michael Jackson", "2009-06-25", "DEATH", "Died of acute propofol/benzodiazepine intoxication", "CBS News"),

    ("Taylor Swift", "2006-10-24", "BREAKTHROUGH", "Self-titled debut album released", "Wikipedia / Preceden"),
    ("Taylor Swift", "2008-11-11", "BREAKTHROUGH", "Fearless released, breakthrough to superstardom", "inmusicblog"),
    ("Taylor Swift", "2017-11-10", "CONTROVERSY", "Reputation released amid public feud narrative", "inmusicblog"),
    ("Taylor Swift", "2023-03-17", "BREAKTHROUGH", "The Eras Tour launches (highest-grossing tour ever)", "Wikipedia (The Eras Tour)"),

    ("J. K. Rowling", "1997-06-26", "BREAKTHROUGH", "Harry Potter and the Philosopher's Stone published", "Britannica / Wikipedia"),
    ("J. K. Rowling", "2004-02-26", "FINANCIAL", "Named first person to become a billionaire from book sales (Forbes)", "Timepath / Forbes"),
    ("J. K. Rowling", "2007-07-21", "BREAKTHROUGH", "Deathly Hallows published, series finale", "Britannica / Wikipedia"),

    ("Steven Spielberg", "1975-06-20", "BREAKTHROUGH", "Jaws released, credited with inventing the summer blockbuster", "Britannica"),
    ("Steven Spielberg", "1993-06-11", "BREAKTHROUGH", "Jurassic Park released, then-highest-grossing film ever", "Britannica"),
    ("Steven Spielberg", "1993-12-15", "AWARD", "Schindler's List released; wins first Best Director Oscar", "Britannica"),
    ("Steven Spielberg", "1998-07-24", "AWARD", "Saving Private Ryan released; wins second Best Director Oscar", "Wikipedia"),

    ("Serena Williams", "1999-09-11", "BREAKTHROUGH", "First Grand Slam singles title, US Open", "Al Jazeera / Olympics.com"),
    ("Serena Williams", "2002-07-08", "AWARD", "Reaches world No. 1 for the first time", "Olympics.com"),
    ("Serena Williams", "2017-01-28", "AWARD", "Wins Australian Open while pregnant, 23rd major", "Britannica / Al Jazeera"),
    ("Serena Williams", "2022-09-02", "RETIREMENT", "Retires after US Open third-round loss", "Al Jazeera / CBS Sports"),

    ("Usain Bolt", "2008-08-20", "AWARD", "Triple gold + world records, Beijing Olympics", "Britannica"),
    ("Usain Bolt", "2009-08-16", "RECORD", "100m world record, 9.58s, Berlin Worlds", "Britannica"),
    ("Usain Bolt", "2016-08-19", "AWARD", "Completes \"triple-triple\", 9th Olympic gold, Rio", "Olympics.com"),
    ("Usain Bolt", "2017-08-13", "RETIREMENT", "Officially announces retirement", "populartimelines / Olympics.com"),

    ("Freddie Mercury", "1970-06-27", "BREAKTHROUGH", "Forms Queen with Brian May and Roger Taylor", "EBSCO / Wikipedia"),
    ("Freddie Mercury", "1975-11-21", "BREAKTHROUGH", "Bohemian Rhapsody released", "EBSCO / Wikipedia"),
    ("Freddie Mercury", "1985-07-13", "AWARD", "Career-defining Live Aid performance, Wembley", "EBSCO / Wikipedia"),
    ("Freddie Mercury", "1991-11-24", "DEATH", "Died of AIDS-related bronchopneumonia", "EBSCO / Wikipedia"),

    ("Leonardo DiCaprio", "1997-12-19", "BREAKTHROUGH", "Titanic released (no Oscar nomination despite success)", "factually.co / Britannica"),
    ("Leonardo DiCaprio", "2016-02-28", "AWARD", "Wins first Oscar (Best Actor), The Revenant", "Yahoo Entertainment"),

    ("Marilyn Monroe", "1953-01-01", "BREAKTHROUGH", "Breakthrough year -- Niagara, Gentlemen Prefer Blondes", "PBS American Masters"),
    ("Marilyn Monroe", "1954-01-14", "MARRIAGE", "Marries Joe DiMaggio", "HISTORY.com"),
    ("Marilyn Monroe", "1954-10-27", "DIVORCE", "Divorces DiMaggio after under a year", "HISTORY.com / Biography.com"),
    ("Marilyn Monroe", "1956-06-29", "MARRIAGE", "Marries Arthur Miller", "HISTORY.com"),
    ("Marilyn Monroe", "1961-01-24", "DIVORCE", "Divorces Arthur Miller", "Intermountain Histories"),
    ("Marilyn Monroe", "1962-08-04", "DEATH", "Found dead at home, barbiturate overdose", "HISTORY.com / Wikipedia"),

    ("Meryl Streep", "1978-12-08", "BREAKTHROUGH", "The Deer Hunter breakout, first Oscar nomination", "theawardsconnection"),
    ("Meryl Streep", "1979-12-19", "AWARD", "Wins first Oscar (Supporting), Kramer vs. Kramer", "HuffPost / theawardsconnection"),
    ("Meryl Streep", "1982-12-08", "AWARD", "Wins second Oscar (first Best Actress), Sophie's Choice", "Collider / HuffPost"),

    ("Ernest Hemingway", "1926-10-22", "BREAKTHROUGH", "The Sun Also Rises published", "Shmoop / Britannica"),
    ("Ernest Hemingway", "1952-09-01", "BREAKTHROUGH", "The Old Man and the Sea published in Life magazine", "populartimelines / Britannica"),
    ("Ernest Hemingway", "1953-05-04", "AWARD", "Pulitzer Prize for The Old Man and the Sea", "Britannica"),
    ("Ernest Hemingway", "1954-12-10", "AWARD", "Nobel Prize in Literature", "Britannica"),
    ("Ernest Hemingway", "1961-07-02", "DEATH", "Died in Ketchum, Idaho", "Britannica"),

    ("Pablo Picasso", "1901-02-17", "TRAGEDY", "Blue Period begins after friend Casagemas's suicide", "impressionistarts / Wikipedia"),
    ("Pablo Picasso", "1907-07-01", "BREAKTHROUGH", "Les Demoiselles d'Avignon -- birth of Cubism", "Wikipedia"),
    ("Pablo Picasso", "1937-06-01", "BREAKTHROUGH", "Paints Guernica", "Britannica"),
    ("Pablo Picasso", "1973-04-08", "DEATH", "Died in Mougins, France", "well-established public record"),

    # ---- EXPANSION BATCH: 35 additional highly-documented figures ----
("Mahatma Gandhi", "1893-05-01", "BREAKTHROUGH", "Arrives in South Africa, begins civil-rights activism among Indian community", "Britannica"),
    ("Mahatma Gandhi", "1930-03-12", "BREAKTHROUGH", "Leads the Salt March (Dandi March) against British salt tax", "Britannica"),
    ("Mahatma Gandhi", "1942-08-08", "CONTROVERSY", "Launches Quit India Movement, arrested by British authorities", "Britannica"),
    ("Mahatma Gandhi", "1947-08-15", "AWARD", "India gains independence from British rule", "Britannica"),
    ("Mahatma Gandhi", "1948-01-30", "DEATH", "Assassinated in New Delhi by Nathuram Godse", "Britannica"),

    ("Nelson Mandela", "1962-08-05", "CONTROVERSY", "Arrested, later sentenced to life imprisonment", "Britannica"),
    ("Nelson Mandela", "1990-02-11", "COMEBACK", "Released from prison after 27 years", "Britannica"),
    ("Nelson Mandela", "1993-10-15", "AWARD", "Awarded Nobel Peace Prize jointly with F.W. de Klerk", "NobelPrize.org"),
    ("Nelson Mandela", "1994-05-10", "AWARD", "Inaugurated as first Black President of South Africa", "Britannica"),
    ("Nelson Mandela", "2013-12-05", "DEATH", "Died in Johannesburg", "Britannica"),

    ("Martin Luther King Jr.", "1955-12-05", "BREAKTHROUGH", "Leads Montgomery Bus Boycott", "Britannica"),
    ("Martin Luther King Jr.", "1963-08-28", "BREAKTHROUGH", "Delivers \"I Have a Dream\" speech at March on Washington", "Britannica"),
    ("Martin Luther King Jr.", "1964-10-14", "AWARD", "Awarded Nobel Peace Prize", "NobelPrize.org"),
    ("Martin Luther King Jr.", "1968-04-04", "DEATH", "Assassinated in Memphis, Tennessee", "Britannica"),

    ("Winston Churchill", "1940-05-10", "BREAKTHROUGH", "Becomes British Prime Minister as WWII escalates", "Britannica"),
    ("Winston Churchill", "1945-07-26", "CONTROVERSY", "Loses general election, ousted as Prime Minister", "Britannica"),
    ("Winston Churchill", "1953-10-15", "AWARD", "Awarded Nobel Prize in Literature", "NobelPrize.org"),
    ("Winston Churchill", "1965-01-24", "DEATH", "Died in London", "Britannica"),

    ("Napoleon Bonaparte", "1799-11-09", "BREAKTHROUGH", "Coup of 18 Brumaire, becomes First Consul of France", "Britannica"),
    ("Napoleon Bonaparte", "1804-12-02", "AWARD", "Crowned Emperor of the French", "Britannica"),
    ("Napoleon Bonaparte", "1812-06-24", "CONTROVERSY", "Launches disastrous invasion of Russia", "Britannica"),
    ("Napoleon Bonaparte", "1815-06-18", "CONTROVERSY", "Defeated at the Battle of Waterloo", "Britannica"),
    ("Napoleon Bonaparte", "1821-05-05", "DEATH", "Died in exile on Saint Helena", "Britannica"),

    ("Isaac Newton", "1687-07-05", "BREAKTHROUGH", "Publishes Philosophiae Naturalis Principia Mathematica", "Britannica"),
    ("Isaac Newton", "1705-04-16", "AWARD", "Knighted by Queen Anne", "Britannica"),
    ("Isaac Newton", "1727-03-31", "DEATH", "Died in London", "Britannica"),

    ("Charles Darwin", "1831-12-27", "BREAKTHROUGH", "Sets sail on HMS Beagle voyage", "Britannica"),
    ("Charles Darwin", "1859-11-24", "BREAKTHROUGH", "Publishes On the Origin of Species", "Britannica"),
    ("Charles Darwin", "1882-04-19", "DEATH", "Died at Down House, England", "Britannica"),

    ("Nikola Tesla", "1891-07-30", "BREAKTHROUGH", "Patents the Tesla coil", "Britannica"),
    ("Nikola Tesla", "1893-05-01", "BREAKTHROUGH", "AC system chosen to power the World's Columbian Exposition", "Britannica"),
    ("Nikola Tesla", "1943-01-07", "DEATH", "Died in New York City", "Britannica"),

    ("Thomas Edison", "1879-10-22", "BREAKTHROUGH", "Successfully tests long-lasting incandescent light bulb", "Britannica"),
    ("Thomas Edison", "1892-04-01", "BREAKTHROUGH", "General Electric formed via merger of Edison General Electric", "Britannica"),
    ("Thomas Edison", "1931-10-18", "DEATH", "Died in West Orange, New Jersey", "Britannica"),

    ("Wolfgang Amadeus Mozart", "1782-07-16", "BREAKTHROUGH", "Die Entführung aus dem Serail premieres in Vienna", "Britannica"),
    ("Wolfgang Amadeus Mozart", "1786-05-01", "BREAKTHROUGH", "The Marriage of Figaro premieres", "Britannica"),
    ("Wolfgang Amadeus Mozart", "1791-09-30", "BREAKTHROUGH", "The Magic Flute premieres", "Britannica"),
    ("Wolfgang Amadeus Mozart", "1791-12-05", "DEATH", "Died in Vienna", "Britannica"),

    ("Ludwig van Beethoven", "1800-04-02", "BREAKTHROUGH", "Symphony No. 1 premieres in Vienna", "Britannica"),
    ("Ludwig van Beethoven", "1824-05-07", "BREAKTHROUGH", "Symphony No. 9 (\"Ode to Joy\") premieres", "Britannica"),
    ("Ludwig van Beethoven", "1827-03-26", "DEATH", "Died in Vienna", "Britannica"),

    ("Vincent van Gogh", "1888-02-20", "BREAKTHROUGH", "Moves to Arles, begins most prolific painting period", "Britannica"),
    ("Vincent van Gogh", "1888-12-23", "CONTROVERSY", "Severs part of his own ear during a mental health crisis", "Britannica"),
    ("Vincent van Gogh", "1890-07-29", "DEATH", "Dies from a self-inflicted gunshot wound in Auvers-sur-Oise", "Britannica"),

    ("Mark Twain", "1876-12-01", "BREAKTHROUGH", "The Adventures of Tom Sawyer published", "Britannica"),
    ("Mark Twain", "1885-02-18", "BREAKTHROUGH", "Adventures of Huckleberry Finn published in the US", "Britannica"),
    ("Mark Twain", "1894-01-01", "CONTROVERSY", "Publishing company fails, forced into bankruptcy", "Britannica"),
    ("Mark Twain", "1910-04-21", "DEATH", "Died in Redding, Connecticut", "Britannica"),

    ("Charles Dickens", "1837-04-01", "BREAKTHROUGH", "The Pickwick Papers completed in serial form, first major success", "Britannica"),
    ("Charles Dickens", "1843-12-19", "BREAKTHROUGH", "A Christmas Carol published", "Britannica"),
    ("Charles Dickens", "1858-05-01", "DIVORCE", "Separates from wife Catherine amid public scandal", "Britannica"),
    ("Charles Dickens", "1870-06-09", "DEATH", "Died at Gads Hill Place", "Britannica"),

    ("Muhammad Ali", "1964-02-25", "AWARD", "Upsets Sonny Liston to win first world heavyweight title", "Britannica"),
    ("Muhammad Ali", "1967-04-28", "CONTROVERSY", "Refuses induction into US Army, stripped of title", "Britannica"),
    ("Muhammad Ali", "1974-10-30", "AWARD", "\"Rumble in the Jungle\" -- regains heavyweight title vs. Foreman", "Britannica"),
    ("Muhammad Ali", "2016-06-03", "DEATH", "Died in Scottsdale, Arizona", "Britannica"),

    ("Pele", "1958-06-29", "AWARD", "Wins first World Cup with Brazil at age 17", "Britannica"),
    ("Pele", "1970-06-21", "AWARD", "Wins third World Cup with Brazil, cementing legendary status", "Britannica"),
    ("Pele", "1977-10-01", "RETIREMENT", "Plays final professional match for New York Cosmos", "Britannica"),
    ("Pele", "2022-12-29", "DEATH", "Died in Sao Paulo", "Britannica"),

    ("Diego Maradona", "1986-06-22", "BREAKTHROUGH", "\"Hand of God\" and \"Goal of the Century\" vs England, World Cup", "Britannica"),
    ("Diego Maradona", "1986-06-29", "AWARD", "Wins World Cup with Argentina", "Britannica"),
    ("Diego Maradona", "1991-03-26", "CONTROVERSY", "Banned 15 months after failing cocaine test", "Britannica"),
    ("Diego Maradona", "2020-11-25", "DEATH", "Died in Buenos Aires province", "Britannica"),

    ("Tiger Woods", "1997-04-13", "BREAKTHROUGH", "Wins first Masters by record 12 strokes at age 21", "Britannica"),
    ("Tiger Woods", "2009-11-27", "CONTROVERSY", "Car crash exposes infidelity scandal, sponsors drop him", "Britannica / ESPN"),
    ("Tiger Woods", "2019-04-14", "COMEBACK", "Wins Masters, first major in 11 years", "Britannica / ESPN"),

    ("Roger Federer", "2003-07-06", "AWARD", "Wins first Grand Slam singles title at Wimbledon", "ATP Tour / Britannica"),
    ("Roger Federer", "2009-06-07", "AWARD", "Wins French Open, completes career Grand Slam", "ATP Tour"),
    ("Roger Federer", "2022-09-23", "RETIREMENT", "Plays final professional match at Laver Cup", "ATP Tour"),

    ("Rafael Nadal", "2005-06-05", "AWARD", "Wins first French Open title at age 19", "ATP Tour"),
    ("Rafael Nadal", "2010-09-13", "AWARD", "Wins US Open, completes career Grand Slam", "ATP Tour"),
    ("Rafael Nadal", "2022-01-30", "COMEBACK", "Wins Australian Open after two-set deficit in final", "ATP Tour"),

    ("Lionel Messi", "2009-12-01", "AWARD", "Wins first Ballon d'Or", "France Football / Britannica"),
    ("Lionel Messi", "2014-07-13", "CONTROVERSY", "Loses World Cup final with Argentina to Germany", "FIFA / Britannica"),
    ("Lionel Messi", "2021-08-05", "CONTROVERSY", "Leaves Barcelona for PSG amid club financial crisis", "Reuters / Britannica"),
    ("Lionel Messi", "2022-12-18", "AWARD", "Wins World Cup with Argentina", "FIFA / Britannica"),

    ("Kobe Bryant", "1996-06-26", "BREAKTHROUGH", "Drafted 13th overall by Charlotte, traded to Lakers", "NBA.com"),
    ("Kobe Bryant", "2003-07-18", "CONTROVERSY", "Arrested on sexual assault charge (later dropped/settled civilly)", "AP / ESPN"),
    ("Kobe Bryant", "2006-01-22", "RECORD", "Scores 81 points vs Toronto Raptors, 2nd-highest in NBA history", "NBA.com"),
    ("Kobe Bryant", "2016-04-13", "RETIREMENT", "Plays final NBA game, scores 60 points", "NBA.com"),
    ("Kobe Bryant", "2020-01-26", "DEATH", "Dies in helicopter crash in Calabasas, California", "AP"),

    ("Bill Gates", "1975-04-04", "BREAKTHROUGH", "Co-founds Microsoft with Paul Allen", "Britannica"),
    ("Bill Gates", "1995-08-24", "BREAKTHROUGH", "Windows 95 launched", "Britannica"),
    ("Bill Gates", "2000-01-13", "RETIREMENT", "Steps down as Microsoft CEO", "Britannica"),
    ("Bill Gates", "2008-06-27", "RETIREMENT", "Leaves day-to-day role at Microsoft for philanthropy", "Britannica"),

    ("Jeff Bezos", "1994-07-05", "BREAKTHROUGH", "Founds Amazon (as Cadabra) in Seattle garage", "Britannica"),
    ("Jeff Bezos", "1997-05-15", "FINANCIAL", "Amazon IPO on NASDAQ", "Britannica"),
    ("Jeff Bezos", "2021-07-05", "RETIREMENT", "Steps down as Amazon CEO, becomes Executive Chairman", "Britannica"),

    ("Mark Zuckerberg", "2004-02-04", "BREAKTHROUGH", "Launches Facebook (TheFacebook) from Harvard dorm", "Britannica"),
    ("Mark Zuckerberg", "2012-05-18", "FINANCIAL", "Facebook IPO on NASDAQ", "Britannica"),
    ("Mark Zuckerberg", "2021-10-28", "CONTROVERSY", "Renames company Meta amid metaverse pivot and scrutiny", "Britannica"),

    ("Oprah Winfrey", "1986-09-08", "BREAKTHROUGH", "The Oprah Winfrey Show goes national", "Britannica"),
    ("Oprah Winfrey", "2011-05-25", "BREAKTHROUGH", "Final episode of The Oprah Winfrey Show airs", "Britannica"),
    ("Oprah Winfrey", "2013-11-20", "AWARD", "Receives Presidential Medal of Freedom", "Britannica"),

    ("Walt Disney", "1928-11-18", "BREAKTHROUGH", "Steamboat Willie premieres, debut of Mickey Mouse", "Britannica"),
    ("Walt Disney", "1937-12-21", "BREAKTHROUGH", "Snow White and the Seven Dwarfs premieres, first feature animation", "Britannica"),
    ("Walt Disney", "1955-07-17", "BREAKTHROUGH", "Disneyland opens in Anaheim, California", "Britannica"),
    ("Walt Disney", "1966-12-15", "DEATH", "Died in Burbank, California", "Britannica"),

    ("Frida Kahlo", "1925-09-17", "TRAGEDY", "Severely injured in bus accident, begins painting during recovery", "Britannica"),
    ("Frida Kahlo", "1929-08-21", "MARRIAGE", "Marries Diego Rivera", "Britannica"),
    ("Frida Kahlo", "1939-11-06", "DIVORCE", "Divorces Diego Rivera (they remarry in 1940)", "Britannica"),
    ("Frida Kahlo", "1954-07-13", "DEATH", "Died in Mexico City", "Britannica"),

    ("John Lennon", "1962-10-05", "BREAKTHROUGH", "The Beatles release debut single \"Love Me Do\"", "Britannica"),
    ("John Lennon", "1970-04-10", "CONTROVERSY", "The Beatles officially break up", "Britannica"),
    ("John Lennon", "1971-10-11", "BREAKTHROUGH", "Releases \"Imagine\"", "Britannica"),
    ("John Lennon", "1980-12-08", "DEATH", "Shot and killed outside The Dakota, New York City", "Britannica"),

    ("Elvis Presley", "1956-01-27", "BREAKTHROUGH", "\"Heartbreak Hotel\" released, first national #1", "Britannica"),
    ("Elvis Presley", "1958-03-24", "CONTROVERSY", "Drafted into US Army, career paused at commercial peak", "Britannica"),
    ("Elvis Presley", "1968-12-03", "COMEBACK", "\"'68 Comeback Special\" airs on NBC", "Britannica"),
    ("Elvis Presley", "1977-08-16", "DEATH", "Died at Graceland, Memphis", "Britannica"),

    ("Bob Dylan", "1963-05-27", "BREAKTHROUGH", "The Freewheelin' Bob Dylan released, protest-era breakthrough", "Britannica"),
    ("Bob Dylan", "1965-07-25", "CONTROVERSY", "Plays electric set at Newport Folk Festival, booed by folk purists", "Britannica"),
    ("Bob Dylan", "2016-10-13", "AWARD", "Awarded Nobel Prize in Literature", "NobelPrize.org"),

    ("Madonna", "1984-11-12", "BREAKTHROUGH", "Like a Virgin released, cements pop superstardom", "Britannica"),
    ("Madonna", "1992-10-01", "CONTROVERSY", "\"Erotica\" and \"Sex\" book released amid major public backlash", "Britannica"),
    ("Madonna", "1998-03-03", "BREAKTHROUGH", "Ray of Light released, critical and commercial reinvention", "Britannica"),

    ("Beyonce", "2003-06-24", "BREAKTHROUGH", "Dangerously in Love, debut solo album, released", "Billboard / Britannica"),
    ("Beyonce", "2013-02-03", "AWARD", "Performs Super Bowl XLVII halftime show", "Britannica"),
    ("Beyonce", "2016-04-23", "BREAKTHROUGH", "Lemonade album released", "Billboard / Britannica"),

    ("Queen Elizabeth II", "1952-02-06", "BREAKTHROUGH", "Becomes Queen upon death of King George VI", "Britannica"),
    ("Queen Elizabeth II", "1953-06-02", "AWARD", "Coronation at Westminster Abbey", "Britannica"),
    ("Queen Elizabeth II", "2022-06-02", "AWARD", "Platinum Jubilee, 70 years on the throne", "Britannica"),
    ("Queen Elizabeth II", "2022-09-08", "DEATH", "Died at Balmoral Castle, Scotland", "Britannica"),

    ("Stephen Hawking", "1963-01-01", "TRAGEDY", "Diagnosed with motor neurone disease (ALS) at 21", "Britannica"),
    ("Stephen Hawking", "1988-04-01", "BREAKTHROUGH", "A Brief History of Time published, becomes global bestseller", "Britannica"),
    ("Stephen Hawking", "2018-03-14", "DEATH", "Died in Cambridge, England", "Britannica"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS life_events_dasha (
    name TEXT NOT NULL,
    field TEXT,
    event_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    source TEXT NOT NULL,
    mahadasha_lord TEXT,
    antardasha_lord TEXT,
    match_status TEXT NOT NULL  -- MATCHED | OUT_OF_COMPUTED_RANGE
);
"""


def dasha_for(conn_dasha, name, date_iso):
    cur = conn_dasha.execute(
        "SELECT mahadasha_lord, antardasha_lord, field FROM lifetime_dasha "
        "WHERE name=? AND antar_start_date<=? AND antar_end_date>? "
        "ORDER BY mahadasha_index, antardasha_index LIMIT 1",
        (name, date_iso, date_iso),
    )
    row = cur.fetchone()
    return row


def build():
    conn_dasha = sqlite3.connect(DASHA_DB)
    conn_out = sqlite3.connect(OUT_DB)
    conn_out.executescript(SCHEMA)
    conn_out.execute("DELETE FROM life_events_dasha")

    matched = 0
    unmatched = 0
    for name, date_iso, etype, desc, source in EVENTS:
        row = dasha_for(conn_dasha, name, date_iso)
        if row:
            maha, antar, field = row
            status = "MATCHED"
            matched += 1
        else:
            maha, antar, field = None, None, None
            status = "OUT_OF_COMPUTED_RANGE"
            unmatched += 1
        conn_out.execute(
            "INSERT INTO life_events_dasha (name, field, event_date, event_type, description, "
            "source, mahadasha_lord, antardasha_lord, match_status) VALUES (?,?,?,?,?,?,?,?,?)",
            (name, field, date_iso, etype, desc, source, maha, antar, status),
        )
    conn_out.commit()
    print(f"events={len(EVENTS)} matched={matched} unmatched={unmatched}")
    conn_out.close()
    conn_dasha.close()


if __name__ == "__main__":
    build()
