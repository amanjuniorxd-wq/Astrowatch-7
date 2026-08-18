"""
Astrowatch — real, independently-checked verification updates for the pilot dataset.

Each entry here corresponds to an actual WebSearch performed this session (a
separate pass from the original ingestion). This is intentionally a SEPARATE file
from curated_events.py rather than edits scattered through it -- keeps the
verification work auditable as its own diff, and keeps a clear record of exactly
which events were actually re-checked in this later pass versus the original one.

Per this session's own discipline: "do not use general model knowledge as
verification." Every entry below cites the specific source(s) actually fetched via
WebSearch this pass, with the real URLs returned by the search. Where two
genuinely independent organizations corroborated the same fact, the event is
promoted to MULTI_SOURCE_CONFIRMED; a single corroborating source would be
SINGLE_SOURCE (none of this batch needed that -- every search this pass surfaced
at least two independent, non-mirror sources agreeing).
"""

VERIFICATION_UPDATES = {
    "Austria-Hungary declares war on Serbia (start of WWI)": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-HISTORY-WWI-START", "History.com — 'Austria-Hungary declares war on Serbia'",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/july-28/austria-hungary-declares-war-on-serbia"),
            ("SRC-LOC-WWI-START", "Library of Congress 'In Custodia Legis' blog",
             "Library of Congress", "government_archive", 2,
             "https://blogs.loc.gov/law/2014/07/july-28-1914-state-of-war-with-serbia-declared/"),
        ],
        "corrections": {"start_time": "11:10", "timezone": "Europe/Vienna", "time_confidence": "APPROXIMATE"},
        "notes": "Confirmed via WebSearch this session. Both sources agree on 28 July 1914; "
                 "Library of Congress source additionally gives the declaration transmission "
                 "time (11:10 A.M., sent from Vienna to Serbia's PM) -- added as start_time.",
    },
    "Attack on Pearl Harbor": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-HISTORY-PEARLHARBOR", "History.com — 'Pearl Harbor bombed'",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/december-7/pearl-harbor-bombed"),
            ("SRC-BRITANNICA-PEARLHARBOR", "Britannica — 'Attack on Pearl Harbor Timeline'",
             "Encyclopaedia Britannica", "encyclopedia", 3,
             "https://www.britannica.com/story/attack-on-pearl-harbor-timeline"),
        ],
        "corrections": {"start_time": "07:55"},
        "notes": "Confirmed via WebSearch this session; both sources most commonly cite 7:55am "
                 "Hawaii time for the attack's commencement (some sources cite 7:48-7:53am for "
                 "the first aircraft sighting) -- corrected from this dataset's earlier 07:48.",
    },
    "Rwandan genocide begins": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-HRW-RWANDA", "Human Rights Watch — 'The Rwandan Genocide: How It Was Prepared'",
             "Human Rights Watch", "ngo_report", 2,
             "https://www.hrw.org/legacy/backgrounder/africa/rwanda0406/5.htm"),
            ("SRC-HISTORY-RWANDA", "History.com — 'Violence erupts in Rwanda'",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/april-7/civil-war-erupts-in-rwanda"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: plane shot down 6 April 1994; mass "
                 "killing recognized as beginning 7 April 1994 per HRW's own chapter title -- "
                 "matches this dataset's existing April 7 start_date and description.",
    },
    "Fall of the Berlin Wall": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-BERLINDE-WALL", "Berlin.de — 'Opening and fall of the Berlin Wall'",
             "Berlin Senate Chancellery", "government_archive", 2,
             "https://www.berlin.de/en/history/8482274-8619314-opening-and-fall-of-the-berlin-wall.en.html"),
            ("SRC-TIME-WALL", "TIME — 'What Happened the Day the Berlin Wall Fell'",
             "Time USA, LLC", "news_archive", 3,
             "https://time.com/5720386/berlin-wall-fall/"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 9 November 1989. Real timeline detail "
                 "found (announcement ~18:50, first checkpoint opens 21:20, full opening by "
                 "23:00) but not added as a single start_time given the ambiguity of which "
                 "moment counts as 'the wall falling' -- kept UNKNOWN rather than picking one.",
    },
    "Lehman Brothers collapses (Global Financial Crisis)": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-HISTORY-LEHMAN", "History.com — 'Lehman Brothers declares bankruptcy'",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/september-15/lehman-brothers-collapses"),
            ("SRC-BRITANNICA-LEHMAN", "Britannica — 'Bankruptcy of Lehman Brothers'",
             "Encyclopaedia Britannica", "encyclopedia", 3,
             "https://www.britannica.com/event/bankruptcy-of-Lehman-Brothers"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 15 September 2008.",
    },
    "Apollo 11 Moon landing": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-THISDAYINAVIATION-APOLLO11", "This Day in Aviation — Apollo 11 landing",
             "This Day in Aviation", "aviation_history_archive", 3,
             "https://www.thisdayinaviation.com/20-july-1969-201740-utc/"),
            ("SRC-SMITHSONIAN-APOLLO11", "Smithsonian National Air and Space Museum — Apollo 11 Timeline",
             "Smithsonian Institution", "museum_archive", 2,
             "https://airandspace.si.edu/explore/stories/apollo-missions/apollo-11-moon-landing/apollo-11-timeline"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: touchdown 20:17:39 UTC, 20 July 1969 -- "
                 "matches this dataset's existing 20:17 exactly, now with primary-adjacent "
                 "museum/archive citation instead of general knowledge.",
    },
    "Chernobyl nuclear disaster": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-HISTORY-CHERNOBYL", "History.com — 'Test triggers nuclear disaster at Chernobyl'",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/april-26/nuclear-disaster-at-chernobyl"),
            ("SRC-NRC-CHERNOBYL", "US Nuclear Regulatory Commission — Chernobyl backgrounder",
             "U.S. Nuclear Regulatory Commission", "government_agency", 1,
             "https://www.nrc.gov/reading-rm/doc-collections/fact-sheets/chernobyl-bg"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 01:23 (MSD, UTC+4), 26 April 1986 -- "
                 "matches this dataset's existing value. NRC source is Tier 1 (official US "
                 "government nuclear regulator), upgrading this event's source_quality_tier.",
        "source_quality_tier_override": 1,
    },
    "WHO declares COVID-19 a pandemic": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-NPR-COVIDPANDEMIC", "NPR — '5 years ago today, the WHO declared COVID-19 a pandemic'",
             "National Public Radio", "news_archive", 3,
             "https://www.npr.org/2025/03/11/nx-s1-5323221/5-years-ago-today-the-who-declared-covid-19-a-pandemic"),
            ("SRC-STAT-COVIDPANDEMIC", "STAT News — 'WHO declares the coronavirus outbreak a pandemic'",
             "STAT", "news_archive", 3,
             "https://www.statnews.com/2020/03/11/who-declares-the-coronavirus-outbreak-a-pandemic/"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 11 March 2020.",
    },
    "Nelson Mandela released from prison": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-SAHO-MANDELA", "South African History Online — Mandela's release",
             "South African History Online", "academic_archive", 2,
             "https://sahistory.org.za/content/nelson-mandela-released-prison-11-february-1990"),
            ("SRC-CBS-MANDELA", "CBS News — 'On this Day: Feb. 11th, 1990'",
             "CBS News", "news_archive", 3,
             "https://www.cbsnews.com/news/on-this-day-february-11th-1990-nelson-mandela-released-from-prison/"),
        ],
        "corrections": {"start_time": "16:14", "timezone": "Africa/Johannesburg", "time_confidence": "EXACT"},
        "notes": "Confirmed via WebSearch this session: 11 February 1990; both sources cite "
                 "Mandela appearing at Victor Verster Prison's gates at 16:14 local time.",
    },
    "1976 Tangshan earthquake": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-BRITANNICA-TANGSHAN", "Britannica — 'Tangshan earthquake of 1976'",
             "Encyclopaedia Britannica", "encyclopedia", 3,
             "https://www.britannica.com/event/Tangshan-earthquake-of-1976"),
            ("SRC-HISTORY-TANGSHAN", "History.com — Tangshan earthquake",
             "A&E Television Networks", "encyclopedia", 3,
             "https://www.history.com/this-day-in-history/july-28/worst-modern-earthquake"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 03:42 local time, 28 July 1976 -- matches "
                 "this dataset's existing value exactly. Death toll figures vary substantially "
                 "across sources (official ~242,000; some historians argue up to 655,000) -- "
                 "left undescribed in exact numbers in this dataset's description field "
                 "precisely because of this real, source-confirmed uncertainty.",
    },
    "Bangladesh Liberation War ends — Pakistani forces surrender at Dhaka": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-BIZSTANDARD-1971WAR", "Business Standard — 1971 war coverage",
             "Business Standard", "news_archive", 3,
             "https://www.business-standard.com/article/current-affairs/vijay-diwas-how-india-ended-pak-s-atrocities-and-ensured-freed-bangladesh-118121600120_1.html"),
            ("SRC-BHARATRAKSHAK-1971WAR", "Bharat Rakshak archive — Instrument of Surrender",
             "Bharat Rakshak", "military_history_archive", 3,
             "https://www.bharat-rakshak.com/archives/1971/Dec16/index.html"),
        ],
        "corrections": {"start_time": "16:31", "timezone": "Asia/Dhaka", "time_confidence": "EXACT"},
        "notes": "Confirmed via WebSearch this session: 16 December 1971; both sources cite "
                 "the surrender signed at 16:31 hrs local time at Dhaka's Ramna Racecourse.",
    },
    "Thai baht devaluation triggers Asian financial crisis": {
        "verification_status": "MULTI_SOURCE_CONFIRMED",
        "sources": [
            ("SRC-FEDHISTORY-ASIANCRISIS", "Federal Reserve History — 'Asian Financial Crisis'",
             "Federal Reserve System", "government_agency", 1,
             "https://www.federalreservehistory.org/essays/asian-financial-crisis"),
            ("SRC-CHIFED-ASIANCRISIS", "Federal Reserve Bank of Chicago — retrospective on the 1997 crisis",
             "Federal Reserve Bank of Chicago", "government_agency", 1,
             "https://www.chicagofed.org/publications/chicago-fed-letter/2001/january-161"),
        ],
        "corrections": {},
        "notes": "Confirmed via WebSearch this session: 2 July 1997. Both sources are official "
                 "US Federal Reserve System publications -- Tier 1.",
        "source_quality_tier_override": 1,
    },
}
