"""
Astrowatch — historical event database data models.

Plain dataclasses mirroring historical_events_schema.sql exactly. No astrology
imports (see historical/__init__.py).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Source:
    source_id: str
    dataset_name: str
    organization: Optional[str]
    source_type: str
    tier: int
    url: Optional[str]
    access_date: Optional[str]
    coverage: Optional[str]
    notes: Optional[str] = None


@dataclass
class Event:
    event_id: str
    canonical_event_id: str
    event_name: str
    event_type: str
    event_subtype: str
    start_date: str
    date_confidence: str
    time_confidence: str
    location_confidence: str
    location_precision: str
    description: str
    source_quality_tier: int
    verification_status: str
    dataset_version: str
    created_at: str
    updated_at: str
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    timezone: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    verification_count: int = 0


@dataclass
class EventSource:
    event_id: str
    source_id: str
    link_verification_status: str
    created_at: str
    source_url: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ControlDate:
    control_id: str
    date: str
    sampling_method: str
    selection_timestamp: str
    source_window: str
    dataset_version: str
    region: Optional[str] = None
    seed: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class DatasetVersion:
    version_id: str
    created_date: str
    description: Optional[str] = None
    event_count: Optional[int] = None
    source_count: Optional[int] = None
    frozen: bool = False
    frozen_at: Optional[str] = None
    checksum_sha256: Optional[str] = None
    known_limitations: Optional[str] = None
    notes: Optional[str] = None
