"""Reuse existing read-only artifact checks for this independent comparison."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
SOURCE = ROOT.parent / "generated/literature-analysis-graph/source/literature-analysis"


if __name__ == "__main__":
    path = REPO / "tests/acceptance/literature-analysis-attention/compare.py"
    spec = importlib.util.spec_from_file_location("literature_comparison", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.SOURCE = SOURCE
    report = {name: module.read_group(name) for name in ("graph-run", "control")}
    hashes = [report[name]["facts"].get("input_hash") for name in ("graph-run", "control")]
    report["same_input_hash"] = bool(hashes[0]) and hashes[0] == hashes[1]
    report["semantic_review"] = "Separate review in REPORT.md; schema checks do not judge meaning"
    with (ROOT / "comparison.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({name: report[name]["status"] for name in ("graph-run", "control")}, ensure_ascii=False))
