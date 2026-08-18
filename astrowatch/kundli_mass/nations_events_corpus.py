"""
Astrowatch -- real, dated major national events for a substantial, diverse subset
of nations_corpus.py, mapped against each nation's mechanically-computed lifetime
Mahadasha/Antardasha timeline (nations_lifetime_dasha.db).

DATA HONESTY (same convention as life_events_dasha_mapping.py / events_corpus.py):
these are widely-documented, major national/world-historical events (wars,
revolutions, coups, partitions, major economic crises/booms, reunifications) --
the kind covered in any standard modern-history reference, not individually
re-verified live for every entry. This is a SMALL, non-random sample (25 nations,
~140 events) chosen for how well-documented their modern history is, not to fit a
predetermined astrological narrative. Any pattern drawn from this is exploratory,
not a validated statistical finding (same caveat this project has applied to
every other small-sample dasha-correlation pass, e.g. GRAHA_MAHADASHA_LIFE_EVENT_
SYNTHESIS.md, and consistent with ASTROWATCH-BT-001's null result on 519 events).

Event type tags:
  WAR             -- entered/fought a major war or armed conflict
  REVOLUTION      -- revolution, coup, or violent regime change
  ECON_CRISIS     -- major economic crisis/crash/hyperinflation/famine
  ECON_BOOM       -- major sustained economic growth phase (named era)
  PARTITION       -- territorial partition/split/loss of major territory
  REUNIFICATION   -- territorial reunification/major annexation
  REGIME_CHANGE   -- major peaceful/negotiated change of government system
  DISASTER        -- major natural disaster with large national impact
  DIPLOMATIC      -- major treaty/alliance/international-standing shift
"""
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DASHA_DB = os.path.join(THIS_DIR, "nations_lifetime_dasha.db")
OUT_DB = os.path.join(THIS_DIR, "nations_events_dasha_mapping.db")

