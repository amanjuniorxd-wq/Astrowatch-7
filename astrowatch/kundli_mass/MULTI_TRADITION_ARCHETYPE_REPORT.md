# Multi-Tradition (Jyotisha + Hellenistic) Chart-Archetype Pattern Report

Corpus: famous_people_corpus.py -- 1304 people successfully charted across 7 fields (1 error(s), same already-known 'Homer (traditional)' legendary/undated entry as elsewhere in this project).

This extends the existing Jyotisha-only FAMOUS_PEOPLE_CHART_ARCHETYPE_REPORT.md with a second,
independently-weighted tradition (Hellenistic sect) applied to the SAME underlying sign data
(see dignity_tables.py) -- not a second independent astronomical claim, but a genuinely
different interpretive layer (sect vs. house) that can either converge or diverge with
Jyotisha's own house-based reading of the same 10th-house lord.

## Per-field summary

### ACTOR (n=175)

- 10th-lord Jyotisha dignity: {'OWN_SIGN': 40, 'NEUTRAL': 113, 'DEBILITATED': 12, 'EXALTED': 10}
- 10th-lord Hellenistic sect status: {'contrary_to_sect': 83, 'of_sect': 68, 'n/a (mercury/node)': 24}
- Chart sect distribution (day/night): {'day': 173, 'night': 2}
- Cross-tradition convergence on 10th-lord direction: {'DISAGREE': 56, 'AGREE_NEGATIVE': 24, 'AGREE_POSITIVE': 34, 'NO_SIGNAL': 61}
  (58/175 = 33% show the two traditions agreeing on direction; 56/175 = 32% disagree)

### ARTIST_DIRECTOR (n=141)

- 10th-lord Jyotisha dignity: {'NEUTRAL': 87, 'EXALTED': 15, 'DEBILITATED': 9, 'OWN_SIGN': 30}
- 10th-lord Hellenistic sect status: {'of_sect': 52, 'contrary_to_sect': 61, 'n/a (mercury/node)': 28}
- Chart sect distribution (day/night): {'night': 1, 'day': 140}
- Cross-tradition convergence on 10th-lord direction: {'DISAGREE': 41, 'AGREE_POSITIVE': 27, 'NO_SIGNAL': 60, 'AGREE_NEGATIVE': 13}
  (40/141 = 28% show the two traditions agreeing on direction; 41/141 = 29% disagree)

### ATHLETE (n=271)

- 10th-lord Jyotisha dignity: {'NEUTRAL': 168, 'OWN_SIGN': 55, 'DEBILITATED': 25, 'EXALTED': 23}
- 10th-lord Hellenistic sect status: {'contrary_to_sect': 124, 'of_sect': 98, 'n/a (mercury/node)': 49}
- Chart sect distribution (day/night): {'day': 271}
- Cross-tradition convergence on 10th-lord direction: {'AGREE_NEGATIVE': 26, 'NO_SIGNAL': 104, 'DISAGREE': 91, 'AGREE_POSITIVE': 50}
  (76/271 = 28% show the two traditions agreeing on direction; 91/271 = 34% disagree)

### AUTHOR (n=146)

- 10th-lord Jyotisha dignity: {'OWN_SIGN': 26, 'NEUTRAL': 92, 'DEBILITATED': 15, 'EXALTED': 13}
- 10th-lord Hellenistic sect status: {'contrary_to_sect': 52, 'of_sect': 69, 'n/a (mercury/node)': 25}
- Chart sect distribution (day/night): {'day': 146}
- Cross-tradition convergence on 10th-lord direction: {'DISAGREE': 42, 'NO_SIGNAL': 63, 'AGREE_POSITIVE': 26, 'AGREE_NEGATIVE': 15}
  (41/146 = 28% show the two traditions agreeing on direction; 42/146 = 29% disagree)

### BUSINESS (n=174)

