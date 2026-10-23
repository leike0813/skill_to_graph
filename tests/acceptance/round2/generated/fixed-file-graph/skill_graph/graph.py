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
    needs_input: bool
    rows: int
    total: int
    content: str
    approved: bool
    status: str
    path: str
    error: dict


def error(code: str, path, detail) -> dict:
    return {"status": "error",
            "error": {"code": code, "path": str(path) if path is not None else None,
                      "detail": str(detail)}}


def collect(state: State):
    missing = [key for key in ("source_csv", "output_dir")
               if not isinstance(state.get(key), str) or not state[key].strip()]
    if not missing:
        return {"needs_input": False}
    reply = interrupt({
        "question": "提供 source_csv 和 output_dir；缺失时不要猜路径。",
        "fields": missing,
    })
    received = ({key: reply[key] for key in missing
                 if isinstance(reply, dict) and isinstance(reply.get(key), str)
                 and reply[key].strip()}
                if isinstance(reply, dict) else {})
    return {**received, "needs_input": bool(set(missing) - set(received))}


def plan(state: State):
    source_csv = Path(state["source_csv"]).expanduser().resolve()
    try:
        proc = subprocess.run(
            [sys.executable, str(SOURCE / "scripts/render.py"), str(source_csv)],
            cwd=SOURCE, text=True, capture_output=True, check=False,
        )
        report = json.loads(proc.stdout)
    except (OSError, ValueError) as exc:
        return error("plan-error", source_csv, exc)
    if proc.returncode:
        detail = report.get("error") if isinstance(report, dict) else None
        if isinstance(detail, dict):
            return {"status": "error", "error": detail}
        return error("plan-error", source_csv, detail or proc.stderr.strip() or "render.py failed")
    try:
        return {"rows": report["rows"], "total": report["total"],
                "content": report["content"], "status": "planned"}
    except (KeyError, TypeError) as exc:
        return error("plan-error", source_csv, f"Invalid render plan: {exc}")


def confirm(state: State):
    target = Path(state["output_dir"]).expanduser().resolve() / "summary.txt"
    approved = interrupt({
        "question": "回复 true 批准写入，回复 false 放弃。",
        "rows": state["rows"],
        "total": state["total"],
        "path": str(target),
    }) is True
    return {"approved": approved,
            "status": "approved" if approved else "cancelled"}


def write(state: State):
    target = Path(state["output_dir"]).expanduser().resolve() / "summary.txt"
    if target.exists():
        return error("file-exists", target, "Refusing to overwrite an existing summary.txt")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as stream:
            stream.write(state["content"])
    except OSError as exc:
        return {**error("write-error", target, exc), "rows": state["rows"],
                "total": state["total"]}
    return {"status": "ok", "path": str(target)}


def make_graph(config=None, *, checkpointer=None, store=None):
    builder = StateGraph(State)
    builder.add_node("collect", collect)
    builder.add_node("plan", plan)
    builder.add_node("confirm", confirm)
    builder.add_node("write", write)
    builder.add_edge(START, "collect")
    builder.add_conditional_edges("collect",
                                  lambda state: "collect" if state["needs_input"] else "plan")
    builder.add_conditional_edges("plan",
                                  lambda state: "confirm" if state["status"] == "planned" else END)
    builder.add_conditional_edges("confirm",
                                  lambda state: "write" if state["approved"] else END)
    builder.add_edge("write", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def cli_graph(config):
    return make_graph(config)
