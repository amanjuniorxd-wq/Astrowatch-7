"""
Astrowatch — guards the architectural boundary described in historical/__init__.py.

If this test ever fails, something in historical/ has started depending on
Astrowatch's astrology code, or vice versa -- exactly the coupling the spec
(items 26, and the historical-event-selection rules) prohibits.
"""
import ast
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORICAL_DIR = os.path.join(REPO_ROOT, "historical")

ASTROLOGY_MODULES = {
    "ayanamsha", "panchang", "rashi_nakshatra", "rule_registry", "aspects",
    "engines", "forecast", "rule_matcher", "coordinates", "ephemeris_client",
    "evaluate_forecasts",
}

ASTROLOGY_FILES = {m + ".py" for m in ASTROLOGY_MODULES}


def _imported_module_names(py_path: str):
    with open(py_path) as f:
        tree = ast.parse(f.read(), filename=py_path)
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


class AstrologicalIndependenceTests(unittest.TestCase):

    def test_no_historical_module_imports_astrology_code(self):
        offenders = []
        for root, _dirs, files in os.walk(HISTORICAL_DIR):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                path = os.path.join(root, fname)
                imported = _imported_module_names(path)
                bad = imported & ASTROLOGY_MODULES
                if bad:
                    offenders.append((path, bad))
        self.assertEqual(offenders, [], f"historical/ modules importing astrology code: {offenders}")

    def test_no_astrology_module_imports_historical_package(self):
        offenders = []
        for fname in ASTROLOGY_FILES:
            path = os.path.join(REPO_ROOT, fname)
            if not os.path.exists(path):
                continue
            imported = _imported_module_names(path)
            if "historical" in imported or "data" in imported:
                offenders.append(path)
        self.assertEqual(offenders, [], f"astrology modules importing historical/: {offenders}")

    def test_no_historical_module_has_executable_astrology_references(self):
        # Belt-and-suspenders check: even without a top-level import, code could
        # reference an astrology identifier (e.g. via a local import inside a
        # function, or a dynamically-resolved name). This walks the AST for actual
        # Name/Attribute/Call/Import references to the prohibited terms -- but
        # deliberately does NOT scan docstrings or comments, since historical/__init__.py
        # legitimately DISCUSSES these terms in prose to document the boundary itself
        # (a naive text search flagged that prose as a violation on first run of this
        # test -- a real false positive, fixed here by switching to AST-based
        # identifier matching instead of raw text search).
        prohibited_terms = {
            "grahayuddha", "ayanamsha", "nakshatra", "rashi", "panchang",
            "tithi", "graha", "sidereal_unresolved",
        }
        hits = []
        for root, _dirs, files in os.walk(HISTORICAL_DIR):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(root, fname)
                with open(fpath) as f:
                    tree = ast.parse(f.read(), filename=fpath)
                for node in ast.walk(tree):
                    name = None
                    if isinstance(node, ast.Name):
                        name = node.id
                    elif isinstance(node, ast.Attribute):
                        name = node.attr
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            if alias.name.lower() in prohibited_terms:
                                hits.append((fpath, alias.name))
                        continue
                    if name and name.lower() in prohibited_terms:
                        hits.append((fpath, name))
        self.assertEqual(hits, [], f"astrology-specific identifiers referenced in historical/ code: {hits}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
