"""Resume the existing graph DB once and retain a separate attempt record."""
import json
from pathlib import Path
import shutil
import sqlite3
import time

import run

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    work = ROOT / "graph-run"
    db = work / ".literature_analysis_tmp/literature_analysis.db"
    assert db.is_file(), "The original runtime DB is required"
    evidence = ROOT / "resume-1"
    evidence.mkdir(exist_ok=False)
    snapshot = evidence / ".literature_analysis_tmp"
    snapshot.mkdir()
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as source:
        source.row_factory = sqlite3.Row
        state = dict(source.execute("SELECT * FROM workflow_state").fetchone())
        receipts = [dict(row) for row in source.execute("SELECT * FROM action_receipts")]
        inputs = dict(source.execute("SELECT key,value FROM runtime_inputs"))
        assert state["current_stage"] == "stage_3_digest", state
        assert inputs["model"] == "gpt-6.1-sol" and inputs["language"] == "zh-CN"
        with sqlite3.connect(snapshot / "before.db") as target:
            source.backup(target)
    for name in ("observed-final-response.txt", "graph-events.jsonl", "requests.jsonl"):
        path = work / name
        if path.exists():
            shutil.copy2(path, evidence / ("before-" + name))
    with (evidence / "before-state.json").open("x", encoding="utf-8") as stream:
        json.dump({"workflow_state": state, "receipts": receipts,
                   "runtime_inputs": {k: inputs.get(k) for k in ("model", "language", "input_hash")}},
                  stream, ensure_ascii=False, indent=2)
    started = time.time()
    with (evidence / "graph-result.json").open("x", encoding="utf-8") as stream:
        result = run.graph_run(work)
        record = {"entry": "graph-resume", "resumed_from_stage": state["current_stage"],
                  "working_dir": str(work), "input": run.PAYLOAD, "started_at_epoch": started,
                  "elapsed_seconds": time.time() - started, **result}
        json.dump(record, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"execution": record["execution"], "elapsed_seconds": record["elapsed_seconds"],
                      "error": record["result"].get("error")}, ensure_ascii=False), flush=True)
