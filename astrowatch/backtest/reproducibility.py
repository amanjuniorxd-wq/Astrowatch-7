"""
Astrowatch backtest — rule-registry and astronomy-methodology version snapshots.

Neither function here changes rule behavior or astronomy behavior in any way -- both
only READ already-loaded module state / source files and hash it. This satisfies
spec item 22/23 ("If the existing registry does not have a version/hash mechanism,
implement one without changing rule behavior") without touching rule_registry.py,
ayanamsha.py, coordinates.py, panchang.py, rashi_nakshatra.py, aspects.py, or
forecast.py.
"""

import hashlib
import inspect
import json
import os
from dataclasses import asdict
from typing import Dict


def rule_registry_version_hash() -> Dict[str, str]:
    """Deterministic hash of every field of every Rule in rule_registry.RULES,
    in the module's own list order (not re-sorted, so an actual reordering would
    also change the hash -- reordering is itself a registry change worth catching).
    """
    import rule_registry
    payload = [asdict(r) for r in rule_registry.RULES]
    serialized = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return {
        "hash_sha256": digest,
        "rule_count": str(len(rule_registry.RULES)),
        "algorithm": "sha256(json.dumps([dataclasses.asdict(r) for r in RULES], sort_keys=True))",
    }


# Files that jointly define "astronomy methodology" for this project's purposes:
# ephemeris frame convention, Lahiri ayanamsha, Panchang, Rāśi/Nakshatra, and the
# forecast pipeline that wires them together. aspects.py (configuration/conjunction
# detection) and coordinates.py (Julian Day / frame math) are included too since a
# change to either would silently change results without touching rule_registry.py.
ASTRONOMY_METHODOLOGY_MODULES = [
    "coordinates.py", "ayanamsha.py", "panchang.py", "rashi_nakshatra.py",
    "aspects.py", "forecast.py",
]

# Added during the "VALIDATION HARDENING BEFORE BT-002" pass: rule_matcher.py is now
# a genuine part of the prediction pipeline (it previously wasn't wired into anything
# forecast.py's evaluate_rules() called, and its lunar-pass/eclipse functions were
# NotImplementedError stubs -- see RULE_IMPLEMENTATION_AUDIT.md). A SEPARATE constant
# (not a mutation of the list above) so BT-001's already-recorded astronomy_version
# hash value remains exactly what it always was (a frozen historical fact); this new
# list is what BT-002+ should hash going forward.
ASTRONOMY_METHODOLOGY_MODULES_V2 = ASTRONOMY_METHODOLOGY_MODULES + ["rule_matcher.py"]


def astronomy_version_hash(astrowatch_dir: str, modules=None) -> Dict[str, str]:
    """modules defaults to ASTRONOMY_METHODOLOGY_MODULES (BT-001's exact file set,
    for reproducing that hash). Pass ASTRONOMY_METHODOLOGY_MODULES_V2 for BT-002+."""
    file_list = modules if modules is not None else ASTRONOMY_METHODOLOGY_MODULES
    per_file = {}
    h = hashlib.sha256()
    for fname in file_list:
        path = os.path.join(astrowatch_dir, fname)
        with open(path, "rb") as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        per_file[fname] = file_hash
        h.update(fname.encode("utf-8"))
        h.update(file_hash.encode("utf-8"))
    return {
        "hash_sha256": h.hexdigest(),
        "per_file_sha256": per_file,
        "files_included": file_list,
    }


BACKTEST_PACKAGE_FILES = [
    "ephemeris_source.py", "predictor.py", "predictor_v2.py", "models.py",
    "sampler.py", "controls.py", "scorer.py", "baselines.py", "blindness.py",
    "engine.py", "repository.py", "database.py", "metrics.py", "category_map.py",
    "reproducibility.py",
]


def backtest_code_version_hash(backtest_dir: str) -> Dict[str, str]:
    """Hashes the backtest/ package's own .py files (Phase 17 reproducibility
    requirement: this package's own code is as much a determinant of the result as
    the astronomy/rule-registry files, and previously had no version snapshot at
    all)."""
    per_file = {}
    h = hashlib.sha256()
    for fname in sorted(BACKTEST_PACKAGE_FILES):
        path = os.path.join(backtest_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            content = f.read()
        file_hash = hashlib.sha256(content).hexdigest()
        per_file[fname] = file_hash
        h.update(fname.encode("utf-8"))
        h.update(file_hash.encode("utf-8"))
    return {"hash_sha256": h.hexdigest(), "per_file_sha256": per_file}


def configuration_hash(config: dict) -> str:
    serialized = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
