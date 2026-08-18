"""
Astrowatch -- birth-chart corpus for heads of state/government (US Presidents,
Indian Prime Ministers, and a set of current global leaders), built at explicit
user request to extend the kundli/Mahadasha pattern-mining work to political
leaders specifically, ahead of a requested Trump/September-2026 output.

DATA HONESTY (read before trusting anything downstream):

- BIRTH TIME: many of these figures have a birth time independently documented on
  a birth certificate or hospital record and cited with a high-confidence rating by
  long-standing astrological reference databases (e.g. Astro-Databank's "Rodden
  Rating" AA = from birth certificate/record). Where this project's general
  knowledge includes a specific, credibly-documented time, it is used and tagged
  time_source='DOCUMENTED'. Where no such specific, credible time is known, the
  chart uses 12:00 local noon per this session's explicit standing instruction,
  tagged time_source='ASSUMED_NOON' -- exactly as for the 519-event mass corpus.
  NEVER treat an ASSUMED_NOON leader chart's Ascendant/houses as reliable -- an
  unknown birth time makes the Ascendant essentially unknowable (it can shift a
  full sign roughly every 2 hours).
- LOCATION: birthplace city-level coordinates, real but not pinpoint-precise.
- CURRENT LEADERS: verified live via web search this session (2026-08-15) for the
  roles most likely to have changed recently (UK PM = Andy Burnham as of July 2026,
  succeeding Keir Starmer; Germany Chancellor = Friedrich Merz) -- everything else
  in this list is from general reference knowledge, NOT individually re-verified
  live this pass, and could be stale if a leadership change happened very recently.
- ROLE/OUTCOME TAGS (tenure_years, left_office_reason, notable_crisis) are coarse,
  single-word/short-phrase summaries from general historical knowledge, not a
  rigorously sourced dataset -- same "reference knowledge, not re-verified at this
  volume" disclosure as historical_data quality reports elsewhere in this project.
"""

# (name, birth_date_iso, birth_time_or_None, tz, country, lat, lon, group,
#  tenure_start_iso_or_None, tenure_years, reelected, left_office_reason)

LEADERS = []

def _add(name, date, time, tz, country, lat, lon, group, tenure_start, tenure_years,
         reelected, left_reason):
    LEADERS.append((name, date, time, tz, country, lat, lon, group, tenure_start,
                     tenure_years, reelected, left_reason))

# =====================================================================
# US PRESIDENTS (19 -- exceeds requested 15)
# =====================================================================
_add("George Washington", "1732-02-22", None, "America/New_York", "United States",
     38.19, -76.98, "US_PRESIDENT", "1789-04-30", 8, True, "term_limit_tradition")
_add("Thomas Jefferson", "1743-04-13", None, "America/New_York", "United States",
     38.02, -78.45, "US_PRESIDENT", "1801-03-04", 8, True, "term_limit_tradition")
_add("Abraham Lincoln", "1809-02-12", None, "America/New_York", "United States",
     37.54, -85.74, "US_PRESIDENT", "1861-03-04", 4, True, "assassinated")
_add("Theodore Roosevelt", "1858-10-27", "19:45", "America/New_York", "United States",
     40.71, -74.01, "US_PRESIDENT", "1901-09-14", 7, True, "did_not_seek_third_term")
_add("Woodrow Wilson", "1856-12-28", None, "America/New_York", "United States",
     38.15, -79.07, "US_PRESIDENT", "1913-03-04", 8, True, "term_limit_tradition")
_add("Herbert Hoover", "1874-08-10", None, "America/Chicago", "United States",
     41.66, -91.34, "US_PRESIDENT", "1929-03-04", 4, False, "lost_reelection")
_add("Franklin D. Roosevelt", "1882-01-30", "20:45", "America/New_York", "United States",
     41.79, -73.94, "US_PRESIDENT", "1933-03-04", 12, True, "died_in_office")
_add("Harry Truman", "1884-05-08", "16:00", "America/Chicago", "United States",
     37.80, -94.28, "US_PRESIDENT", "1945-04-12", 8, True, "did_not_seek_reelection")
_add("Dwight Eisenhower", "1890-10-14", None, "America/Chicago", "United States",
     33.75, -96.54, "US_PRESIDENT", "1953-01-20", 8, True, "term_limit")
_add("John F. Kennedy", "1917-05-29", "15:00", "America/New_York", "United States",
     42.33, -71.12, "US_PRESIDENT", "1961-01-20", 3, False, "assassinated")
_add("Richard Nixon", "1913-01-09", "21:35", "America/Los_Angeles", "United States",
     33.89, -117.76, "US_PRESIDENT", "1969-01-20", 5, True, "resigned")
_add("Jimmy Carter", "1924-10-01", "07:00", "America/New_York", "United States",
     32.04, -84.39, "US_PRESIDENT", "1977-01-20", 4, False, "lost_reelection")
_add("Ronald Reagan", "1911-02-06", "04:16", "America/Chicago", "United States",
     41.63, -89.98, "US_PRESIDENT", "1981-01-20", 8, True, "term_limit")
