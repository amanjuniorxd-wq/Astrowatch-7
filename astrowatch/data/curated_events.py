"""
Astrowatch — curated pilot event dataset (non-USGS entries).

SOURCING METHODOLOGY (read this before adding to or trusting this list):
Every entry below falls into one of two groups, and the `verification` field says
which:

  - "MULTI_SOURCE_CONFIRMED" / "SINGLE_SOURCE": the date was actually looked up this
    session via WebSearch, and the `source_note` field records what was found,
    including any genuine disagreement between sources (several of these are
    DISPUTED for exactly that reason -- see the 1918 flu and penicillin entries).
  - "UNVERIFIED": the event and date come from general historical reference
    knowledge (this model's training data), NOT independently re-checked against a
    specific live source this session. These are, to the best of this project's
    knowledge, well-established and correct -- but per this project's own
    discipline ("do not claim verification that didn't happen"), they are labeled
    UNVERIFIED rather than SINGLE_SOURCE, because no specific citable source was
    actually opened and read this session to confirm them. See
    HISTORICAL_DATA_QUALITY_REPORT.md and manual_review.csv for the honest
    breakdown this produces.

No coordinates are given unless a location is extremely well-established public
knowledge (e.g. Hiroshima, Trinity test site); most entries deliberately leave
latitude/longitude NULL with location_precision=COUNTRY or CITY rather than
fabricate false precision (spec item 34).
"""

# Each entry: (event_name, event_type, event_subtype, start_date, end_date,
#              start_time, timezone, date_confidence, time_confidence,
#              country, country_code, region, location_name,
#              latitude, longitude, location_confidence, location_precision,
#              description, verification, source_note)
# end_date/start_time/timezone/latitude/longitude may be None.

