"""
Astrowatch — configuration / aspect detection engine
=================================================
Takes a set of {body: ecliptic_longitude_deg} and detects classical Ptolemaic aspects
under a CONFIGURABLE orb table (different traditions use different orbs -- do not
hard-code modern astrology's default orbs as if they were universal).

Also implements the Bṛhat Saṃhitā's OWN, separate proximity classification for
planet-to-planet conjunctions (graha-yuddha, Ch. XVII), which is not the same system
as Ptolemaic aspects and must not be collapsed into it.

STATUS: written this session, NOT executed against live data (sandbox unavailable).
Logic is plain arithmetic on angle differences and has been reasoned through by hand;
still needs a run against real numbers before being trusted for a backtest.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---- Ptolemaic aspect engine -------------------------------------------------

PTOLEMAIC_ASPECTS = {
    "conjunction": 0,
    "sextile": 60,
    "square": 90,
    "trine": 120,
    "opposition": 180,
}

# Default orb table -- EXPLICITLY a modern-convention default, not sourced from the
# Tetrabiblos text itself (Ptolemy discusses aspects qualitatively; he does not give a
# clean numeric orb table in the portion of Book I extracted so far). Treat this as a
# placeholder to be replaced once/if an orb rule is actually found in the corpus, and
# always report which orb table was used alongside any detected aspect.
DEFAULT_ORB_DEG = {
    "conjunction": 8.0,
    "sextile": 4.0,
    "square": 6.0,
    "trine": 6.0,
    "opposition": 8.0,
}


@dataclass
class DetectedAspect:
    body_a: str
    body_b: str
    aspect: str
    exact_angle: float
    actual_separation: float
    orb_used: float
    orb_table_name: str


def angular_separation(lon_a: float, lon_b: float) -> float:
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def detect_aspects(
    positions: Dict[str, float],
    orb_table: Optional[Dict[str, float]] = None,
    orb_table_name: str = "default_modern_placeholder",
    aspect_set: Optional[Dict[str, float]] = None,
) -> List[DetectedAspect]:
    """
    positions: {body_name: ecliptic_longitude_deg}
    orb_table: {aspect_name: allowed_orb_deg} -- pass a different table per tradition.
    aspect_set: which aspects to test for -- defaults to the five Ptolemaic aspects.
    """
    orb_table = orb_table or DEFAULT_ORB_DEG
    aspect_set = aspect_set or PTOLEMAIC_ASPECTS

    bodies = list(positions.keys())
    found: List[DetectedAspect] = []
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            a, b = bodies[i], bodies[j]
            sep = angular_separation(positions[a], positions[b])
            for aspect_name, exact_angle in aspect_set.items():
                orb = orb_table.get(aspect_name, 0.0)
                if abs(sep - exact_angle) <= orb:
                    found.append(DetectedAspect(
                        body_a=a, body_b=b, aspect=aspect_name,
                        exact_angle=exact_angle, actual_separation=sep,
                        orb_used=orb, orb_table_name=orb_table_name,
                    ))
    return found


# ---- Bṛhat Saṃhitā Ch. XVII graha-yuddha proximity classes -------------------
# Four named classes, by CLOSENESS (not by fixed aspect angle like Ptolemy). The
# actual visual-eclipsing thresholds are not given as clean numeric degree cutoffs in
# the extracted text (they're described qualitatively -- discs "eclipsed," discs
# "rubbing," light "mixing," or "distinctly apart"). This function uses an editorial
# placeholder mapping onto angular separation, clearly flagged as NOT textually
# sourced -- fill in with a properly researched numeric threshold (e.g. from a
# secondary scholarly source on classical Indian planetary-war orbs) before treating
# this classification as authoritative.
GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG = {
    "bheda": 0.5,          # PLACEHOLDER -- "one disc eclipsed by the other"
    "ullekha": 1.0,        # PLACEHOLDER -- "discs appear to touch/rub"
    "amsumardana": 3.0,    # PLACEHOLDER -- "light of the two mixes"
    # beyond amsumardana threshold and within general conjunction range -> "asavya/apasavya"
    "asavya_apasavya": 8.0,
}


@dataclass
class GrahaYuddhaClass:
    body_a: str
    body_b: str
    separation_deg: float
    conjunction_class: str  # bheda / ullekha / amsumardana / asavya_apasavya / none
    note: str


def classify_grahayuddha(
    positions: Dict[str, float],
    thresholds: Optional[Dict[str, float]] = None,
) -> List[GrahaYuddhaClass]:
    thresholds = thresholds or GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG
    bodies = list(positions.keys())
    out: List[GrahaYuddhaClass] = []
    for i in range(len(bodies)):
        for j in range(i + 1, len(bodies)):
            a, b = bodies[i], bodies[j]
            sep = angular_separation(positions[a], positions[b])
            cls = "none"
            if sep <= thresholds["bheda"]:
                cls = "bheda"
            elif sep <= thresholds["ullekha"]:
                cls = "ullekha"
            elif sep <= thresholds["amsumardana"]:
                cls = "amsumardana"
            elif sep <= thresholds["asavya_apasavya"]:
                cls = "asavya_apasavya"
            if cls != "none":
                out.append(GrahaYuddhaClass(
                    body_a=a, body_b=b, separation_deg=sep,
                    conjunction_class=cls,
                    note="Thresholds are PLACEHOLDER, not textually sourced -- see module docstring.",
                ))
    return out


def detect_configuration(tradition: str, positions: Dict[str, float], **kwargs):
    """
    Tradition-gated dispatcher (validation requirement 10). Do NOT call detect_aspects()
    or classify_grahayuddha() directly from pipeline code -- go through this function so
    it is structurally impossible to accidentally apply Ptolemaic aspect rules to a
    Bṛhat Saṃhitā rule lookup, or vice versa.
    """
    tradition = tradition.lower()
    if tradition in ("ptolemy", "tetrabiblos", "hellenistic"):
        return detect_aspects(positions, **kwargs)
    if tradition in ("brihat_samhita", "jyotisha", "indian"):
        return classify_grahayuddha(positions, **kwargs)
    raise ValueError(
        f"Unknown tradition '{tradition}' -- no configuration-detection rule exists for "
        f"it. Refusing to guess which aspect/conjunction system to apply."
    )


def is_retrograde(lon_today_deg: float, lon_yesterday_deg: float) -> bool:
    """Crude retrograde test: apparent ecliptic longitude decreasing day-over-day
    (handles the 360/0 wrap). Needs two real position samples a day apart -- this
    function does no fetching itself."""
    diff = (lon_today_deg - lon_yesterday_deg + 540) % 360 - 180
    return diff < 0


# ---- Ch. XVIII lunar-pass (Moon north/south of a planet) --------------------------
# Added during the "VALIDATION HARDENING BEFORE BT-002" pass. This is a NEW, ADDITIVE
# capability -- nothing above this line was changed. Ch. XVIII (BS-18-*) rules key off
# whether the Moon passes NORTH or SOUTH of a planet at the moment of longitude
# conjunction. This requires ecliptic LATITUDE (not just longitude) for both bodies --
# a genuinely different physical quantity than the graha-yuddha proximity classes
# above, which only ever needed longitude separation. rule_matcher.py's
# match_lunar_pass_rules() previously raised NotImplementedError specifically because
# this latitude comparison was "not wired up" -- see that function's docstring, which
# is now implemented via classify_lunar_pass() below.
#
# THRESHOLD NOTE (read before using): the extracted Ch. XVIII text (Iyer 1884, Sl. 1-8)
# states the qualitative rule "Moon passes north or south of a planet" without giving a
# numeric longitude-conjunction orb (how close counts as "passing"), the same kind of
# gap that graha-yuddha (Ch. XVII, immediately prior chapter, same treatise) has for its
# proximity CLASSES. LUNAR_PASS_PLACEHOLDER_ORB_DEG below reuses the SAME numeric value
# (8.0 degrees) as graha-yuddha's widest class (GRAHAYUDDHA_PLACEHOLDER_THRESHOLDS_DEG
# ["asavya_apasavya"]) for methodological consistency within the same chapter family --
# it is NOT independently sourced, NOT tuned against any backtest result, and should be
# replaced the moment a textually-grounded orb is found for this specific chapter. This
# choice was made BEFORE looking at any BT-002 result (BT-002 has not been run).

LUNAR_PASS_PLACEHOLDER_ORB_DEG = 8.0  # PLACEHOLDER -- see note above. Mirrors the
                                        # existing graha-yuddha "asavya_apasavya" bound.


@dataclass
class LunarPassResult:
    planet: str
    moon_lon: float
    moon_lat: float
    planet_lon: float
    planet_lat: float
    longitude_separation_deg: float
    in_conjunction_range: bool
    side: str          # "north" | "south" | "not_in_range"
    orb_used_deg: float


def classify_lunar_pass(
    moon_lon: float, moon_lat: float, planet: str, planet_lon: float, planet_lat: float,
    orb_deg: Optional[float] = None,
) -> LunarPassResult:
    """
    Determines whether the Moon is currently 'passing' the given planet (longitude
    separation within orb_deg -- see THRESHOLD NOTE above) and, if so, whether the
    Moon is north or south of the planet (ecliptic latitude comparison, per Ch.
    XVIII's own textual criterion -- ayanamsa-independent, since a constant longitude
    shift does not affect latitude at all; see rule_registry.py's zodiac_requirement
    classification for Ch. XVIII).
    """
    orb = LUNAR_PASS_PLACEHOLDER_ORB_DEG if orb_deg is None else orb_deg
    sep = angular_separation(moon_lon, planet_lon)
    in_range = sep <= orb
    if not in_range:
        side = "not_in_range"
    elif moon_lat > planet_lat:
        side = "north"
    elif moon_lat < planet_lat:
        side = "south"
    else:
        side = "not_in_range"  # exactly equal latitude -- no meaningful N/S claim
    return LunarPassResult(
        planet=planet, moon_lon=moon_lon, moon_lat=moon_lat, planet_lon=planet_lon,
        planet_lat=planet_lat, longitude_separation_deg=sep, in_conjunction_range=in_range,
        side=side, orb_used_deg=orb,
    )


# ---- Ptolemy Book II Ch. III -- triplicity/quadrant lookup table ------------------
# PT-II-3-general is a LOOKUP TABLE referenced by PT-II-6-01 (eclipse locality), not an
# independently-triggerable rule -- it has no trigger CONDITION of its own (every
# zodiac sign belongs to exactly one triplicity/quadrant at all times, so asking
# whether it "fires" on a given date is not a meaningful question; see
# RULE_IMPLEMENTATION_AUDIT.md for the full reasoning). This function makes the table
# usable by PT-II-6-01's eclipse detector without duplicating the table data.

_TRIPLICITY_SIGNS = {
    "fire": ["Aries", "Leo", "Sagittarius"],
    "earth": ["Taurus", "Virgo", "Capricorn"],
    "air": ["Gemini", "Libra", "Aquarius"],
    "water": ["Cancer", "Scorpio", "Pisces"],
}
_TRIPLICITY_QUADRANT = {
    "fire": "NW=Europe", "water": "SE=southern Asia",
    "air": "NE=northern Asia", "earth": "SW=Africa/Libya",
}
_TROPICAL_SIGN_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]


def tropical_sign_for_longitude(tropical_lon_deg: float) -> str:
    idx = int(tropical_lon_deg % 360.0 // 30)
    return _TROPICAL_SIGN_ORDER[idx]


def triplicity_for_tropical_longitude(tropical_lon_deg: float) -> dict:
    """Returns {'sign', 'triplicity', 'quadrant'} per PT-II-3-general's own table
    (rule_registry.RULES rule_id='PT-II-3-general'). Pure data lookup, no invented
    mapping -- the quadrant strings are copied verbatim from that Rule's
    trigger_params."""
    sign = tropical_sign_for_longitude(tropical_lon_deg)
    for triplicity, signs in _TRIPLICITY_SIGNS.items():
        if sign in signs:
            return {"sign": sign, "triplicity": triplicity, "quadrant": _TRIPLICITY_QUADRANT[triplicity]}
    raise ValueError(f"sign {sign!r} not found in any triplicity table -- should be unreachable")


# ---- Ptolemy Book II Ch. VI -- eclipse detection -----------------------------------
# PT-II-6-01 requires "an actual eclipse" (per forecast.py's own prior comment: "eclipse
# -- requires confirming an actual eclipse, not attempted here"). This uses genuine,
# textbook eclipse-geometry criteria (NOT an unsourced interpretive placeholder like the
# graha-yuddha/lunar-pass orbs above): a solar eclipse requires the Sun and Moon to be
# in longitude conjunction AND the Moon's ecliptic latitude to be within the Moon's
# angular radius of the ecliptic plane at that separation (approximated here via a
# standard, citable eclipse-limit angle), at new moon; a lunar eclipse requires
# opposition and node proximity at full moon. This is standard positional astronomy
# (e.g. Meeus, "Astronomical Algorithms", ch. 54), not a project-specific
# interpretation, and is applied identically regardless of which rule it feeds.
#
# ECLIPSE_LATITUDE_LIMIT_DEG: the Moon's ecliptic latitude must be within roughly this
# angle of 0 deg at syzygy for an eclipse (of any magnitude, partial included) to be
# geometrically possible. 1.5 deg is a standard conservative solar-eclipse limit
# (Meeus ch.54 gives ~1.4-1.6 deg depending on the Moon's distance); we use the wider,
# more permissive bound so this never FALSELY rules out a real eclipse -- at the cost
# of occasionally flagging a "possible eclipse" that a fully rigorous Besselian-element
# calculation would rule out. This bound is a genuine astronomical fact (not tunable
# per-rule) and is used identically for every date.
ECLIPSE_LATITUDE_LIMIT_DEG = 1.6
ECLIPSE_LONGITUDE_SYZYGY_ORB_DEG = 1.0  # how close to exact conjunction/opposition (deg)


@dataclass
class EclipseCheckResult:
    kind: str          # "solar" | "lunar" | "none"
    sun_lon: float
    moon_lon: float
    moon_lat: float
    syzygy_separation_deg: float
    eclipse_ecliptic_lon_deg: Optional[float]


def check_for_eclipse(sun_lon: float, moon_lon: float, moon_lat: float) -> EclipseCheckResult:
    """sun_lon/moon_lon: tropical (or any single consistent frame -- eclipses are a
    frame-independent physical alignment) ecliptic longitudes. moon_lat: Moon's
    ecliptic latitude (same frame). Returns kind='solar' if Sun-Moon are in
    near-conjunction with the Moon close enough to the ecliptic (new moon, near a
    node); kind='lunar' if in near-opposition under the same latitude condition (full
    moon, near a node); kind='none' otherwise."""
    conj_sep = angular_separation(sun_lon, moon_lon)
    opp_sep = angular_separation((sun_lon + 180.0) % 360.0, moon_lon)

    if conj_sep <= ECLIPSE_LONGITUDE_SYZYGY_ORB_DEG and abs(moon_lat) <= ECLIPSE_LATITUDE_LIMIT_DEG:
        return EclipseCheckResult("solar", sun_lon, moon_lon, moon_lat, conj_sep, moon_lon)
    if opp_sep <= ECLIPSE_LONGITUDE_SYZYGY_ORB_DEG and abs(moon_lat) <= ECLIPSE_LATITUDE_LIMIT_DEG:
        return EclipseCheckResult("lunar", sun_lon, moon_lon, moon_lat, opp_sep, moon_lon)
    return EclipseCheckResult("none", sun_lon, moon_lon, moon_lat, min(conj_sep, opp_sep), None)
