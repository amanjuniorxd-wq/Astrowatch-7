# Astrowatch Experimental Forecast — Hand-Executed Run

**Request:** `python forecast.py --date 2026-09-01 --region USA --domain POLITICAL` (and
the GLOBAL-scope equivalent, computed alongside for completeness)

**Why hand-executed, not run as `forecast.py`:** this session's sandbox cannot run
Python (see VALIDATION_REPORT.md — disk-space provisioning failure, re-confirmed
multiple times, plus two failed alternate agent-isolation execution paths). Every
number below comes from REAL data — live JPL Horizons and live Swiss Ephemeris queries,
fetched directly through this session's own tools — with the rule-matching arithmetic
worked by hand against that real data. Nothing below is fabricated or estimated from
memory. Where a step cannot be completed honestly, that is stated, not papered over.

**Exact timestamps:**
- Astronomical data fetched: `Wed Aug 12 11:17:44–11:17:54 2026, Pasadena, USA` (JPL
  Horizons response banners, this session)
- Ayanamsha fetched: same session, live query to `astro.com/cgi/swetest.cgi`
- This report assembled: 2026-08-12 (session date)

---

## 1. Astronomical configuration detected (real, live JPL Horizons data)

Source: `https://ssd.jpl.nasa.gov/api/horizons.api`, `EPHEM_TYPE=VECTORS`,
`REF_PLANE=ECLIPTIC`, `CENTER=500@399` (geocentric), target date 2026-09-01 00:00 TDB
(JD 2461284.5), ephemeris DE441. Geometric, no aberration (matches this project's
existing, documented pathway).

**Caveat, stated plainly:** longitudes below are derived as `atan2(Y, X)` on the
returned J2000-fixed ecliptic Cartesian vectors — i.e. **J2000-epoch-fixed**, not
precessed to the date of observation, consistent with `coordinates.ra_dec_to_ecliptic_j2000()`'s
documented behavior elsewhere in this project. This differs from true equinox-of-date
tropical longitude by roughly 0.36° (26 years × ~50.29″/yr) for 2026. **This does not
affect the rule-matching conclusion below**, because planet-to-planet angular
separations are unaffected by a common-mode offset — but absolute sign placement
carries this small, disclosed caveat.

| Body | X (km) | Y (km) | Tropical longitude (J2000-fixed) |
|---|---|---|---|
| Sun | −1.402134E+08 | 5.601580E+07 | **158.22°** (≈ Virgo 8.2°) |
| Moon | 3.412940E+05 | 1.594397E+05 | **25.04°** (≈ Aries 25.0°) |
| Mercury | −1.961829E+08 | 6.246027E+07 | **162.34°** (≈ Virgo 12.3°) |
| Venus | −7.631334E+07 | −3.207740E+07 | **202.80°** (≈ Libra 22.8°) |
| Mars | −6.237542E+07 | 2.696443E+08 | **103.03°** (≈ Cancer 13.0°) |
| Jupiter | −6.359935E+08 | 6.741459E+08 | **133.34°** (≈ Leo 13.3°) |
| Saturn | 1.250798E+09 | 2.957390E+08 | **13.30°** (≈ Aries 13.3°) |

