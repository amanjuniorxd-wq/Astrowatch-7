"""
Astrowatch backtest — automated blindness check.

Same technique as historical/tests/test_astrological_independence.py's third test
(AST-based, not text-search-based, to avoid false positives on legitimate prose/
docstrings that MENTION a forbidden field name while explaining why it is absent).

Checks predictor.py's source for:
  1. No import of historical.models / historical.repository / historical.database
     (the predictor must never be able to open the historical DB or construct an
     Event instance itself).
  2. No reference (as a Name, Attribute, or string dict-key literal) to any of the
     forbidden field names below, anywhere in executable code (docstrings/comments
     are ignored by construction since ast.walk() does not descend into them as
     Name/Attribute/Str-literal-used-as-identifier nodes).
"""

import ast
import os
from typing import List, Tuple

FORBIDDEN_IMPORT_MODULES = {"historical.models", "historical.repository", "historical.database"}

FORBIDDEN_FIELD_NAMES = {
    "event_name", "event_type", "event_subtype", "description", "source_id",
    "source_quality_tier", "verification_status", "verification_count",
    "canonical_event_id", "actual_outcome", "actual_category", "actual_subtype",
    "actual_event_id", "actual_event_name", "dataset_name", "organization",
}


def _predictor_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "predictor.py")


def check_predictor_source(path: str = None) -> Tuple[bool, List[str]]:
    path = path or _predictor_path()
    with open(path) as f:
        source = f.read()
    tree = ast.parse(source, filename=path)

    violations: List[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_IMPORT_MODULES:
                    violations.append(f"line {node.lineno}: import of forbidden module {alias.name!r}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in FORBIDDEN_IMPORT_MODULES:
                violations.append(f"line {node.lineno}: import from forbidden module {mod!r}")
        elif isinstance(node, ast.Name):
            if node.id in FORBIDDEN_FIELD_NAMES:
                violations.append(f"line {node.lineno}: reference to forbidden identifier {node.id!r}")
        elif isinstance(node, ast.Attribute):
            if node.attr in FORBIDDEN_FIELD_NAMES:
                violations.append(f"line {node.lineno}: attribute access {node.attr!r}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # dict-key-style string literals used as subscripts, e.g. row["event_name"]
            if node.value in FORBIDDEN_FIELD_NAMES:
                violations.append(f"line {node.lineno}: string literal {node.value!r} matching a forbidden field name")

    return (len(violations) == 0), violations
