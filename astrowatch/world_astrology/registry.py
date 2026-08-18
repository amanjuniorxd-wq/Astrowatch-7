"""
Astrowatch World Astrology -- registry aggregator.

Single place that imports every tradition module and builds one populated
TraditionRegistry. Nothing else in this package should hand-assemble the list
of tradition modules -- import build_registry() instead, so adding a new
tradition module only ever requires one edit (the TRADITION_MODULES list below).
"""
from . import schema
from .traditions import (
    jyotisha, hellenistic, western, babylonian, persian_islamic,
    chinese, tibetan, egyptian, japanese, mesoamerican,
)

TRADITION_MODULES = [
    jyotisha, hellenistic, western, babylonian, persian_islamic,
    chinese, tibetan, egyptian, japanese, mesoamerican,
]


def build_registry() -> schema.TraditionRegistry:
    reg = schema.TraditionRegistry()
    for mod in TRADITION_MODULES:
        reg.register_all(mod.ENTRIES)
    return reg
