"""
Astrowatch World Astrology -- multi-tradition chart visuals.

Renders one SVG "panel" per tradition for a given ChartBundle (from
reading_engine.build_chart_bundle), meant to be paged through one at a time in
a gallery UI (see gallery.py). Two fundamentally different kinds of panel:

1. COMPUTED WHEEL CHARTS -- real, drawn from real computed longitudes. Only
   exist for the 3 traditions this project can actually place planets for:
   Jyotisha (sidereal), Western (tropical), Hellenistic (sidereal + sect/
   dignity annotations, reusing the same underlying sign data as Jyotisha per
   dignity_tables.py's documented convention). All three share one drawing
   routine (`_wheel_svg`) with a fixed convention -- Ascendant at 9 o'clock,
   signs proceeding counter-clockwise -- specifically so the three wheels are
   visually comparable side by side in the gallery, not just individually
   correct.

2. REFERENCE CARDS -- for the other 7 catalogued traditions (Chinese gets a
   small info card since it has real, computed, but non-chart data; Babylonian/
   Persian-Islamic/Tibetan/Egyptian/Japanese/Mesoamerican get knowledge cards
   pulling straight from their KnowledgeEntry records). These are NOT charts --
   no planetary placement is computed or implied for them, and each card says
   so explicitly. Presenting a numerology-flavored "chart-looking" graphic for
   a tradition this project cannot actually compute would misrepresent what
   the system knows; the honest design choice is a visibly different panel
   type instead.
"""
import math
from dataclasses import dataclass
from typing import List, Optional

from .schema import TraditionRegistry
from . import dignity_tables as dt
from .traditions import chinese as chinese_mod
from .reading_engine import western_tropical_sign

GRAHA_ABBREV = {
    "sun": "Su", "moon": "Mo", "mars": "Ma", "mercury": "Me", "jupiter": "Ju",
    "venus": "Ve", "saturn": "Sa", "rahu": "Ra", "ketu": "Ke",
}
GRAHA_ORDER = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"]

RASHI_NAMES_ORDER = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
                      "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena"]
WESTERN_SIGNS_ORDER = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                        "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

_CX, _CY, _R_OUTER, _R_INNER, _R_LABEL, _R_PLANET = 260, 260, 230, 150, 190, 170


def _deg_to_xy(lon_deg: float, ascendant_deg: float, radius: float):
    """Ascendant placed at 180 degrees (9 o'clock, screen-left), signs increase
    counter-clockwise on screen (matching the standard Western wheel-chart
    convention) -- shared by every wheel this module draws, computed vs
    reference alike, so panels are visually comparable."""
    angle = math.radians(180.0 - (lon_deg - ascendant_deg))
    x = _CX + radius * math.cos(angle)
    y = _CY - radius * math.sin(angle)
    return x, y


