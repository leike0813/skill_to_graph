"""Round-two probes for the three regenerated small-sample graphs.

Reuses the first-round scenario drivers by importing them and overriding their app
bindings. First-round result files are never written; every record lands in round2/results.
No model call is made unless --live is passed explicitly.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ACCEPTANCE = Path(__file__).resolve().parent.parent
ROUND2 = Path(__file__).resolve().parent
GENERATED = ROUND2 / "generated"
RESULTS = ROUND2 / "results"
FIXTURES = ACCEPTANCE.parent / "fixtures/skills"
CHECKER = ACCEPTANCE.parent.parent / "skill-to-graph/scripts/check_graph.py"

sys.path.insert(0, str(ACCEPTANCE))

import fixed_scenarios  # noqa: E402
import live_scenarios  # noqa: E402
import mixed_boundaries  # noqa: E402

DOUBLE_ENV = {"MODEL_ID": "double", "MODEL_PROVIDER": "double", "MODEL_BASE_URL": "unused",
              "MODEL_API_KEY_ENV": "DOUBLE_KEY", "DOUBLE_KEY": "synthetic-not-a-key"}

def load_module(app: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, app / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def app_for(name: str) -> Path:
    return GENERATED / (name + "-graph")


def round2_load(name: str):
    app = app_for(name)
    return app, load_module(app, "round2_" + name.replace("-", "_"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_report(name: str):
    app = app_for(name)
    snapshot = app / "source" / name
    original = FIXTURES / name
    missing, differing, copied = [], [], []
    for path in sorted(original.rglob("*")):
        if path.is_dir():
            continue
        relative = path.relative_to(original)
        target = snapshot / relative
        if not target.is_file():
            missing.append(relative.as_posix())
        elif digest(path) != digest(target):
            differing.append(relative.as_posix())
    for path in sorted(snapshot.rglob("*")):
        if path.is_file():
            copied.append(path.relative_to(snapshot).as_posix())
    return {"snapshot": str(snapshot), "files": copied, "missing": missing,
            "content_differing": differing,
            "matches_source": not missing and not differing}


def static_report(app: Path):
    proc = subprocess.run([sys.executable, str(CHECKER), str(app)],
                          text=True, capture_output=True)
    payload = json.loads(proc.stdout)
    return {"exit_code": proc.returncode, "ok": payload["ok"],
            "checked_files": payload["data"]["checked_files"],
            "graph_entries": payload["data"]["graph_entries"],
            "unresolved_entries": payload["data"]["unresolved_entries"]}


def entry_report(name: str):
    app = app_for(name)
    config = json.loads((app / "langgraph.json").read_text(encoding="utf-8"))
    module = load_module(app, "round2_entry_" + name.replace("-", "_"))
    entries = {}
    for graph_id, value in config["graphs"].items():
        symbol = value.rsplit(":", 1)[1]
        entries[graph_id] = {"entry": value, "callable": callable(getattr(module, symbol, None))}
    return entries


def fixed_report():
    return fixed_scenarios.scenarios(app_for("fixed-file"))


def mixed_boundaries_report():
    original = mixed_boundaries.load
    mixed_boundaries.load = round2_load
    try:
        with patch.dict(os.environ, DOUBLE_ENV):
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                mixed_boundaries.main()
        return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]
    finally:
        mixed_boundaries.load = original


def missing_input_report():
    """Source requires asking for absent paths instead of guessing them."""
    module = load_module(app_for("fixed-file"), "round2_missing_fixed")
    from langgraph.checkpoint.memory import InMemorySaver
    graph = module.make_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "missing-input"}}
    pending = graph.invoke({"source_csv": "/tmp/does-not-matter.csv"}, config)
    assert "__interrupt__" in pending, pending
    interrupt_value = pending["__interrupt__"][0]
    interrupt_value = getattr(interrupt_value, "value", interrupt_value)
    asked = interrupt_value["fields"]
    assert asked == ["output_dir"], asked
    return {"scenario": "missing-output-dir-asks", "asked_fields": asked,
            "wrote_file": False}


def cancelled_report():
    """Cancellation returns no path and creates no output directory."""
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    import tempfile
    module = load_module(app_for("fixed-file"), "round2_cancel_fixed")
    with tempfile.TemporaryDirectory(prefix="round2-cancel-") as temp:
        out = Path(temp) / "cancelled"
        graph = module.make_graph(checkpointer=InMemorySaver())
        config = {"configurable": {"thread_id": "cancel"}}
        graph.invoke({"source_csv": str(app_for("fixed-file") /
                                        "source/fixed-file/data/example.csv"),
                      "output_dir": str(out)}, config)
        final = graph.invoke(Command(resume=False), config)
        assert final["status"] == "cancelled", final
        assert "path" not in final, final
        assert not out.exists(), out
    return {"scenario": "refusal-has-no-path", "status": final["status"],
            "path_absent": True, "output_dir_created": False}


def live_report():
    live_scenarios.configure()
    options = json.loads(os.environ["MODEL_OPTIONS"])
    options["reasoning_effort"] = "high"
    os.environ["MODEL_OPTIONS"] = json.dumps(options)
    original_load = live_scenarios.load
    live_scenarios.load = round2_load
    try:
        return live_scenarios.mixed_cases(), live_scenarios.wait_what_case()
    finally:
        live_scenarios.load = original_load


def wait_path_report():
    """Relative glossary paths sit under workdir; absolute GLOSSARY-MAP targets stay absolute."""
    import tempfile
    module = load_module(app_for("wait-what"), "round2_wait_paths")
    with tempfile.TemporaryDirectory(prefix="round2-paths-") as temp:
        workdir = Path(temp) / "task"
        outside = Path(temp) / "shared/GLOSSARY.md"

        class Runtime:
            config = {"configurable": {"workdir": str(workdir)}}

        relative = module.task_path(Runtime(), "GLOSSARY.md")
        absolute = module.task_path(Runtime(), str(outside))
        assert relative == (workdir / "GLOSSARY.md").resolve(), relative
        assert absolute == outside.resolve(), absolute
    return {"scenario": "glossary-path-semantics", "relative_under_workdir": True,
            "absolute_preserved": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Run real model probes; only valid when the model quota is available.")
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    if args.record.exists():
        parser.error("Choose a new record path; existing observations are preserved")

    report = {"schema": 1, "samples": {},
              "live": {"status": "not-run",
                       "reason": "live model probes are opt-in via --live"}}
    for name in ("fixed-file", "mixed-retrieval", "wait-what"):
        app = app_for(name)
        report["samples"][name] = {
            "application": str(app),
            "static": static_report(app),
            "entries": entry_report(name),
            "snapshot": snapshot_report(name),
        }
    report["samples"]["fixed-file"]["runtime"] = fixed_report()
    report["samples"]["fixed-file"]["boundaries"] = [missing_input_report(),
                                                     cancelled_report()]
    report["samples"]["mixed-retrieval"]["boundaries"] = mixed_boundaries_report()
    report["samples"]["wait-what"]["boundaries"] = [wait_path_report()]
    if args.live:
        try:
            mixed, wait = live_report()
        except Exception as exc:
            report["live"] = {"status": "failed",
                              "error": {"type": type(exc).__name__, "detail": str(exc)}}
        else:
            report["live"] = {"status": "executed", "mixed": mixed, "wait_what": wait}
    args.record.parent.mkdir(parents=True, exist_ok=True)
    with args.record.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"record": str(args.record), "live": report["live"]["status"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