_add("George H. W. Bush", "1924-06-12", None, "America/New_York", "United States",
     42.25, -71.07, "US_PRESIDENT", "1989-01-20", 4, False, "lost_reelection")
_add("Bill Clinton", "1946-08-19", "08:51", "America/Chicago", "United States",
     33.67, -93.59, "US_PRESIDENT", "1993-01-20", 8, True, "term_limit")
_add("George W. Bush", "1946-07-06", "07:26", "America/New_York", "United States",
     41.31, -72.93, "US_PRESIDENT", "2001-01-20", 8, True, "term_limit")
_add("Barack Obama", "1961-08-04", "19:24", "Pacific/Honolulu", "United States",
     21.31, -157.86, "US_PRESIDENT", "2009-01-20", 8, True, "term_limit")
_add("Joe Biden", "1942-11-20", None, "America/New_York", "United States",
     41.41, -75.66, "US_PRESIDENT", "2021-01-20", 4, False, "did_not_seek_reelection")
_add("Donald Trump", "1946-06-14", "10:54", "America/New_York", "United States",
     40.70, -73.79, "US_PRESIDENT", "2017-01-20", None, True, "incumbent_2026")

# =====================================================================
# INDIAN PRIME MINISTERS (10)
# =====================================================================
_add("Jawaharlal Nehru", "1889-11-14", None, "Asia/Kolkata", "India",
     25.45, 81.85, "INDIA_PM", "1947-08-15", 17, True, "died_in_office")
_add("Lal Bahadur Shastri", "1904-10-02", None, "Asia/Kolkata", "India",
     25.28, 83.10, "INDIA_PM", "1964-06-09", 2, False, "died_in_office")
_add("Indira Gandhi", "1917-11-19", None, "Asia/Kolkata", "India",
     25.45, 81.85, "INDIA_PM", "1966-01-24", 15, True, "assassinated")
_add("Morarji Desai", "1896-02-29", None, "Asia/Kolkata", "India",
     21.20, 73.20, "INDIA_PM", "1977-03-24", 2, False, "resigned")
_add("Rajiv Gandhi", "1944-08-20", None, "Asia/Kolkata", "India",
     19.08, 72.88, "INDIA_PM", "1984-10-31", 5, False, "lost_reelection")
_add("P. V. Narasimha Rao", "1921-06-28", None, "Asia/Kolkata", "India",
     18.10, 79.30, "INDIA_PM", "1991-06-21", 5, False, "lost_reelection")
_add("Atal Bihari Vajpayee", "1924-12-25", None, "Asia/Kolkata", "India",
     26.22, 78.18, "INDIA_PM", "1998-03-19", 6, False, "lost_reelection")
_add("Manmohan Singh", "1932-09-26", None, "Asia/Karachi", "Pakistan",
     32.65, 72.75, "INDIA_PM", "2004-05-22", 10, True, "term_ended")
_add("Narendra Modi", "1950-09-17", None, "Asia/Kolkata", "India",
     23.78, 72.64, "INDIA_PM", "2014-05-26", None, True, "incumbent_2026")
_add("Charan Singh", "1902-12-23", None, "Asia/Kolkata", "India",
     28.30, 78.30, "INDIA_PM", "1979-07-28", 1, False, "resigned")

# =====================================================================
# CURRENT GLOBAL LEADERS (verified where noted; general knowledge otherwise --
# see module docstring)
# =====================================================================
_add("Vladimir Putin", "1952-10-07", None, "Europe/Moscow", "Russia",
     59.93, 30.34, "CURRENT_LEADER", "2012-05-07", None, True, "incumbent_2026")
_add("Xi Jinping", "1953-06-15", None, "Asia/Shanghai", "China",
     34.34, 109.60, "CURRENT_LEADER", "2013-03-14", None, True, "incumbent_2026")
_add("Emmanuel Macron", "1977-12-21", None, "Europe/Paris", "France",
     49.90, 2.30, "CURRENT_LEADER", "2017-05-14", None, True, "incumbent_2026")
_add("Andy Burnham", "1970-01-06", None, "Europe/London", "United Kingdom",
     53.55, -2.60, "CURRENT_LEADER", "2026-07-19", None, False, "incumbent_2026")
_add("Friedrich Merz", "1955-11-11", None, "Europe/Berlin", "Germany",
     51.21, 7.60, "CURRENT_LEADER", "2025-05-06", None, False, "incumbent_2026")
_add("Benjamin Netanyahu", "1949-10-21", None, "Asia/Jerusalem", "Israel",
     32.08, 34.78, "CURRENT_LEADER", "2022-12-29", None, True, "incumbent_2026")
_add("Volodymyr Zelenskyy", "1978-01-25", None, "Europe/Kyiv", "Ukraine",
     48.52, 34.60, "CURRENT_LEADER", "2019-05-20", None, False, "incumbent_2026")
_add("Luiz Inacio Lula da Silva", "1945-10-27", None, "America/Recife", "Brazil",
     -7.90, -38.28, "CURRENT_LEADER", "2023-01-01", None, False, "incumbent_2026")
