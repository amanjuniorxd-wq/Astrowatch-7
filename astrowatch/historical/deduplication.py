"""
Astrowatch — duplicate-candidate detection for the historical event database.

This module NEVER auto-merges. It only flags candidate duplicates for a human
(via manual_review.csv) to resolve. No astrology involved.

Matching signals (expanded this pass per an explicit request to broaden detection
beyond name+date+country):
  - normalized event name (exact match)
  - fuzzy name overlap (token Jaccard similarity, catches "Fall of Saigon" vs
    "Saigon falls to North Vietnamese forces" style variants)
  - event type / subtype
  - date proximity (single dates) AND date-range overlap (for DATE_RANGE events)
  - country / region / location_name
  - source_record_id (if two records trace back to the same native ID in an
    upstream source -- e.g. the same USGS earthquake ID appearing via two adapters
    -- that is treated as HIGH confidence regardless of anything else)
  - description token overlap (weak signal on its own, used only to raise/lower
    confidence on a candidate already flagged by a stronger signal, never to flag
    on its own)
"""

import re
from dataclasses import dataclass
from datetime import date as _date
from typing import List, Optional, Sequence


_STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "at", "to", "and", "or", "for", "with",
    "begins", "begin", "ends", "end", "starts", "start", "declares", "declared",
}


def normalize_name(name: str) -> str:
    n = name.lower().strip()
    n = re.sub(r"[^a-z0-9\s]", "", n)
    n = re.sub(r"\s+", " ", n)
    return n


def _tokens(text: str) -> set:
    return {t for t in normalize_name(text).split() if t and t not in _STOPWORDS}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class DuplicateCandidate:
    event_id_a: str
    event_id_b: str
    reason: str
    confidence: str  # "LOW" | "MEDIUM" | "HIGH" -- human judgment call, never auto-merged
    signals: Optional[List[str]] = None


def _date_distance_days(d1: str, d2: str) -> Optional[int]:
    try:
        y1, m1, day1 = (int(x) for x in d1.split("-"))
        y2, m2, day2 = (int(x) for x in d2.split("-"))
        return abs((_date(y1, m1, day1) - _date(y2, m2, day2)).days)
    except (ValueError, AttributeError):
        return None


def _ranges_overlap(a_start, a_end, b_start, b_end) -> bool:
    a_end = a_end or a_start
    b_end = b_end or b_start
    try:
        return not (a_end < b_start or b_end < a_start)
    except TypeError:
        return False


def find_duplicate_candidates(events: Sequence[dict]) -> List[DuplicateCandidate]:
    """events: list of dicts with at least event_id, event_name, event_type,
    event_subtype, start_date, country_code; optionally end_date, region,
    location_name, description, source_record_id. O(n^2) -- fine at pilot scale."""
    candidates: List[DuplicateCandidate] = []
    n = len(events)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = events[i], events[j]
            signals: List[str] = []

            # HIGH-confidence short-circuit: identical native source record ID
            src_a, src_b = a.get("source_record_id"), b.get("source_record_id")
            if src_a and src_b and src_a == src_b:
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"identical upstream source_record_id ({src_a}) -- almost certainly the same "
                    f"underlying record ingested twice",
                    "HIGH", ["source_record_id"],
                ))
                continue

            if a["event_type"] != b["event_type"]:
                continue

            name_a, name_b = normalize_name(a["event_name"]), normalize_name(b["event_name"])
            tokens_a, tokens_b = _tokens(a["event_name"]), _tokens(b["event_name"])
            name_similarity = _jaccard(tokens_a, tokens_b)

            same_country = bool(a.get("country_code")) and a.get("country_code") == b.get("country_code")
            same_region = bool(a.get("region")) and a.get("region") == b.get("region")
            same_location = bool(a.get("location_name")) and a.get("location_name") == b.get("location_name")
            same_subtype = a.get("event_subtype") == b.get("event_subtype")

            days_apart = _date_distance_days(a["start_date"], b["start_date"])
            range_overlap = _ranges_overlap(
                a["start_date"], a.get("end_date"), b["start_date"], b.get("end_date"),
            )

            desc_overlap = 0.0
            if a.get("description") and b.get("description"):
                desc_overlap = _jaccard(_tokens(a["description"]), _tokens(b["description"]))

            if name_a == name_b:
                signals.append("identical_normalized_name")
            elif name_similarity >= 0.6:
                signals.append(f"fuzzy_name_similarity={name_similarity:.2f}")
            if same_country:
                signals.append("same_country")
            if same_region:
                signals.append("same_region")
            if same_location:
                signals.append("same_location_name")
            if same_subtype:
                signals.append("same_subtype")
            if days_apart is not None and days_apart <= 1:
                signals.append(f"dates_within_{days_apart}_day(s)")
            elif range_overlap:
                signals.append("date_ranges_overlap")
            if desc_overlap >= 0.3:
                signals.append(f"description_overlap={desc_overlap:.2f}")

            if "identical_normalized_name" in signals and (days_apart is not None and days_apart <= 3):
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"identical normalized name ('{name_a}'), {days_apart} day(s) apart",
                    "HIGH", signals,
                ))
            elif "identical_normalized_name" in signals:
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"identical normalized name ('{name_a}') but dates far apart -- verify same event",
                    "MEDIUM", signals,
                ))
            elif any(s.startswith("fuzzy_name_similarity") for s in signals) and (same_country or same_location) \
                    and (days_apart is not None and days_apart <= 3 or range_overlap):
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"similar name ('{a['event_name']}' vs '{b['event_name']}'), matching "
                    f"location/date signals",
                    "MEDIUM", signals,
                ))
            elif same_location and same_subtype and (days_apart is not None and days_apart <= 1):
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"same location+subtype+date (within {days_apart} day(s)), different name text "
                    f"('{a['event_name']}' vs '{b['event_name']}') -- verify not the same event",
                    "LOW", signals,
                ))
            elif same_country and same_subtype and (days_apart is not None and days_apart <= 1):
                candidates.append(DuplicateCandidate(
                    a["event_id"], b["event_id"],
                    f"same country+subtype+date (within {days_apart} day(s)), different name text "
                    f"('{a['event_name']}' vs '{b['event_name']}') -- verify not the same event",
                    "LOW", signals,
                ))
    return candidates