- 10th-lord Jyotisha dignity: {'NEUTRAL': 113, 'OWN_SIGN': 34, 'DEBILITATED': 17, 'EXALTED': 10}
- 10th-lord Hellenistic sect status: {'contrary_to_sect': 82, 'of_sect': 64, 'n/a (mercury/node)': 28}
- Chart sect distribution (day/night): {'day': 168, 'night': 6}
- Cross-tradition convergence on 10th-lord direction: {'DISAGREE': 54, 'NO_SIGNAL': 73, 'AGREE_NEGATIVE': 17, 'AGREE_POSITIVE': 30}
  (47/174 = 27% show the two traditions agreeing on direction; 54/174 = 31% disagree)

### MUSICIAN (n=204)

- 10th-lord Jyotisha dignity: {'NEUTRAL': 131, 'OWN_SIGN': 43, 'EXALTED': 20, 'DEBILITATED': 10}
- 10th-lord Hellenistic sect status: {'of_sect': 93, 'contrary_to_sect': 82, 'n/a (mercury/node)': 29}
- Chart sect distribution (day/night): {'night': 5, 'day': 199}
- Cross-tradition convergence on 10th-lord direction: {'AGREE_POSITIVE': 48, 'DISAGREE': 64, 'NO_SIGNAL': 77, 'AGREE_NEGATIVE': 15}
  (63/204 = 31% show the two traditions agreeing on direction; 64/204 = 31% disagree)

### SCIENTIST (n=193)

- 10th-lord Jyotisha dignity: {'NEUTRAL': 132, 'OWN_SIGN': 36, 'EXALTED': 14, 'DEBILITATED': 11}
- 10th-lord Hellenistic sect status: {'of_sect': 71, 'n/a (mercury/node)': 31, 'contrary_to_sect': 91}
- Chart sect distribution (day/night): {'day': 192, 'night': 1}
- Cross-tradition convergence on 10th-lord direction: {'AGREE_POSITIVE': 32, 'DISAGREE': 63, 'NO_SIGNAL': 79, 'AGREE_NEGATIVE': 19}
  (51/193 = 26% show the two traditions agreeing on direction; 63/193 = 33% disagree)

## CRITICAL CAVEAT: chart-sect distribution is an ASSUMED_NOON artifact, not a finding

Self-check performed before finalizing this report: the near-universal 'day chart'
result above (e.g. ACTOR 173/175 day) is NOT a real astrological pattern. At an
ASSUMED_NOON birth time, the Sun is mechanically near its daily culmination (the
Midheaven), which in whole-sign houses almost always falls in house 9, 10, or 11 --
squarely inside the 7-12 'day chart' range regardless of who the person is or what
field they're in. Verified directly: three unrelated ASSUMED_NOON test charts (different
dates/timezones/latitudes) all produced Sun in house 10 or 11. Only 33 of 1305 people
in this corpus have a specifically DOCUMENTED (non-noon) birth time -- too few to
break out a meaningful per-field comparison on their own.

Practical consequence: the 'chart sect distribution' and 'cross-tradition convergence'
numbers above are substantially CONFOUNDED for any field whose corpus is mostly
ASSUMED_NOON entries (essentially all of them) -- they mostly reflect which of the
non-neutral planets (Sun/Jupiter/Saturn vs. Moon/Venus/Mars) happens to be that
field's most common 10th-house lord, crossed with an almost-constant 'day' sect,
rather than any real distribution of birth-time-sensitive sect across the field.
The 10th-lord JYOTISHA dignity numbers are NOT affected by this (dignity depends on
sign, not house/time-of-day), so that half of this report remains as reliable as the
original Jyotisha-only report.

## Limitations

- Structural (natal chart) analysis only -- no news/career-event correlation was
  attempted for the full 1305-person corpus in this pass (see module docstring);
  the real, individually-sourced correlation work remains the existing 53-person
  subset documented elsewhere in this project.
- Sign-level dignity only (no moolatrikona, no triplicity/term/face).
- Mercury and the lunar nodes are sect-neutral in this project's Hellenistic
  implementation (see dignity_tables.py) -- their 10th-lord rows show 'n/a'.
- Most charts use ASSUMED_NOON birth time (see famous_people_corpus.py docstring) --
  house placements (and therefore the 10th lord identity itself) are accordingly
  less reliable than Moon-based facts would be.