# (nation_name, date_iso, event_type, description)
EVENTS = [
    ("India", "1962-10-20", "WAR", "Sino-Indian War begins"),
    ("India", "1971-12-03", "WAR", "Indo-Pakistani War / Bangladesh Liberation War"),
    ("India", "1974-05-18", "DIPLOMATIC", "First nuclear test (Smiling Buddha)"),
    ("India", "1991-07-24", "ECON_BOOM", "Economic liberalization reforms launched"),
    ("India", "1998-05-11", "DIPLOMATIC", "Pokhran-II nuclear tests"),
    ("India", "2019-08-05", "REGIME_CHANGE", "Article 370 revoked, Jammu & Kashmir reorganized"),

    ("United States", "1861-04-12", "WAR", "American Civil War begins (Fort Sumter)"),
    ("United States", "1929-10-29", "ECON_CRISIS", "Wall Street Crash / start of Great Depression"),
    ("United States", "1941-12-07", "WAR", "Pearl Harbor attack, US enters WWII"),
    ("United States", "1963-11-22", "REGIME_CHANGE", "Assassination of President Kennedy"),
    ("United States", "1974-08-09", "REGIME_CHANGE", "Nixon resigns over Watergate"),
    ("United States", "2001-09-11", "WAR", "9/11 attacks"),
    ("United States", "2008-09-15", "ECON_CRISIS", "Lehman Brothers collapse / global financial crisis"),

    ("China", "1966-05-16", "REVOLUTION", "Cultural Revolution begins"),
    ("China", "1976-09-09", "REGIME_CHANGE", "Death of Mao Zedong"),
    ("China", "1978-12-18", "ECON_BOOM", "Deng Xiaoping's 'Reform and Opening-up' launched"),
    ("China", "1989-06-04", "REVOLUTION", "Tiananmen Square crackdown"),
    ("China", "2001-12-11", "ECON_BOOM", "Accession to the World Trade Organization"),

    ("Russia", "1998-08-17", "ECON_CRISIS", "Russian financial crisis / ruble default"),
    ("Russia", "1999-12-31", "REGIME_CHANGE", "Yeltsin resigns, Putin becomes acting president"),
    ("Russia", "2014-03-18", "REUNIFICATION", "Annexation of Crimea"),
    ("Russia", "2022-02-24", "WAR", "Full-scale invasion of Ukraine begins"),

    ("Germany", "1990-10-03", "REUNIFICATION", "German reunification"),
    ("Germany", "2015-08-25", "REGIME_CHANGE", "Merkel suspends Dublin Regulation, major refugee-policy shift"),

    ("United Kingdom", "1973-01-01", "DIPLOMATIC", "Joins the European Economic Community"),
    ("United Kingdom", "1982-04-02", "WAR", "Falklands War begins"),
    ("United Kingdom", "2016-06-23", "DIPLOMATIC", "Brexit referendum"),
    ("United Kingdom", "2020-01-31", "DIPLOMATIC", "Formally leaves the European Union"),

    ("France", "1968-05-03", "REVOLUTION", "May 1968 civil unrest"),

    ("Japan", "1991-03-01", "ECON_CRISIS", "Asset price bubble collapse, start of 'Lost Decade'"),
    ("Japan", "2011-03-11", "DISASTER", "Tohoku earthquake/tsunami and Fukushima disaster"),

    ("Israel", "1967-06-05", "WAR", "Six-Day War"),
    ("Israel", "1973-10-06", "WAR", "Yom Kippur War"),
    ("Israel", "1979-03-26", "DIPLOMATIC", "Peace treaty with Egypt signed"),
    ("Israel", "1993-09-13", "DIPLOMATIC", "Oslo Accords signed"),
    ("Israel", "2023-10-07", "WAR", "Hamas-led attack, Israel-Hamas war begins"),

    ("South Africa", "1976-06-16", "REVOLUTION", "Soweto uprising"),
    ("South Africa", "1990-02-11", "REGIME_CHANGE", "Nelson Mandela released from prison"),
    ("South Africa", "1994-04-27", "REGIME_CHANGE", "First fully democratic, multiracial elections"),

    ("Brazil", "1964-04-01", "REVOLUTION", "Military coup, start of military dictatorship"),
    ("Brazil", "1985-03-15", "REGIME_CHANGE", "Return to civilian rule"),
    ("Brazil", "1994-07-01", "ECON_BOOM", "Plano Real launched, hyperinflation ended"),

    ("Pakistan", "1971-12-16", "PARTITION", "Surrender in Dhaka, loss of East Pakistan (Bangladesh independence)"),
    ("Pakistan", "1998-05-28", "DIPLOMATIC", "Chagai-I nuclear tests"),
    ("Pakistan", "1999-10-12", "REVOLUTION", "Musharraf military coup"),

    ("Ukraine", "2014-02-22", "REVOLUTION", "Euromaidan revolution, Yanukovych ousted"),
    ("Ukraine", "2022-02-24", "WAR", "Russian full-scale invasion begins"),

    ("Iran", "1979-02-11", "REVOLUTION", "Islamic Revolution, Shah overthrown"),
    ("Iran", "1980-09-22", "WAR", "Iran-Iraq War begins"),

    ("Vietnam", "1975-04-30", "REUNIFICATION", "Fall of Saigon, end of Vietnam War"),
    ("Vietnam", "1986-12-18", "ECON_BOOM", "Doi Moi economic reforms launched"),

    ("South Korea", "1950-06-25", "WAR", "Korean War begins"),
    ("South Korea", "1997-11-21", "ECON_CRISIS", "Asian financial crisis, IMF bailout"),
    ("South Korea", "1987-06-29", "REGIME_CHANGE", "Democratization declaration ends military rule"),

    ("Egypt", "1952-07-23", "REVOLUTION", "Free Officers coup, monarchy overthrown"),
    ("Egypt", "1956-07-26", "DIPLOMATIC", "Suez Canal nationalized"),
    ("Egypt", "2011-01-25", "REVOLUTION", "Arab Spring uprising, Mubarak overthrown"),

    ("Nigeria", "1967-07-06", "WAR", "Nigerian Civil War (Biafra) begins"),
    ("Nigeria", "1999-05-29", "REGIME_CHANGE", "Return to civilian democratic rule"),

    ("Rwanda", "1994-04-07", "WAR", "Genocide against the Tutsi begins"),

    ("Afghanistan", "1979-12-24", "WAR", "Soviet invasion begins"),
    ("Afghanistan", "1996-09-27", "REGIME_CHANGE", "Taliban capture Kabul (first rule)"),
    ("Afghanistan", "2001-10-07", "WAR", "US-led invasion begins"),
    ("Afghanistan", "2021-08-15", "REGIME_CHANGE", "Taliban retake Kabul as US withdraws"),

    ("Syria", "2011-03-15", "REVOLUTION", "Civil war begins (Arab Spring uprising)"),
    ("Syria", "2024-12-08", "REGIME_CHANGE", "Assad government falls"),

    ("Cuba", "1959-01-01", "REVOLUTION", "Cuban Revolution, Batista overthrown"),
    ("Cuba", "1962-10-16", "DIPLOMATIC", "Cuban Missile Crisis begins"),

    ("Argentina", "1976-03-24", "REVOLUTION", "Military coup, start of the 'Dirty War' junta"),
    ("Argentina", "1982-04-02", "WAR", "Falklands War begins"),
    ("Argentina", "2001-12-20", "ECON_CRISIS", "Economic collapse, president resigns amid riots"),

    ("Greece", "2010-04-23", "ECON_CRISIS", "Requests EU/IMF bailout, sovereign debt crisis begins"),


    ("Zimbabwe", "2008-01-01", "ECON_CRISIS", "Hyperinflation crisis peaks"),

    ("Venezuela", "2016-01-01", "ECON_CRISIS", "Hyperinflation and economic collapse deepen"),
]
