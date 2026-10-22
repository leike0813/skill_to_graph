import json
from pathlib import Path
import subprocess
import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

SOURCE = Path(__file__).resolve().parents[1] / "source/fixed-file"


class State(TypedDict, total=False):
    source_csv: str
    output_dir: str
    rows: int
    total: int
    content: str
    status: str
    approved: bool
    path: str
    error: dict


def failed(code, detail):
    return {"status": "error", "error": {"code": code, "path": None, "detail": detail}}


def gather(state):
    missing = [key for key in ("source_csv", "output_dir") if not state.get(key)]
    if missing:
        reply = interrupt({"question": "Provide the missing input paths", "fields": missing})
        return {key: reply[key] for key in missing}
    return {}


def plan(state):
    try:
        proc = subprocess.run([sys.executable, str(SOURCE / "scripts/render.py"),
                               str(Path(state["source_csv"]).resolve())],
                              cwd=SOURCE, text=True, capture_output=True, check=False)
        result = json.loads(proc.stdout)
        if proc.returncode:
            return {"status": "error", "error": result.get("error", {"code": "source-script", "detail": result})}
        return {"rows": result["rows"], "total": result["total"],
                "content": result["content"], "status": "planned"}
    except (OSError, ValueError, KeyError) as exc:
        return failed("plan", str(exc))


def confirm(state):
    approved = interrupt({"question": "Write summary.txt?", "rows": state["rows"],
                          "total": state["total"], "content": state["content"],
                          "path": str(Path(state["output_dir"]) / "summary.txt")}) is True
    return {"approved": approved, "status": "approved" if approved else "cancelled"}


def write(state):
    try:
        folder = Path(state["output_dir"])
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "summary.txt"
        with path.open("x", encoding="utf-8") as stream:
            stream.write(state["content"])
        return {"status": "ok", "path": str(path)}
    except (OSError, KeyError) as exc:
        result = failed("write", str(exc))
        result["error"]["path"] = str(Path(state["output_dir"]) / "summary.txt")
        return result


def make_graph(config=None, *, checkpointer=None, store=None):
    builder = StateGraph(State)
    builder.add_node("gather", gather)
    builder.add_node("plan", plan)
    builder.add_node("confirm", confirm)
    builder.add_node("write", write)
    builder.add_edge(START, "gather")
    builder.add_edge("gather", "plan")
    builder.add_conditional_edges("plan", lambda s: "confirm" if s["status"] == "planned" else END)
    builder.add_conditional_edges("confirm", lambda s: "write" if s["approved"] else END)
    builder.add_edge("write", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def cli_graph(config):
    return make_graph(config)
