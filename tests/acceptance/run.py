"""Explicit acceptance probes. Never run by unittest discovery; never starts a server."""
import argparse
from datetime import datetime, timezone
import importlib.util
import importlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib import error, request
import uuid

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "skill-to-graph/scripts/check_graph.py"


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        return jsonable(value.model_dump())
    if hasattr(value, "value"):
        return {"value": jsonable(value.value)}
    return str(value)


def static_probe(app):
    proc = subprocess.run([sys.executable, str(CHECKER), str(app)], text=True, capture_output=True)
    if proc.returncode:
        raise ValueError(proc.stdout or proc.stderr)
    return json.loads(proc.stdout)


def python_probe(app, graph_id, payload, resume, config, events, factory=None):
    graphs = json.loads((app / "langgraph.json").read_text())["graphs"]
    entry = graphs[graph_id]
    target, symbol = (entry["path"] if isinstance(entry, dict) else entry).rsplit(":", 1)
    symbol = factory or symbol
    sys.path.insert(0, str(app))
    if target.endswith(".py"):
        spec = importlib.util.spec_from_file_location("acceptance_graph_" + uuid.uuid4().hex, app / target)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(target)
    graph = getattr(module, symbol)
    if not hasattr(graph, "invoke"):
        kwargs = {}
        if "checkpointer" in inspect.signature(graph).parameters:
            from langgraph.checkpoint.memory import InMemorySaver
            kwargs["checkpointer"] = InMemorySaver()
        graph = graph(config, **kwargs)
    events.append({"stage": "load", "outcome": "loaded"})
    result = graph.invoke(payload, config)
    events.append({"stage": "call", "outcome": "executed", "result": jsonable(result)})
    if resume is not None:
        from langgraph.types import Command
        result = graph.invoke(Command(resume=resume), config)
        events.append({"stage": "resume", "outcome": "executed", "result": jsonable(result)})


def cli_probe(url, graph_id, payload, resume, config, events):
    def post(path, value):
        req = request.Request(url.rstrip("/") + path, data=json.dumps(value).encode(),
                              headers={"Content-Type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=120) as response:
            return json.loads(response.read())
    thread = post("/threads", {})["thread_id"]
    result = post(f"/threads/{thread}/runs/wait", {"assistant_id": graph_id, "input": payload, "config": config})
    events.append({"stage": "call", "outcome": "executed", "thread_id": thread, "result": result})
    if resume is not None:
        result = post(f"/threads/{thread}/runs/wait", {"assistant_id": graph_id,
                      "command": {"resume": resume}, "config": config})
        events.append({"stage": "resume", "outcome": "executed", "result": result})


def record_run(args):
    app = args.directory.resolve()
    events = []
    record = {"schema": 1, "time": datetime.now(timezone.utc).isoformat(),
              "application": str(app), "entry": args.mode, "graph_id": args.graph_id,
              "evidence_kind": args.evidence_kind, "relocated": args.relocate,
              "python_factory": getattr(args, "python_factory", None),
              "config_file": str(args.config) if getattr(args, "config", None) else None,
              "outcome": "not-run", "judgement": "pending-review", "events": events,
              "uncovered": ["Business semantics require comparison with the source contract"]}
    def probe(directory):
        events.append({"stage": "static", "outcome": "passed", "result": static_probe(directory)})
        if args.mode == "static":
            return
        if not args.input:
            raise ValueError("Runtime probes require --input")
        payload = json.loads(args.input.read_text())
        resume = json.loads(args.resume.read_text()) if args.resume else None
        config = {"configurable": {"thread_id": uuid.uuid4().hex}}
        if getattr(args, "config", None):
            supplied = json.loads(args.config.read_text())
            config.update(supplied)
        if args.mode == "python":
            python_probe(directory, args.graph_id, payload, resume, config, events, getattr(args, "python_factory", None))
        else:
            if not args.server:
                raise ConnectionError("CLI probe requires an already configured --server")
            cli_probe(args.server, args.graph_id, payload, resume, config, events)
    try:
        if args.relocate:
            if args.mode == "cli":
                raise ValueError("CLI relocation requires a server configured from the moved application; use a separate CLI probe")
            with tempfile.TemporaryDirectory(prefix="skill-graph-moved-") as temp:
                moved = Path(temp) / "application"
                shutil.copytree(app, moved)
                probe(moved)
        else:
            probe(app)
        record["outcome"] = "static-passed" if args.mode == "static" else "executed"
    except (ImportError, ConnectionError, error.URLError) as exc:
        record["outcome"] = "blocked"
        record["issue"] = {"type": type(exc).__name__, "detail": str(exc)}
    except Exception as exc:
        record["outcome"] = "failed"
        record["issue"] = {"type": type(exc).__name__, "detail": str(exc)}
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--mode", choices=["static", "python", "cli"], default="static")
    parser.add_argument("--graph-id", required=True)
    parser.add_argument("--input", type=Path, help="JSON source input; use synthetic nonsecret data")
    parser.add_argument("--config", type=Path, help="JSON runtime config, e.g. task workdir; no credentials")
    parser.add_argument("--python-factory", help="Python entry symbol in the configured module, if different from the CLI entry")
    parser.add_argument("--resume", type=Path, help="JSON reply; resumes the same graph/thread")
    parser.add_argument("--server", help="Existing local Agent Server URL; does not start it")
    parser.add_argument("--relocate", action="store_true")
    parser.add_argument("--evidence-kind", choices=["static", "runtime", "double", "live-model"], default="runtime")
    parser.add_argument("--record", required=True, type=Path, help="New record file; refuses to overwrite")
    args = parser.parse_args()
    # Reserve the record before invoking code so a conflicting path has no runtime side effects.
    with args.record.open("x", encoding="utf-8") as stream:
        record = record_run(args)
        json.dump(record, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"record": str(args.record), "outcome": record["outcome"]}))
    return 0 if record["outcome"] in {"static-passed", "executed"} else 1


if __name__ == "__main__":
    sys.exit(main())