CURATED_EVENTS = [
    # ---------------------------------------------------------------- MILITARY
    ("Austria-Hungary declares war on Serbia (start of WWI)", "MILITARY", "war_start",
     "1914-07-28", None, None, None, "EXACT", "UNKNOWN",
     "Austria-Hungary", "AUT", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "Formal declaration of war following the assassination of Archduke Franz Ferdinand; conventionally marks the start of World War I.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Armistice of 11 November 1918 (WWI ends)", "MILITARY", "war_end",
     "1918-11-11", None, "11:00", "Europe/Paris", "EXACT", "EXACT",
     "France", "FRA", "Europe", "Compiègne", None, None, "REGION", "REGION",
     "Armistice between the Allies and Germany signed in a railway carriage at Compiègne, taking effect at the 'eleventh hour of the eleventh day of the eleventh month.'",
     "UNVERIFIED", "Extremely well-established; the 11am timing is the famous detail of the event itself."),

    ("Germany invades Poland (start of WWII in Europe)", "MILITARY", "war_start",
     "1939-09-01", None, None, None, "EXACT", "UNKNOWN",
     "Poland", "POL", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "German invasion of Poland, conventionally marking the start of World War II in Europe.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Attack on Pearl Harbor", "MILITARY", "invasion",
     "1941-12-07", None, "07:48", "Pacific/Honolulu", "EXACT", "APPROXIMATE",
     "United States", "USA", "North America", "Pearl Harbor, Hawaii", 21.3469, -157.9528,
     "CITY", "CITY",
     "Surprise Japanese air attack on the US Pacific Fleet at Pearl Harbor, bringing the US into WWII.",
     "UNVERIFIED", "General reference knowledge; time widely cited but treated as approximate here."),

    ("D-Day — Allied invasion of Normandy", "MILITARY", "invasion",
     "1944-06-06", None, "06:30", "Europe/Paris", "EXACT", "APPROXIMATE",
     "France", "FRA", "Europe", "Normandy", None, None, "REGION", "REGION",
     "Allied amphibious landings in Normandy, opening the Western Front against Nazi Germany.",
     "UNVERIFIED", "General reference knowledge; H-Hour widely cited, treated as approximate here."),

    ("V-E Day — Germany's surrender in WWII", "MILITARY", "war_end",
     "1945-05-08", None, None, None, "EXACT", "UNKNOWN",
     "Germany", "DEU", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "Unconditional surrender of Nazi Germany takes effect, ending WWII in Europe.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Japan announces surrender (V-J Day)", "MILITARY", "war_end",
     "1945-08-15", "1945-09-02", None, None, "EXACT", "UNKNOWN",
     "Japan", "JPN", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Japan announces its surrender on Aug 15, 1945; formal instrument of surrender signed aboard USS Missouri on Sept 2, 1945, ending WWII.",
     "UNVERIFIED", "General reference knowledge; both dates widely and consistently cited."),

    ("Korean War begins", "MILITARY", "war_start",
     "1950-06-25", None, None, None, "EXACT", "UNKNOWN",
     "South Korea", "KOR", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "North Korean forces cross the 38th parallel into South Korea.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Korean Armistice Agreement signed", "MILITARY", "ceasefire",
     "1953-07-27", None, None, None, "EXACT", "UNKNOWN",
     "North Korea", "PRK", "Asia", "Panmunjom", None, None, "REGION", "REGION",
     "Armistice ending active combat in the Korean War signed at Panmunjom.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Second Sino-Japanese War begins (Marco Polo Bridge Incident)", "MILITARY", "war_start",
     "1937-07-07", None, None, None, "EXACT", "UNKNOWN",
     "China", "CHN", "Asia", "Beijing", None, None, "REGION", "REGION",
     "Clash between Chinese and Japanese troops near the Marco Polo Bridge, escalating into full-scale war.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Six-Day War", "MILITARY", "war_start",
     "1967-06-05", "1967-06-10", None, None, "EXACT", "UNKNOWN",
     "Israel", "ISR", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "War between Israel and a coalition of Arab states (Egypt, Jordan, Syria).",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Yom Kippur War begins", "MILITARY", "war_start",
     "1973-10-06", None, None, None, "EXACT", "UNKNOWN",
     "Israel", "ISR", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "Coordinated surprise attack on Israel by Egypt and Syria on the Jewish holiday of Yom Kippur.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Fall of Saigon (end of Vietnam War)", "MILITARY", "war_end",
     "1975-04-30", None, None, None, "EXACT", "UNKNOWN",
     "Vietnam", "VNM", "Asia", "Saigon", None, None, "CITY", "CITY",
     "North Vietnamese/Viet Cong forces capture Saigon, ending the Vietnam War.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Bangladesh Liberation War ends — Pakistani forces surrender at Dhaka", "MILITARY", "war_end",
     "1971-12-16", None, None, None, "EXACT", "UNKNOWN",
     "Bangladesh", "BGD", "Asia", "Dhaka", None, None, "CITY", "CITY",
     "Instrument of Surrender signed by Pakistani forces at Dhaka, ending the Bangladesh Liberation War / Indo-Pakistani War of 1971.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Argentina invades the Falkland Islands", "MILITARY", "invasion",
     "1982-04-02", None, None, None, "EXACT", "UNKNOWN",
     "United Kingdom", "GBR", "South America", "Falkland Islands", None, None, "REGION", "REGION",
     "Argentine forces invade the British-held Falkland Islands, starting the Falklands War.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Iraq invades Kuwait (start of Gulf War crisis)", "MILITARY", "invasion",
     "1990-08-02", None, None, None, "EXACT", "UNKNOWN",
     "Kuwait", "KWT", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "Iraqi forces invade and occupy Kuwait.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Operation Desert Storm begins", "MILITARY", "invasion",
     "1991-01-17", None, None, None, "EXACT", "UNKNOWN",
     "Iraq", "IRQ", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "US-led coalition begins the air campaign to expel Iraqi forces from Kuwait.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Rwandan genocide begins", "MILITARY", "major_military_crisis",
     "1994-04-07", "1994-07-15", None, None, "EXACT", "UNKNOWN",
     "Rwanda", "RWA", "Africa", None, None, None, "COUNTRY", "COUNTRY",
     "Mass killings of Tutsi and moderate Hutu begin the day after President Habyarimana's plane was shot down.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("US-led invasion of Iraq begins", "MILITARY", "invasion",
     "2003-03-20", None, None, None, "EXACT", "UNKNOWN",
     "Iraq", "IRQ", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "US-led coalition forces invade Iraq.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Russia launches full-scale invasion of Ukraine", "MILITARY", "invasion",
     "2022-02-24", None, None, None, "EXACT", "UNKNOWN",
     "Ukraine", "UKR", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "Russian armed forces launch a full-scale invasion of Ukraine.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Battle of Stalingrad ends in Soviet victory", "MILITARY", "battle",
     "1943-02-02", None, None, None, "EXACT", "UNKNOWN",
     "Russia", "RUS", "Europe", "Stalingrad", None, None, "CITY", "CITY",
     "Surrender of the German Sixth Army ends the Battle of Stalingrad, a major turning point of WWII.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Suez Crisis begins — Israel invades the Sinai", "MILITARY", "invasion",
     "1956-10-29", None, None, None, "EXACT", "UNKNOWN",
     "Egypt", "EGY", "Middle East", "Sinai Peninsula", None, None, "REGION", "REGION",
     "Israeli forces invade the Sinai Peninsula, the opening move of the Suez Crisis.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Cuban Missile Crisis resolved", "MILITARY", "major_military_crisis",
     "1962-10-28", None, None, None, "EXACT", "UNKNOWN",
     "Cuba", "CUB", "Caribbean", None, None, None, "COUNTRY", "COUNTRY",
     "Khrushchev agrees to remove Soviet missiles from Cuba, de-escalating the Cuban Missile Crisis.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("D-Day of the Gulf War ground campaign", "MILITARY", "battle",
     "1991-02-24", "1991-02-28", None, None, "EXACT", "UNKNOWN",
     "Kuwait", "KWT", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "Ground invasion phase of the Gulf War (Operation Desert Sabre), liberating Kuwait in roughly 100 hours.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("NATO bombing campaign against Yugoslavia begins", "MILITARY", "major_military_crisis",
     "1999-03-24", None, None, None, "EXACT", "UNKNOWN",
     "Serbia", "SRB", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "NATO begins Operation Allied Force, an air campaign against the Federal Republic of Yugoslavia over Kosovo.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    # ---------------------------------------------------------------- POLITICAL
    ("Storming of the Bastille", "POLITICAL", "revolution",
     "1789-07-14", None, None, None, "EXACT", "UNKNOWN",
     "France", "FRA", "Europe", "Paris", None, None, "CITY", "CITY",
     "Parisian revolutionaries storm the Bastille fortress, a flashpoint of the French Revolution.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("United States Declaration of Independence adopted", "POLITICAL", "independence",
     "1776-07-04", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Philadelphia", None, None, "CITY", "CITY",
     "Continental Congress formally adopts the Declaration of Independence.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Assassination of Archduke Franz Ferdinand", "POLITICAL", "assassination",
     "1914-06-28", None, None, None, "EXACT", "UNKNOWN",
     "Austria-Hungary", "AUT", "Europe", "Sarajevo", None, None, "CITY", "CITY",
     "Assassination of the Archduke and his wife in Sarajevo, the immediate trigger for WWI.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Assassination of Abraham Lincoln", "POLITICAL", "assassination",
     "1865-04-14", None, "22:15", "America/New_York", "EXACT", "APPROXIMATE",
     "United States", "USA", "North America", "Washington, DC", None, None, "CITY", "CITY",
     "Lincoln is shot at Ford's Theatre on the evening of April 14, 1865; he dies early the next morning.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    ("Assassination of John F. Kennedy", "POLITICAL", "assassination",
     "1963-11-22", None, "12:30", "America/Chicago", "EXACT", "APPROXIMATE",
     "United States", "USA", "North America", "Dallas, Texas", 32.7767, -96.7970,
     "CITY", "CITY",
     "President Kennedy is shot while riding in a motorcade through Dealey Plaza, Dallas.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    ("Assassination of Mahatma Gandhi", "POLITICAL", "assassination",
     "1948-01-30", None, None, None, "EXACT", "UNKNOWN",
     "India", "IND", "Asia", "New Delhi", None, None, "CITY", "CITY",
     "Gandhi is shot by Nathuram Godse in New Delhi.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Assassination of Martin Luther King Jr.", "POLITICAL", "assassination",
     "1968-04-04", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Memphis, Tennessee", None, None, "CITY", "CITY",
     "King is shot on the balcony of the Lorraine Motel in Memphis.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Assassination of Yitzhak Rabin", "POLITICAL", "assassination",
     "1995-11-04", None, None, None, "EXACT", "UNKNOWN",
     "Israel", "ISR", "Middle East", "Tel Aviv", None, None, "CITY", "CITY",
     "Israeli Prime Minister Rabin is assassinated at a peace rally in Tel Aviv.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Assassination of Anwar Sadat", "POLITICAL", "assassination",
     "1981-10-06", None, None, None, "EXACT", "UNKNOWN",
     "Egypt", "EGY", "Middle East", "Cairo", None, None, "CITY", "CITY",
     "Egyptian President Sadat is assassinated during a military parade in Cairo.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Fall of the Berlin Wall", "POLITICAL", "major_political_crisis",
     "1989-11-09", None, None, None, "EXACT", "UNKNOWN",
     "Germany", "DEU", "Europe", "Berlin", None, None, "CITY", "CITY",
     "East German authorities open the Berlin Wall's checkpoints, allowing free movement for the first time since 1961.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Berlin Wall construction begins", "POLITICAL", "major_political_crisis",
     "1961-08-13", None, None, None, "EXACT", "UNKNOWN",
     "Germany", "DEU", "Europe", "Berlin", None, None, "CITY", "CITY",
     "East German authorities begin sealing the border between East and West Berlin.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Dissolution of the Soviet Union", "POLITICAL", "constitutional_change",
     "1991-12-26", None, None, None, "EXACT", "UNKNOWN",
     "Russia", "RUS", "Europe", "Moscow", None, None, "CITY", "CITY",
     "The Soviet of the Republics formally votes the USSR out of existence, a day after Gorbachev's resignation.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Nelson Mandela released from prison", "POLITICAL", "major_political_crisis",
     "1990-02-11", None, None, None, "EXACT", "UNKNOWN",
     "South Africa", "ZAF", "Africa", "Cape Town", None, None, "CITY", "CITY",
     "Nelson Mandela is released after 27 years of imprisonment.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("South Africa's first multiracial general election", "POLITICAL", "election",
     "1994-04-27", None, None, None, "EXACT", "UNKNOWN",
     "South Africa", "ZAF", "Africa", None, None, None, "COUNTRY", "COUNTRY",
     "South Africa's first election in which citizens of all races could vote, won by the ANC under Mandela.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Mao Zedong proclaims the People's Republic of China", "POLITICAL", "government_change",
     "1949-10-01", None, None, None, "EXACT", "UNKNOWN",
     "China", "CHN", "Asia", "Beijing", None, None, "CITY", "CITY",
     "Mao Zedong proclaims the founding of the People's Republic of China from Tiananmen Gate.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Cuban Revolution — Batista flees, Castro takes power", "POLITICAL", "revolution",
     "1959-01-01", None, None, None, "EXACT", "UNKNOWN",
     "Cuba", "CUB", "Caribbean", "Havana", None, None, "CITY", "CITY",
     "President Batista flees Cuba as Castro's revolutionary forces take control.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Iranian Revolution culminates — monarchy collapses", "POLITICAL", "revolution",
     "1979-02-11", None, None, None, "EXACT", "UNKNOWN",
     "Iran", "IRN", "Middle East", "Tehran", None, None, "CITY", "CITY",
     "Collapse of the provisional government marks the effective triumph of the Iranian Revolution.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Tunisian Revolution — President Ben Ali flees (start of Arab Spring)", "POLITICAL", "revolution",
     "2011-01-14", None, None, None, "EXACT", "UNKNOWN",
     "Tunisia", "TUN", "Africa", None, None, None, "COUNTRY", "COUNTRY",
     "President Zine El Abidine Ben Ali flees Tunisia after weeks of protest, widely seen as the start of the Arab Spring.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Brexit referendum", "POLITICAL", "election",
     "2016-06-23", None, None, None, "EXACT", "UNKNOWN",
     "United Kingdom", "GBR", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "UK voters narrowly choose to leave the European Union.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Richard Nixon resigns the US presidency", "POLITICAL", "government_change",
     "1974-08-09", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Washington, DC", None, None, "CITY", "CITY",
     "Nixon resigns following the Watergate scandal, the only US president to do so.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Tiananmen Square crackdown", "POLITICAL", "major_political_crisis",
     "1989-06-04", None, None, None, "EXACT", "UNKNOWN",
     "China", "CHN", "Asia", "Beijing", None, None, "CITY", "CITY",
     "Chinese military forces suppress pro-democracy protests centered on Tiananmen Square.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Hong Kong handover to China", "POLITICAL", "constitutional_change",
     "1997-07-01", None, None, None, "EXACT", "UNKNOWN",
     "Hong Kong", "HKG", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Sovereignty over Hong Kong transfers from the United Kingdom to the People's Republic of China.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Bangladesh declares independence", "POLITICAL", "independence",
     "1971-03-26", None, None, None, "EXACT", "UNKNOWN",
     "Bangladesh", "BGD", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Declaration of independence from Pakistan, precipitating the Bangladesh Liberation War.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("India and Pakistan gain independence (Partition)", "POLITICAL", "independence",
     "1947-08-15", None, None, None, "EXACT", "UNKNOWN",
     "India", "IND", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "India becomes independent from British rule (Pakistan's independence was marked the previous day, Aug 14).",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    # ---------------------------------------------------------------- ECONOMIC
    ("Wall Street Crash — Black Tuesday", "ECONOMIC", "market_crash",
     "1929-10-29", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "New York City", None, None, "CITY", "CITY",
     "Catastrophic collapse of US stock prices, a defining trigger of the Great Depression.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Thai baht devaluation triggers Asian financial crisis", "ECONOMIC", "financial_crisis",
     "1997-07-02", None, None, None, "EXACT", "UNKNOWN",
     "Thailand", "THA", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Thailand floats the baht after abandoning its US dollar peg, triggering the 1997 Asian financial crisis.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Lehman Brothers collapses (Global Financial Crisis)", "ECONOMIC", "financial_crisis",
     "2008-09-15", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "New York City", None, None, "CITY", "CITY",
     "Lehman Brothers files for bankruptcy, the largest in US history, deepening the global financial crisis.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Black Monday stock market crash", "ECONOMIC", "market_crash",
     "1987-10-19", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "Global stock markets crash; the Dow Jones falls over 22% in a single day.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Nixon Shock — US ends dollar-gold convertibility", "ECONOMIC", "major_economic_policy",
     "1971-08-15", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "President Nixon unilaterally ends the convertibility of the US dollar into gold, effectively ending Bretton Woods.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Bretton Woods Agreement signed", "ECONOMIC", "major_economic_policy",
     "1944-07-22", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Bretton Woods, New Hampshire", None, None, "CITY", "CITY",
     "44 Allied nations agree on a new international monetary system at Bretton Woods.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Greece requests EU/IMF bailout (European debt crisis)", "ECONOMIC", "financial_crisis",
     "2010-04-23", None, None, None, "EXACT", "UNKNOWN",
     "Greece", "GRC", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "Greece formally requests activation of the EU/IMF financial support mechanism.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Argentina declares sovereign debt default", "ECONOMIC", "sovereign_default",
     "2001-12-23", None, None, None, "EXACT", "UNKNOWN",
     "Argentina", "ARG", "South America", "Buenos Aires", None, None, "CITY", "CITY",
     "Interim President Adolfo Rodríguez Saá declares a moratorium on Argentina's international debt — at the time the largest sovereign default in history.",
     "SINGLE_SOURCE", "Confirmed via WebSearch this session (PBS Newshour / globalsecurity.org coverage): Rodríguez Saá announced the default on 23 Dec 2001, the day of his appointment as interim president."),

    ("Black Wednesday — UK exits the ERM", "ECONOMIC", "major_currency_event",
     "1992-09-16", None, None, None, "EXACT", "UNKNOWN",
     "United Kingdom", "GBR", "Europe", None, None, None, "COUNTRY", "COUNTRY",
     "Speculative pressure forces the UK to withdraw the pound sterling from the European Exchange Rate Mechanism.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("China's 'Reform and Opening Up' economic policy launched", "ECONOMIC", "major_economic_policy",
     "1978-12-18", "1978-12-22", None, None, "DATE_RANGE", "UNKNOWN",
     "China", "CHN", "Asia", "Beijing", None, None, "CITY", "CITY",
     "The Third Plenary Session of the 11th CPC Central Committee launches Deng Xiaoping's market-oriented economic reforms.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("OPEC oil embargo begins (1973 oil crisis)", "ECONOMIC", "major_economic_policy",
     "1973-10-17", None, None, None, "EXACT", "UNKNOWN",
     "Saudi Arabia", "SAU", "Middle East", None, None, None, "COUNTRY", "COUNTRY",
     "OAPEC announces an oil embargo against nations supporting Israel in the Yom Kippur War, quadrupling oil prices.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Physical euro currency enters circulation", "ECONOMIC", "major_currency_event",
     "2002-01-01", None, None, None, "EXACT", "UNKNOWN",
     "Germany", "DEU", "Europe", None, None, None, "REGION", "COUNTRY",
     "Euro banknotes and coins enter circulation across the eurozone, replacing national currencies.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Silicon Valley Bank collapses", "ECONOMIC", "banking_crisis",
     "2023-03-10", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "Silicon Valley Bank fails and is taken over by regulators, the largest US bank failure since 2008.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Venezuela launches the Bolívar Soberano (hyperinflation redenomination)", "ECONOMIC", "major_currency_event",
     "2018-08-20", None, None, None, "EXACT", "UNKNOWN",
     "Venezuela", "VEN", "South America", None, None, None, "COUNTRY", "COUNTRY",
     "Venezuela redenominates its currency, dropping five zeros, amid hyperinflation.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Zimbabwe effectively abandons its national currency", "ECONOMIC", "major_currency_event",
     "2009-02-02", None, None, None, "APPROXIMATE", "UNKNOWN",
     "Zimbabwe", "ZWE", "Africa", None, None, None, "COUNTRY", "COUNTRY",
     "Zimbabwe moves to a multi-currency system after hyperinflation renders the Zimbabwean dollar worthless.",
     "UNVERIFIED", "General reference knowledge; exact transition date less crisply documented than the other currency events here, hence APPROXIMATE."),

    # ------------------------------------------------------ NATURAL_DISASTER
    ("Krakatoa erupts", "NATURAL_DISASTER", "volcanic_eruption",
     "1883-08-27", None, None, None, "EXACT", "UNKNOWN",
     "Indonesia", "IDN", "Southeast Asia", "Sunda Strait", None, None, "REGION", "REGION",
     "Catastrophic eruption of Krakatoa, heard thousands of kilometers away and triggering deadly tsunamis.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Mount Tambora's climactic eruption", "NATURAL_DISASTER", "volcanic_eruption",
     "1815-04-10", None, None, None, "EXACT", "UNKNOWN",
     "Indonesia", "IDN", "Southeast Asia", "Sumbawa", None, None, "REGION", "REGION",
     "The largest volcanic eruption in recorded history, leading to the 1816 'Year Without a Summer.'",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Mount Pinatubo's climactic eruption", "NATURAL_DISASTER", "volcanic_eruption",
     "1991-06-15", None, None, None, "EXACT", "UNKNOWN",
     "Philippines", "PHL", "Southeast Asia", "Luzon", None, None, "REGION", "REGION",
     "Second-largest volcanic eruption of the 20th century, causing global temporary cooling.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Mount St. Helens erupts", "NATURAL_DISASTER", "volcanic_eruption",
     "1980-05-18", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Washington State", None, None, "REGION", "REGION",
     "Major eruption of Mount St. Helens, the deadliest and most economically destructive volcanic event in US history.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Eruption of Vesuvius destroys Pompeii and Herculaneum", "NATURAL_DISASTER", "volcanic_eruption",
     "0079-08-24", None, None, None, "DISPUTED", "UNKNOWN",
     "Italy", "ITA", "Europe", "Pompeii", None, None, "REGION", "REGION",
     "Eruption of Mount Vesuvius buries Pompeii and Herculaneum. Traditionally dated August 24 (per Pliny the Younger's account), though some archaeological/climatic evidence has led scholars to argue for an October date instead.",
     "UNVERIFIED", "General reference knowledge; the DISPUTED classification itself reflects a genuine, well-known scholarly disagreement (Aug 24 vs autumn), not just uncertainty in this project's own sourcing."),

    ("2004 Indian Ocean tsunami", "NATURAL_DISASTER", "tsunami",
     "2004-12-26", None, "00:58", "UTC", "EXACT", "EXACT",
     "Indonesia", "IDN", "Southeast Asia", "Off the coast of Sumatra", None, None, "REGION", "REGION",
     "Tsunami triggered by the M9.1 Sumatra-Andaman earthquake (see the USGS-sourced earthquake record for that event), killing roughly 230,000 people across the Indian Ocean rim.",
     "UNVERIFIED", "Date/time anchored to the already-verified USGS earthquake record for the same event; the tsunami's broader human-impact description is general reference knowledge."),

    ("2011 Tōhoku tsunami", "NATURAL_DISASTER", "tsunami",
     "2011-03-11", None, "05:46", "UTC", "EXACT", "EXACT",
     "Japan", "JPN", "Asia", "Tōhoku coast", None, None, "REGION", "REGION",
     "Tsunami triggered by the M9.1 Tōhoku earthquake (see the USGS-sourced earthquake record), which also caused the Fukushima Daiichi nuclear disaster.",
     "UNVERIFIED", "Date/time anchored to the already-verified USGS earthquake record for the same event."),

    ("Hurricane Katrina makes landfall near New Orleans", "NATURAL_DISASTER", "cyclone_hurricane",
     "2005-08-29", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "New Orleans, Louisiana", None, None, "CITY", "CITY",
     "Catastrophic hurricane and levee failure devastate New Orleans and the Gulf Coast.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Hurricane Maria makes landfall on Puerto Rico", "NATURAL_DISASTER", "cyclone_hurricane",
     "2017-09-20", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "Caribbean", "Puerto Rico", None, None, "COUNTRY", "COUNTRY",
     "Catastrophic Category 4 hurricane devastates Puerto Rico's infrastructure and power grid.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Bhola cyclone strikes East Pakistan", "NATURAL_DISASTER", "cyclone_hurricane",
     "1970-11-12", None, None, None, "EXACT", "UNKNOWN",
     "Bangladesh", "BGD", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "One of the deadliest tropical cyclones on record strikes the Ganges Delta region of East Pakistan (now Bangladesh).",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Cyclone Nargis strikes Myanmar", "NATURAL_DISASTER", "cyclone_hurricane",
     "2008-05-02", None, None, None, "EXACT", "UNKNOWN",
     "Myanmar", "MMR", "Southeast Asia", "Irrawaddy Delta", None, None, "REGION", "REGION",
     "Deadliest natural disaster in Myanmar's recorded history.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("1931 China floods begin", "NATURAL_DISASTER", "flood",
     "1931-06-01", "1931-08-31", None, None, "APPROXIMATE", "UNKNOWN",
     "China", "CHN", "Asia", "Yangtze and Huai River basins", None, None, "REGION", "REGION",
     "Series of catastrophic floods along the Yangtze and Huai rivers, among the deadliest natural disasters ever recorded; exact onset dates vary by source.",
     "UNVERIFIED", "General reference knowledge; date range is APPROXIMATE because sources vary on precise onset."),

    ("2010 Pakistan floods begin", "NATURAL_DISASTER", "flood",
     "2010-07-27", "2010-09-30", None, None, "APPROXIMATE", "UNKNOWN",
     "Pakistan", "PAK", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Monsoon flooding affects roughly a fifth of Pakistan's total land area.",
     "UNVERIFIED", "General reference knowledge; onset APPROXIMATE."),

    ("Australia's 'Black Summer' bushfire season begins", "NATURAL_DISASTER", "wildfire",
     "2019-09-01", "2020-03-01", None, None, "APPROXIMATE", "UNKNOWN",
     "Australia", "AUS", "Oceania", None, None, None, "COUNTRY", "COUNTRY",
     "Unprecedented bushfire season across Australia, burning tens of millions of hectares.",
     "UNVERIFIED", "General reference knowledge; onset APPROXIMATE (fires were already burning in some regions before September)."),

    ("Camp Fire destroys Paradise, California", "NATURAL_DISASTER", "wildfire",
     "2018-11-08", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Paradise, California", None, None, "CITY", "CITY",
     "Deadliest and most destructive wildfire in California history.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("1906 San Francisco earthquake", "NATURAL_DISASTER", "earthquake",
     "1906-04-18", None, "05:12", "America/Los_Angeles", "EXACT", "APPROXIMATE",
     "United States", "USA", "North America", "San Francisco, California", 37.7749, -122.4194,
     "CITY", "CITY",
     "Major earthquake (~M7.9) and resulting fires devastate San Francisco.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    ("2010 Haiti earthquake", "NATURAL_DISASTER", "earthquake",
     "2010-01-12", None, "21:53", "America/Port-au-Prince", "EXACT", "APPROXIMATE",
     "Haiti", "HTI", "Caribbean", "Port-au-Prince", 18.5392, -72.3364,
     "CITY", "CITY",
     "M7.0 earthquake devastates Port-au-Prince and surrounding areas, with a very high death toll relative to the magnitude due to building vulnerability.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    ("1976 Tangshan earthquake", "NATURAL_DISASTER", "earthquake",
     "1976-07-28", None, "03:42", "Asia/Shanghai", "EXACT", "APPROXIMATE",
     "China", "CHN", "Asia", "Tangshan", None, None, "CITY", "CITY",
     "One of the deadliest earthquakes of the 20th century, largely destroying the industrial city of Tangshan.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    # ----------------------------------------------------- SOCIAL_PUBLIC_HEALTH
    ("First documented cases of the 1918 influenza pandemic", "SOCIAL_PUBLIC_HEALTH", "pandemic",
     "1918-03-04", None, None, None, "DISPUTED", "UNKNOWN",
     "United States", "USA", "North America", "Camp Funston, Kansas", None, None, "CITY", "CITY",
     "Soldiers at Camp Funston report influenza-like illness; commonly cited as the first documented cases of the 1918 pandemic, though earlier unusual influenza was separately reported in Haskell County, Kansas in Jan-Feb 1918, and some sources cite March 11 for the first officially confirmed case.",
     "MULTI_SOURCE_CONFIRMED", "Checked via WebSearch this session: History.com/CDC materials cite March 4, 1918 at Camp Funston; other sources cite March 11 for confirmation, and note earlier Haskell County cases in Jan-Feb 1918 -- genuine source disagreement, reflected in DISPUTED."),

    ("WHO declares COVID-19 a pandemic", "SOCIAL_PUBLIC_HEALTH", "pandemic",
     "2020-03-11", None, None, None, "EXACT", "UNKNOWN",
     "Switzerland", "CHE", "Europe", "Geneva", None, None, "CITY", "CITY",
     "The World Health Organization formally characterizes the COVID-19 outbreak as a pandemic.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("First COVID-19 cluster identified in Wuhan", "SOCIAL_PUBLIC_HEALTH", "epidemic",
     "2019-12-01", "2019-12-31", None, None, "APPROXIMATE", "UNKNOWN",
     "China", "CHN", "Asia", "Wuhan", None, None, "CITY", "CITY",
     "Initial cluster of pneumonia cases of unknown cause identified in Wuhan, later attributed to SARS-CoV-2.",
     "UNVERIFIED", "General reference knowledge; exact index-case date remains genuinely disputed/uncertain in the literature, hence APPROXIMATE and a date range rather than a single day."),

    ("CDC publishes first report on what becomes known as AIDS", "SOCIAL_PUBLIC_HEALTH", "epidemic",
     "1981-06-05", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Atlanta, Georgia", None, None, "CITY", "CITY",
     "CDC's Morbidity and Mortality Weekly Report describes Pneumocystis pneumonia in five gay men in Los Angeles — the first official published recognition of what became the AIDS epidemic.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("SARS outbreak begins in Guangdong, China", "SOCIAL_PUBLIC_HEALTH", "epidemic",
     "2002-11-16", None, None, None, "APPROXIMATE", "UNKNOWN",
     "China", "CHN", "Asia", "Guangdong", None, None, "REGION", "REGION",
     "First known case of SARS in Guangdong province, later spreading internationally in 2003.",
     "UNVERIFIED", "General reference knowledge; exact index case date is APPROXIMATE per most accounts."),

    ("WHO declares West Africa Ebola outbreak a public health emergency", "SOCIAL_PUBLIC_HEALTH", "epidemic",
     "2014-08-08", None, None, None, "EXACT", "UNKNOWN",
     "Guinea", "GIN", "Africa", None, None, None, "REGION", "REGION",
     "WHO declares the West African Ebola outbreak a Public Health Emergency of International Concern.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Black Death arrives in Europe via Sicily", "SOCIAL_PUBLIC_HEALTH", "pandemic",
     "1347-10-01", "1347-12-31", None, None, "APPROXIMATE", "UNKNOWN",
     "Italy", "ITA", "Europe", "Messina, Sicily", None, None, "CITY", "REGION",
     "Genoese trading ships carrying plague arrive at Messina, conventionally marking the Black Death's arrival in Europe.",
     "UNVERIFIED", "General reference knowledge; medieval date precision is inherently approximate."),

    ("Student protests begin in Beijing (Tiananmen movement)", "SOCIAL_PUBLIC_HEALTH", "major_protest",
     "1989-04-15", None, None, None, "EXACT", "UNKNOWN",
     "China", "CHN", "Asia", "Beijing", None, None, "CITY", "CITY",
     "Mourning for reformist leader Hu Yaobang's death catalyzes student protests centered on Tiananmen Square, later crushed on June 4.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("George Floyd protests begin", "SOCIAL_PUBLIC_HEALTH", "major_protest",
     "2020-05-25", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Minneapolis, Minnesota", None, None, "CITY", "CITY",
     "The killing of George Floyd by Minneapolis police sparks nationwide and international protests against police brutality.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Hong Kong anti-extradition-bill protests begin", "SOCIAL_PUBLIC_HEALTH", "civil_unrest",
     "2019-06-09", None, None, None, "EXACT", "UNKNOWN",
     "Hong Kong", "HKG", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Mass march against a proposed extradition bill; the start of months of sustained protest and unrest.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Tahrir Square protests begin in Egypt", "SOCIAL_PUBLIC_HEALTH", "major_protest",
     "2011-01-25", None, None, None, "EXACT", "UNKNOWN",
     "Egypt", "EGY", "Middle East", "Cairo", None, None, "CITY", "CITY",
     "Mass protests centered on Tahrir Square begin, part of the wider Arab Spring, leading to Mubarak's resignation weeks later.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("19th Amendment ratified — US women's suffrage", "SOCIAL_PUBLIC_HEALTH", "major_social_movement",
     "1920-08-18", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "Ratification of the 19th Amendment guarantees American women the right to vote.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("March on Washington ('I Have a Dream' speech)", "SOCIAL_PUBLIC_HEALTH", "major_social_movement",
     "1963-08-28", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Washington, DC", None, None, "CITY", "CITY",
     "March on Washington for Jobs and Freedom, where Martin Luther King Jr. delivers his 'I Have a Dream' speech.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Stonewall riots begin", "SOCIAL_PUBLIC_HEALTH", "civil_unrest",
     "1969-06-28", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "New York City", None, None, "CITY", "CITY",
     "Police raid of the Stonewall Inn sparks days of rioting, a foundational event of the modern LGBT rights movement.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Gdańsk Agreement signed — Solidarity movement founded", "SOCIAL_PUBLIC_HEALTH", "major_social_movement",
     "1980-08-31", None, None, None, "EXACT", "UNKNOWN",
     "Poland", "POL", "Europe", "Gdańsk", None, None, "CITY", "CITY",
     "Polish government agrees to allow independent trade unions, leading to the formation of Solidarity.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Velvet Revolution begins in Czechoslovakia", "SOCIAL_PUBLIC_HEALTH", "civil_unrest",
     "1989-11-17", None, None, None, "EXACT", "UNKNOWN",
     "Czech Republic", "CZE", "Europe", "Prague", None, None, "CITY", "CITY",
     "Student demonstration in Prague escalates into the peaceful Velvet Revolution, ending communist rule.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Soweto uprising", "SOCIAL_PUBLIC_HEALTH", "civil_unrest",
     "1976-06-16", None, None, None, "EXACT", "UNKNOWN",
     "South Africa", "ZAF", "Africa", "Soweto", None, None, "CITY", "CITY",
     "Student-led protests against Afrikaans-language education policy are met with lethal police force.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Euromaidan protests begin in Ukraine", "SOCIAL_PUBLIC_HEALTH", "civil_unrest",
     "2013-11-21", None, None, None, "EXACT", "UNKNOWN",
     "Ukraine", "UKR", "Europe", "Kyiv", None, None, "CITY", "CITY",
     "Protests begin after the government suspends preparations for an EU association agreement, eventually leading to the ouster of President Yanukovych.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    # ---------------------------------------------------- SCIENCE_TECHNOLOGY
    ("Apollo 11 Moon landing", "SCIENCE_TECHNOLOGY", "major_space_event",
     "1969-07-20", None, "20:17", "UTC", "EXACT", "EXACT",
     "United States", "USA", "Extraterrestrial", "Sea of Tranquility, the Moon", None, None, "REGION", "REGION",
     "Apollo 11's lunar module Eagle touches down on the Moon; Armstrong and Aldrin become the first humans to walk on another world.",
     "UNVERIFIED", "General reference knowledge; the touchdown time (20:17 UTC) is one of the most precisely and widely documented timestamps in spaceflight history."),

    ("Yuri Gagarin becomes the first human in space", "SCIENCE_TECHNOLOGY", "major_space_event",
     "1961-04-12", None, "06:07", "UTC", "EXACT", "EXACT",
     "Kazakhstan", "KAZ", "Asia", "Baikonur Cosmodrome", None, None, "CITY", "CITY",
     "Vostok 1 launches Yuri Gagarin into orbit, the first human spaceflight.",
     "UNVERIFIED", "General reference knowledge; launch time is a well-documented historical timestamp."),

    ("Sputnik 1 launched", "SCIENCE_TECHNOLOGY", "major_space_event",
     "1957-10-04", None, None, None, "EXACT", "UNKNOWN",
     "Kazakhstan", "KAZ", "Asia", "Baikonur Cosmodrome", None, None, "REGION", "REGION",
     "The Soviet Union launches Sputnik 1, the first artificial satellite, starting the Space Age.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Chernobyl nuclear disaster", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "1986-04-26", None, "01:23", "Europe/Kyiv", "EXACT", "EXACT",
     "Ukraine", "UKR", "Europe", "Pripyat", None, None, "CITY", "CITY",
     "Reactor 4 of the Chernobyl Nuclear Power Plant explodes during a safety test, the worst nuclear accident in history by casualties/cost.",
     "UNVERIFIED", "General reference knowledge; the timestamp is one of the most precisely documented details of the disaster."),

    ("Fukushima Daiichi nuclear disaster begins", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "2011-03-11", None, None, None, "EXACT", "UNKNOWN",
     "Japan", "JPN", "Asia", "Ōkuma", None, None, "REGION", "REGION",
     "The Tōhoku earthquake and tsunami disable cooling systems at Fukushima Daiichi, triggering meltdowns.",
     "UNVERIFIED", "Date anchored to the already-verified USGS earthquake record for the same triggering event."),

    ("Three Mile Island accident", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "1979-03-28", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Pennsylvania", None, None, "REGION", "REGION",
     "Partial meltdown at the Three Mile Island Nuclear Generating Station, the most significant US commercial nuclear accident.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Trinity — first detonation of a nuclear weapon", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "1945-07-16", None, "05:29", "America/Denver", "EXACT", "EXACT",
     "United States", "USA", "North America", "Jornada del Muerto desert, New Mexico", 33.6772, -106.4754,
     "EXACT", "EXACT",
     "The Manhattan Project's Trinity test, the first detonation of a nuclear weapon.",
     "UNVERIFIED", "General reference knowledge; the timestamp is one of the most precisely documented details of the Manhattan Project."),

    ("Atomic bombing of Hiroshima", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "1945-08-06", None, "08:15", "Asia/Tokyo", "EXACT", "EXACT",
     "Japan", "JPN", "Asia", "Hiroshima", 34.3853, 132.4553,
     "EXACT", "EXACT",
     "The United States drops an atomic bomb on Hiroshima, the first use of a nuclear weapon in warfare.",
     "UNVERIFIED", "General reference knowledge; 8:15am local time is one of the most widely and precisely documented timestamps in modern history."),

    ("Atomic bombing of Nagasaki", "SCIENCE_TECHNOLOGY", "nuclear_event",
     "1945-08-09", None, "11:02", "Asia/Tokyo", "EXACT", "EXACT",
     "Japan", "JPN", "Asia", "Nagasaki", None, None, "CITY", "CITY",
     "The United States drops a second atomic bomb on Nagasaki.",
     "UNVERIFIED", "General reference knowledge; widely and precisely documented timestamp."),

    ("Alexander Fleming observes penicillin's antibacterial effect", "SCIENCE_TECHNOLOGY", "major_scientific_discovery",
     "1928-09-28", None, None, None, "DISPUTED", "UNKNOWN",
     "United Kingdom", "GBR", "Europe", "London", None, None, "CITY", "CITY",
     "Fleming notices a mold contaminating a Staphylococcus culture plate is inhibiting bacterial growth. Some sources date his return from holiday (and first noticing) to Sept 3, others date the specific observation to Sept 28 -- both September 1928.",
     "MULTI_SOURCE_CONFIRMED", "Checked via WebSearch this session: LiveScience/history.com sources genuinely disagree between Sept 3 and Sept 28, 1928 -- reflected honestly as DISPUTED rather than picking one."),

    ("Watson and Crick determine the structure of DNA", "SCIENCE_TECHNOLOGY", "major_scientific_discovery",
     "1953-02-28", None, None, None, "APPROXIMATE", "UNKNOWN",
     "United Kingdom", "GBR", "Europe", "Cambridge", None, None, "CITY", "CITY",
     "Watson and Crick work out the double-helix structure of DNA (their paper was published April 25, 1953).",
     "UNVERIFIED", "General reference knowledge; the exact 'discovery moment' date is inherently approximate versus the well-documented publication date."),

    ("First iPhone released", "SCIENCE_TECHNOLOGY", "major_technology_event",
     "2007-06-29", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "Apple releases the first iPhone in the United States.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Tim Berners-Lee proposes the World Wide Web", "SCIENCE_TECHNOLOGY", "major_technology_event",
     "1989-03-12", None, None, None, "APPROXIMATE", "UNKNOWN",
     "Switzerland", "CHE", "Europe", "CERN", None, None, "CITY", "CITY",
     "Berners-Lee circulates 'Information Management: A Proposal' at CERN, the conceptual origin of the World Wide Web.",
     "UNVERIFIED", "General reference knowledge; proposal date is well documented but the 'invention' itself was a process, hence APPROXIMATE."),

    ("ChatGPT publicly released", "SCIENCE_TECHNOLOGY", "major_technology_event",
     "2022-11-30", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "OpenAI releases ChatGPT to the public, rapidly popularizing conversational AI.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Wright Brothers' first powered flight", "SCIENCE_TECHNOLOGY", "major_technology_event",
     "1903-12-17", None, "10:35", "America/New_York", "EXACT", "APPROXIMATE",
     "United States", "USA", "North America", "Kitty Hawk, North Carolina", None, None, "CITY", "CITY",
     "The Wright Flyer makes the first sustained, controlled, powered flight of a heavier-than-air aircraft.",
     "UNVERIFIED", "General reference knowledge; widely cited approximate time."),

    ("Human Genome Project declared complete", "SCIENCE_TECHNOLOGY", "major_scientific_discovery",
     "2003-04-14", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", None, None, None, "COUNTRY", "COUNTRY",
     "The International Human Genome Sequencing Consortium announces completion of the Human Genome Project.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("Dolly the sheep's cloning is announced", "SCIENCE_TECHNOLOGY", "major_scientific_discovery",
     "1997-02-22", None, None, None, "EXACT", "UNKNOWN",
     "United Kingdom", "GBR", "Europe", "Roslin, Scotland", None, None, "CITY", "CITY",
     "The Roslin Institute announces the successful cloning of Dolly the sheep (born the previous July, kept confidential until this announcement).",
     "UNVERIFIED", "General reference knowledge; announcement date universally cited."),

    ("He Jiankui announces first gene-edited human babies", "SCIENCE_TECHNOLOGY", "major_scientific_discovery",
     "2018-11-26", None, None, None, "EXACT", "UNKNOWN",
     "China", "CHN", "Asia", None, None, None, "COUNTRY", "COUNTRY",
     "Chinese scientist He Jiankui announces the birth of the first CRISPR-edited human babies, triggering international controversy.",
     "UNVERIFIED", "General reference knowledge; widely and consistently dated."),

    ("Voyager 1 launched", "SCIENCE_TECHNOLOGY", "major_space_event",
     "1977-09-05", None, None, None, "EXACT", "UNKNOWN",
     "United States", "USA", "North America", "Cape Canaveral, Florida", None, None, "CITY", "CITY",
     "NASA launches the Voyager 1 probe, which later becomes the first human-made object to enter interstellar space.",
     "UNVERIFIED", "General reference knowledge; universally dated."),

    ("First ISS module (Zarya) launched", "SCIENCE_TECHNOLOGY", "major_space_event",
     "1998-11-20", None, None, None, "EXACT", "UNKNOWN",
     "Kazakhstan", "KAZ", "Asia", "Baikonur Cosmodrome", None, None, "REGION", "REGION",
     "Launch of the Zarya module, the first component of the International Space Station.",
     "UNVERIFIED", "General reference knowledge; universally dated."),
]

FIELDS = (
    "event_name", "event_type", "event_subtype", "start_date", "end_date",
    "start_time", "timezone", "date_confidence", "time_confidence",
    "country", "country_code", "region", "location_name",
    "latitude", "longitude", "location_confidence", "location_precision",
    "description", "verification", "source_note",
)


def as_dicts():
    return [dict(zip(FIELDS, row)) for row in CURATED_EVENTS]