def _wheel_svg(title: str, subtitle: str, sign_names: List[str], ascendant_deg: float,
                placements: List[tuple], annotations: Optional[dict] = None,
                footer_lines: Optional[List[str]] = None) -> str:
    """placements: list of (abbrev, longitude_deg, extra_label_or_None).
    annotations: optional {abbrev: short_badge_string} drawn under the glyph."""
    annotations = annotations or {}
    footer_lines = footer_lines or []
    parts = [
        f'<svg viewBox="0 0 520 {560 + 18*len(footer_lines)}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Georgia, serif">',
        f'<rect x="0" y="0" width="520" height="{560 + 18*len(footer_lines)}" fill="#fdfcf7"/>',
        f'<text x="260" y="30" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{title}</text>',
        f'<text x="260" y="50" text-anchor="middle" font-size="12" fill="#666">{subtitle}</text>',
        f'<circle cx="{_CX}" cy="{_CY}" r="{_R_OUTER}" fill="none" stroke="#333" stroke-width="2"/>',
        f'<circle cx="{_CX}" cy="{_CY}" r="{_R_INNER}" fill="none" stroke="#999" stroke-width="1"/>',
    ]
    for i in range(12):
        sign_start_deg = i * 30.0
        x1, y1 = _deg_to_xy(sign_start_deg, ascendant_deg, _R_OUTER)
        x2, y2 = _deg_to_xy(sign_start_deg, ascendant_deg, _R_INNER)
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#bbb" stroke-width="1"/>')
        lx, ly = _deg_to_xy(sign_start_deg + 15.0, ascendant_deg, _R_LABEL)
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" font-size="11" fill="#555">{sign_names[i]}</text>')
    asc_x1, asc_y1 = _deg_to_xy(ascendant_deg, ascendant_deg, _R_OUTER + 12)
    asc_x2, asc_y2 = _deg_to_xy(ascendant_deg, ascendant_deg, _R_INNER)
    parts.append(f'<line x1="{asc_x1:.1f}" y1="{asc_y1:.1f}" x2="{asc_x2:.1f}" y2="{asc_y2:.1f}" stroke="#a33" stroke-width="2"/>')
    parts.append(f'<text x="{asc_x1:.1f}" y="{asc_y1-4:.1f}" text-anchor="middle" font-size="10" fill="#a33">ASC</text>')

    slot_used = {}
    for abbrev, lon, extra in placements:
        base_r = _R_PLANET
        key = int(lon // 6)
        slot_used[key] = slot_used.get(key, 0) + 1
        r = base_r - (slot_used[key] - 1) * 16
        px, py = _deg_to_xy(lon, ascendant_deg, r)
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="13" fill="#fff" stroke="#333" stroke-width="1"/>')
        parts.append(f'<text x="{px:.1f}" y="{py+4:.1f}" text-anchor="middle" font-size="12" font-weight="bold" fill="#222">{abbrev}</text>')
        badge = annotations.get(abbrev)
        if badge:
            parts.append(f'<text x="{px:.1f}" y="{py+22:.1f}" text-anchor="middle" font-size="8" fill="#a33">{badge}</text>')

    y = 540
    for line in footer_lines:
        parts.append(f'<text x="20" y="{y}" font-size="11" fill="#444">{line}</text>')
        y += 18
    parts.append("</svg>")
    return "\n".join(parts)


def render_jyotisha_wheel(bundle) -> str:
    chart = bundle.entity.chart
    asc_deg = chart.ascendant_sidereal_deg
    placements = [(GRAHA_ABBREV[g], chart.grahas[g].sidereal_lon_deg, None) for g in GRAHA_ORDER]
    footer = [
        f"Ascendant: {chart.ascendant_rashi.rashi_name} ({chart.ascendant_rashi.rashi_index+1}/12)",
        f"Moon: {chart.grahas['moon'].rashi.rashi_name}, {chart.grahas['moon'].nakshatra.nakshatra_name} Nakshatra",
        f"Ayanamsha: {chart.ayanamsha_source} ({chart.ayanamsha_deg:.2f} deg)",
        "Computed: kundli.compute_kundli() (Swiss Ephemeris, file-based, sidereal Lahiri)",
    ]
    return _wheel_svg("Jyotisha (Vedic) Chart", "Sidereal zodiac, whole-sign houses",
                       RASHI_NAMES_ORDER, asc_deg, placements, footer_lines=footer)


def render_western_wheel(bundle) -> str:
    chart = bundle.entity.chart
    asc_tropical = chart.ascendant_tropical_deg
    placements = [(GRAHA_ABBREV[g], chart.grahas[g].tropical_lon_deg, None)
                  for g in GRAHA_ORDER if g not in ("rahu", "ketu")]
    footer = [
        f"Tropical Ascendant sign: {western_tropical_sign(asc_tropical)}",
        "Sign placement only -- no quadrant house system computed (see western.py limitations).",
        "Rahu/Ketu, aspects, and outer planets (Uranus/Neptune/Pluto) not shown -- not computed.",
        "Computed: kundli.compute_kundli() tropical longitudes (same ephemeris pass as Jyotisha).",
    ]
    return _wheel_svg("Western Chart (Tropical)", "Tropical zodiac, sign placement only",
                       WESTERN_SIGNS_ORDER, asc_tropical, placements, footer_lines=footer)


def render_hellenistic_wheel(bundle) -> str:
    chart = bundle.entity.chart
    asc_deg = chart.ascendant_sidereal_deg
    is_day = bundle.is_day_chart
    placements = [(GRAHA_ABBREV[g], chart.grahas[g].sidereal_lon_deg, None)
                  for g in GRAHA_ORDER if g not in ("rahu", "ketu")]
    annotations = {}
    for g in GRAHA_ORDER:
        if g in ("rahu", "ketu"):
            continue
        rashi_name = chart.grahas[g].rashi.rashi_name
        d = dt.dignity_of(g, rashi_name)
        of_sect = dt.hellenistic_sect_favor(is_day, g)
        badge = {"EXALTED": "Exalt", "OWN_SIGN": "Domic", "DEBILITATED": "Fall", "NEUTRAL": ""}[d]
        if of_sect is True:
            badge = (badge + " +sect").strip()
        elif of_sect is False:
            badge = (badge + " -sect").strip()
        annotations[GRAHA_ABBREV[g]] = badge
    footer = [
        f"Chart sect: {'DAY' if is_day else 'NIGHT'} (Sun in house {chart.grahas['sun'].house})",
        "Dignity shown: domicile/exaltation/fall only -- triplicity/term/face not computed.",
        "Sign data is the SAME sidereal placements as the Jyotisha wheel (see dignity_tables.py);",
        "the Hellenistic layer here is the interpretive one (sect + dignity), not new astronomy.",
    ]
    return _wheel_svg("Hellenistic Chart", "Sect + essential dignity (domicile/exaltation/fall)",
                       RASHI_NAMES_ORDER, asc_deg, placements, annotations=annotations, footer_lines=footer)


def render_chinese_card(bundle) -> str:
    stem, branch, animal = bundle.chinese_birth_year
    entity = bundle.entity
    lines = [
        f'<svg viewBox="0 0 520 320" xmlns="http://www.w3.org/2000/svg" font-family="Georgia, serif">',
        '<rect x="0" y="0" width="520" height="320" fill="#fdf6ea"/>',
        '<text x="260" y="34" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">Chinese Astrology</text>',
        '<text x="260" y="54" text-anchor="middle" font-size="12" fill="#666">Sexagenary (Stems-and-Branches) year cycle -- reference card, not a chart</text>',
        f'<rect x="60" y="90" width="400" height="130" rx="10" fill="#fff" stroke="#c9a227" stroke-width="2"/>',
        f'<text x="260" y="140" text-anchor="middle" font-size="26" font-weight="bold" fill="#c9a227">{stem}-{branch}</text>',
        f'<text x="260" y="175" text-anchor="middle" font-size="20" fill="#333">Year of the {animal}</text>',
        f'<text x="260" y="200" text-anchor="middle" font-size="12" fill="#777">Birth/inception year: {entity.inception_date[:4]}</text>',
        '<text x="30" y="250" font-size="11" fill="#444">Computed: sexagenary_year_index(), a Jan-1-anchored approximation of the</text>',
        '<text x="30" y="266" font-size="11" fill="#444">true lunisolar new year boundary -- see chinese.py docstring.</text>',
        '<text x="30" y="290" font-size="11" fill="#444">BaZi (4 Pillars), Zi Wei Dou Shu, and Qi Men Dun Jia are catalogued in this</text>',
        '<text x="30" y="306" font-size="11" fill="#444">system but NOT computed -- no full Chinese natal chart is produced here.</text>',
        '</svg>',
    ]
    return "\n".join(lines)


def render_reference_card(registry: TraditionRegistry, tradition: str, display_name: str) -> str:
    """The honest non-chart panel for the 6 seed-level traditions. Pulls real
    KnowledgeEntry content (technique names + one-line definitions) straight
    from the registry -- nothing here is invented for display purposes."""
    entries = registry.by_tradition(tradition)
    lines = [
        f'<svg viewBox="0 0 520 {160 + 46*min(len(entries),6)}" xmlns="http://www.w3.org/2000/svg" font-family="Georgia, serif">',
        f'<rect x="0" y="0" width="520" height="{160 + 46*min(len(entries),6)}" fill="#f2f0ec"/>',
        f'<text x="260" y="34" text-anchor="middle" font-size="20" font-weight="bold" fill="#222">{display_name}</text>',
        '<text x="260" y="54" text-anchor="middle" font-size="12" fill="#a33">Reference card -- NO chart computed for this tradition</text>',
        '<text x="260" y="70" text-anchor="middle" font-size="10" fill="#777">'
        'This project has no calculation engine for this tradition (see world_astrology docs).</text>',
    ]
    y = 100
    for e in entries[:6]:
        conf = e.confidence_level.value.replace("_", " ")
        definition = e.definition if len(e.definition) < 120 else e.definition[:117] + "..."
        lines.append(f'<text x="20" y="{y}" font-size="12" font-weight="bold" fill="#333">{e.technique}</text>')
        lines.append(f'<text x="20" y="{y+16}" font-size="10" fill="#666">[{conf}]</text>')
        lines.append(f'<text x="20" y="{y+32}" font-size="10" fill="#444">{definition}</text>')
        y += 46
    lines.append("</svg>")
    return "\n".join(lines)


REFERENCE_TRADITIONS = [
    ("babylonian", "Babylonian / Mesopotamian Astrology"),
    ("persian_islamic", "Persian / Islamic Astrology"),
    ("tibetan", "Tibetan Astrology"),
    ("egyptian", "Egyptian Astrology"),
    ("japanese", "Japanese Astrology (Onmyodo)"),
    ("mesoamerican", "Mayan / Mesoamerican Astrology"),
]


@dataclass
class ChartPanel:
    tradition_key: str
    display_name: str
    is_computed_chart: bool
    svg: str


def build_gallery_panels(bundle, registry: TraditionRegistry) -> List[ChartPanel]:
    """The full ordered set of panels for one entity's multi-tradition gallery
    -- 3 real computed wheels, 1 computed-but-non-chart card, 6 honest
    reference cards. Order: computed traditions first (most information-dense),
    reference traditions after."""
    panels = [
        ChartPanel("jyotisha", "Jyotisha (Vedic)", True, render_jyotisha_wheel(bundle)),
        ChartPanel("hellenistic", "Hellenistic", True, render_hellenistic_wheel(bundle)),
        ChartPanel("western", "Western (Tropical)", True, render_western_wheel(bundle)),
        ChartPanel("chinese", "Chinese", True, render_chinese_card(bundle)),
    ]
    for key, display in REFERENCE_TRADITIONS:
        panels.append(ChartPanel(key, display, False, render_reference_card(registry, key, display)))
    return panels
