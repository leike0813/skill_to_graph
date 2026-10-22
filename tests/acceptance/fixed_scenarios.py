"""Run source-derived file scenarios with real local scripts and LangGraph."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

APP = Path(__file__).resolve().parent / "generated/fixed-file-graph"


def load(app):
    spec = importlib.util.spec_from_file_location("file_scenario", app / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scenarios(app):
    observations = []
    module = load(app)
    with tempfile.TemporaryDirectory() as temp:
        work = Path(temp)
        for name, reply in [("approve", True), ("reject", False), ("existing", True)]:
            out = work / name
            if name == "existing":
                out.mkdir()
                (out / "summary.txt").write_text("keep")
            graph = module.make_graph(checkpointer=InMemorySaver())
            config = {"configurable": {"thread_id": name}}
            pending = graph.invoke({"source_csv": str(app / "source/fixed-file/data/example.csv"),
                                    "output_dir": str(out)}, config)
            assert "__interrupt__" in pending
            assert pending["rows"] == 2 and pending["total"] == 5
            if name != "existing":
                assert not out.exists()
            final = graph.invoke(Command(resume=reply), config)
            expected = {"approve": "ok", "reject": "cancelled", "existing": "error"}[name]
            assert final["status"] == expected, final
            if name == "approve":
                assert (out / "summary.txt").read_text() == "Total: 5\n"
            elif name == "reject":
                assert not out.exists()
            else:
                assert (out / "summary.txt").read_text() == "keep"
            observations.append({"scenario": name, "status": final["status"], "assertions": "passed"})
        for name, content in [("negative", "name,count\na,-1\n"), ("missing-column", "name\na\n")]:
            csv = work / (name + ".csv")
            csv.write_text(content)
            out = work / (name + "-out")
            final = module.make_graph().invoke({"source_csv": str(csv), "output_dir": str(out)})
            assert final["status"] == "error" and not out.exists(), final
            assert final["error"]["code"] == "invalid-csv"
            observations.append({"scenario": name, "status": final["status"], "assertions": "passed"})
        final = module.make_graph().invoke({"source_csv": str(work / "missing.csv"),
                                            "output_dir": str(work / "missing-out")})
        assert final["status"] == "error" and not (work / "missing-out").exists()
        observations.append({"scenario": "script-io-failure", "status": "error", "assertions": "passed"})
    return observations


def main():
    original = scenarios(APP)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        transient_source = root / "original/fixed-file"
        shutil.copytree(APP / "source/fixed-file", transient_source)
        staged = root / "staged"
        helper = Path(__file__).resolve().parents[2] / "skill-to-graph/scripts/skill_package.py"
        subprocess.run([sys.executable, str(helper), "copy", str(transient_source),
                        "--output", str(staged)], check=True, capture_output=True)
        for item in APP.iterdir():
            if item.name != "source":
                if item.is_dir():
                    shutil.copytree(item, staged / item.name)
                else:
                    shutil.copy2(item, staged / item.name)
        moved = root / "moved"
        staged.rename(moved)
        # Make the test conversion's source path unavailable while retaining the user fixture.
        transient_source.rename(root / "unavailable-source")
        relocated = scenarios(moved)
    print(json.dumps({"evidence_kind": "real-local-runtime", "original": original,
                      "relocated": relocated, "model_used": False}, indent=2))


if __name__ == "__main__":
    main()
