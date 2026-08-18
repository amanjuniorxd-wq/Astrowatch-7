"""
Astrowatch — Panchang (partial)
================================
PARTIAL IMPLEMENTATION, HONESTLY SCOPED. The five traditional "limbs" (pañcāṅga) are
tithi, vara, nakshatra, yoga, karana. This module computes:

  - tithi   -- real, standard formula: floor((Moon_lon - Sun_lon mod 360) / 12) + 1,
               giving a lunar day 1-30. Ayanamsha cancels out (it's a difference of two
               longitudes in the SAME frame), so this does not depend on which Lahiri
               path is used -- tropical or sidereal longitudes give the identical tithi.
  - vara    -- weekday, trivial from the Julian Day (JD 0.5 = Monday, standard
               convention: (floor(JD + 1.5)) mod 7 -> 0=Sunday ... 6=Saturday).
  - nakshatra (of the Moon) -- delegates to rashi_nakshatra.nakshatra_for_longitude()
               on the Moon's SIDEREAL longitude (this one DOES depend on ayanamsha).

NOT IMPLEMENTED: yoga, karana. These require additional definitional research this
project has not done yet (yoga = sum of Sun+Moon sidereal longitudes binned into 27;
karana = half-tithi, 11 named units in a specific repeating pattern with named
exceptions) -- rather than guess at the exact traditional binning/naming convention,
this module explicitly returns None for both and callers must treat that as "not
available," not as "zero" or any other silent default.

STATUS: written this pass, NOT executed (same blocker as everything else -- see
VALIDATION_REPORT.md). Tithi/vara arithmetic hand-traced against the FINAL TASK example
in FORECAST_RUN_2026_09_USA.md.
"""

import math
from dataclasses import dataclass
from typing import Optional

import rashi_nakshatra as rn

TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima/Amavasya",
]  # 1-15 (Shukla/Krishna paksha share these names; 15th differs by paksha)

VARA_NAMES = ["Ravivara (Sun)", "Somavara (Moon)", "Mangalavara (Mars)",
              "Budhavara (Mercury)", "Guruvara (Jupiter)", "Shukravara (Venus)",
              "Shanivara (Saturn)"]


@dataclass
class PanchangPartial:
    tithi_number: int          # 1-30
    tithi_name: str
    paksha: str                 # "Shukla" (waxing, tithi 1-15) or "Krishna" (waning, 16-30)
    vara_index: int              # 0=Sunday ... 6=Saturday
    vara_name: str
    moon_nakshatra: rn.NakshatraPlacement
    yoga: Optional[str] = None    # NOT IMPLEMENTED
    karana: Optional[str] = None  # NOT IMPLEMENTED
    not_implemented: tuple = ("yoga", "karana")


def compute_tithi(sun_tropical_lon_deg: float, moon_tropical_lon_deg: float):
    diff = (moon_tropical_lon_deg - sun_tropical_lon_deg) % 360.0
    tithi_number = int(diff // 12.0) + 1  # 1-30
    tithi_number = min(tithi_number, 30)
    paksha = "Shukla" if tithi_number <= 15 else "Krishna"
    name_index = (tithi_number - 1) % 15
    tithi_name = TITHI_NAMES[name_index]
    return tithi_number, tithi_name, paksha


def compute_vara(jd_ut: float):
    # Standard convention: JD .5 (midnight) boundary; floor(JD+1.5) mod 7, 0=Sunday.
    vara_index = int(math.floor(jd_ut + 1.5)) % 7
    return vara_index, VARA_NAMES[vara_index]


def compute_partial_panchang(
    jd_ut: float, sun_tropical_lon_deg: float, moon_tropical_lon_deg: float,
    moon_sidereal_lon_deg: float,
) -> PanchangPartial:
    tithi_number, tithi_name, paksha = compute_tithi(sun_tropical_lon_deg, moon_tropical_lon_deg)
    vara_index, vara_name = compute_vara(jd_ut)
    moon_nakshatra = rn.nakshatra_for_longitude(moon_sidereal_lon_deg)
    return PanchangPartial(
        tithi_number=tithi_number, tithi_name=tithi_name, paksha=paksha,
        vara_index=vara_index, vara_name=vara_name, moon_nakshatra=moon_nakshatra,
    )