(Longitude = `atan2(Y,X) mod 360`, hand-computed to ~0.05° precision from the fetched
vectors; full raw responses were fetched live this session and are available in this
conversation's tool history.)

## 2. Lahiri (sidereal) coordinates

Ayanamsha at JD 2461284.5 (2026-09-01, TT), live Swiss Ephemeris 2.10.03, sidereal mode
1 ("Lahiri"): **24°13′55.6279″ = 24.232119°** — `source: live_swisseph`, not the linear
fallback (per HARD SAFEGUARD #4, production mode never silently substitutes).

| Body | Sidereal longitude | Rāśi | Nakshatra (pada) |
|---|---|---|---|
| Sun | 133.99° | Simha 13.99° | Purva Phalguni, pada 1 |
| Moon | 0.81° | Mesha 0.81° | Ashwini, pada 1 |
| Mercury | 138.11° | Simha 18.11° | Purva Phalguni, pada 2 |
| Venus | 178.57° | Kanya 28.57° | Chitra, pada 2 |
| Mars | 78.80° | Mithuna 18.80° | Ardra, pada 4 |
| Jupiter | 109.11° | Karka 19.11° | Ashlesha, pada 1 |
| Saturn | 349.07° | Meena 19.07° | Revati, pada 1 |

(`rashi_for_longitude()` / `nakshatra_for_longitude()`, `rashi_nakshatra.py`, hand-traced
against these real sidereal values.)

## 3. Panchang (partial — see panchang.py for what's implemented)

- **Tithi:** (Moon − Sun) mod 360 = 226.82° → tithi 19 → **Krishna Chaturthi** (4th day
  of the waning fortnight)
- **Vara:** JD 2461284.5 → **Mangalavara (Tuesday)** — independently sanity-checked by
  calendar day-count from 2026-01-01 (a Thursday) forward 243 days: also lands on
  Tuesday. Consistent.
- **Nakshatra (Moon):** Ashwini, pada 1 (same as row above)
- **Yoga, Karana:** **NOT IMPLEMENTED** — `panchang.py` returns `None` for both rather
  than guessing at a binning convention this project hasn't researched.

## 4. Rules matched

**Zero.** Full evaluation below.

### Graha-yuddha check (Bṛhat Saṃhitā Ch. XVII, zodiac-independent, only the classical
5 planets — Mercury/Venus/Mars/Jupiter/Saturn — per the extracted text's own scope):

Minimum pairwise separation among all 10 pairs: **Mercury–Jupiter, 29.00°.** The
widest placeholder threshold in `aspects.GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG`
(`asavya_apasavya`) is 8.0°. **No pair is remotely close enough to classify**, by a
margin of over 20° — this conclusion is robust even given the ~0.05-0.3° imprecision in
the hand-computed longitudes above, and independent of the separate, already-flagged
concern that those thresholds are themselves unsourced placeholders (see aspects.py).
BS-17-04, 04b, 05, 05b, 17-16: **all fired=False.**

### Moon-latitude rules (BS-18-02, 18-06, 18-general): **NOT EVALUATED.** This project
has never implemented ecliptic-latitude computation (see AUDIT.md capability gap) —
these rules require knowing whether the Moon passes north or south of a planet, which
this pipeline cannot currently determine at all, fired or not.

### BS-19 (year-lord), BS-42 (price/omen), BS-20 (planetary shapes): **HISTORICALLY
UNRESOLVED — NOT USED.** `zodiac_requirement == "sidereal_unresolved"` for all of these
— untouched by this pass, per explicit instruction.

### Ptolemy PT-II-3 / PT-II-6 (triplicity / eclipse locality): **NOT EVALUATED.**
PT-II-6 requires confirming an actual solar/lunar eclipse on or near this date — not
checked this pass, not assumed. No eclipse-detection capability exists in this project.

### Geography safeguard (HARD SAFEGUARD #3), region = USA specifically:

**Every single rule above is additionally excluded from a USA-scoped forecast**, because
`geographic_specificity_for_rule()`'s allowlist is empty: no rule in `rule_registry.py`
documents a mechanism connecting to any specific modern country. BS rules use `"general"`
or name extinct peoples (Śaka, Bāhlīka, Sindh, Pahlava, Yavana); Ptolemy's PT-II-3
quadrant table covers the Hellenistic-era known world (Europe / southern Asia / northern
Asia / Africa-Libya) and does not include the Americas. Mapping any of this onto "USA"
would require inventing a geographic mechanism the source doesn't have — explicitly
disallowed.

## 5. Source of each rule

See table in section 4 — every rule cites `<author>, Ch. <chapter>, <citation>` from
`rule_registry.py`, unmodified this pass.

## 6. Historical evidence available

**None.** `historical_sample_size = 0` for every candidate. No historical backtest has
ever been run in this project — `VALIDATION_REPORT.md`'s own gate table still shows
`[ ] first blind historical backtest completed`, unchecked, at every phase including
this one.

## 7. Confidence / evidence status

`confidence = UNVALIDATED`, `evidence_level = UNVALIDATED` — derived mechanically from
`historical_sample_size == 0` (see `forecast._confidence_from_sample_size()`), not
chosen or adjusted by hand.

## 8. Final experimental forecast

```
ASTROWATCH EXPERIMENTAL FORECAST
Region:            USA
Forecast window:   1 September 2026 (7-day temporal precision requested)
Configuration:     Sun 158.22° Virgo / Moon 25.04° Aries / Mercury 162.34° Virgo /
                    Venus 202.80° Libra / Mars 103.03° Cancer / Jupiter 133.34° Leo /
                    Saturn 13.30° Aries (tropical, J2000-fixed; see caveat above)
Traditional rule:  NONE FIRED
Source:            N/A
Traditional association: N/A
Historical evidence: 0 comparable historical occurrences (no backtest exists)
Observed outcome:  N/A
Baseline:          N/A
Evidence:          UNVALIDATED
Status:            EXPERIMENTAL

NO FORECAST.

Reasons:
  1. No rule in the current registry legitimately fired for this configuration
     (closest planetary pairing, Mercury-Jupiter, is 29 degrees apart -- not remotely
     close to any conjunction-class threshold).
  2. Every rule that could theoretically apply was additionally excluded because none
     of them document a geographic mechanism connecting to the USA specifically.
  3. Three rules (BS-19, BS-42, BS-20) remain HISTORICALLY UNRESOLVED and are never
     used regardless of configuration.
  4. Several rules (BS-18, Ptolemy eclipse/triplicity) have no implemented detector in
     this project yet -- a missing capability, not a negative result.
  5. historical_sample_size = 0 -- even a fired rule would carry confidence=UNVALIDATED.

This is a traditional-astrology research forecast, not a certainty -- and in this case,
not a forecast at all.
```

**The GLOBAL-scope version of this same run (no country claimed) reaches the identical
NO FORECAST conclusion**, for reasons 1, 3, and 4 above (reason 2 doesn't apply when no
country is claimed) — the real Sept 2026 configuration simply doesn't produce a
qualifying match under any currently-implemented, sourced rule, geography aside.

## 9. Exact timestamp forecast was generated

Underlying data fetched **2026-08-12, 11:17:44–11:17:54 America/Los_Angeles** (JPL
Horizons response banners) and same-session for the Swiss Ephemeris ayanamsha query.
This report assembled the same session (2026-08-12). No prediction record was written
to `predictions.db` — per the schema's own rule, a record needs a real
`prediction_id`/`created_at` from an actually-executed run, and this was a hand-executed
demonstration, not an application run.

---

## What this run does and doesn't demonstrate

**Does:** shows the full pipeline's logic — real astronomical data in, real ayanamsha,
real Rāśi/Nakshatra/Panchang classification, real (negative) rule evaluation, honest
NO FORECAST output — traced end to end by hand, with every safeguard from the previous
instruction (no invented rules, no invented geography, no resolved-unresolved rules, no
fabricated confidence) intact and visibly doing its job.

**Doesn't:** prove `forecast.py` runs correctly as code — it has never been executed by
a Python interpreter. Doesn't establish that the pipeline would behave identically for a
configuration where a rule DOES fire (no such case was available in this test window to
exercise that path). Doesn't constitute a validated prediction method for anything,
including US politics — the honest output of a careful pipeline, run on real data with
real safeguards, was "no basis for a claim," which is itself the useful result.
