"""Probe an already configured local CLI service; does not start it."""
import argparse
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent


def run(server):
    def post(path, value):
        req = Request(server.rstrip("/") + path, data=json.dumps(value).encode(),
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=240) as response:
            return json.loads(response.read())
    observations = []
    with tempfile.TemporaryDirectory(prefix="cli-graph-") as temp:
        root = Path(temp)
        for graph_id, reply in [("fixed-file", True), ("fixed-file", False), ("mixed-retrieval", True)]:
            out = root / (graph_id + str(reply))
            if graph_id == "fixed-file":
                payload = {"source_csv": str(ROOT / "generated/fixed-file-graph/source/fixed-file/data/example.csv"), "output_dir": str(out)}
            else:
                payload = {"question": "Explain both explicit graph control and saved progress, using evidence keys.",
                           "catalog": str(ROOT / "generated/mixed-retrieval-graph/source/mixed-retrieval/examples/catalog.json"),
                           "output_dir": str(out)}
            thread = post("/threads", {})["thread_id"]
            pending = post(f"/threads/{thread}/runs/wait", {"assistant_id": graph_id, "input": payload})
            assert "__interrupt__" in pending and not out.exists(), pending
            final = post(f"/threads/{thread}/runs/wait", {"assistant_id": graph_id, "command": {"resume": reply}})
            assert final["status"] == ("ok" if reply else "cancelled"), final
            if reply:
                path = out / ("summary.txt" if graph_id == "fixed-file" else "report.md")
                assert path.is_file()
                expected = "Total: 5\n" if graph_id == "fixed-file" else final["report"]
                assert path.read_text() == expected
            else:
                assert not out.exists()
            observations.append({"graph_id": graph_id, "reply": reply, "thread_id": thread,
                                 "pause_before_file": True, "result": final})
        workspace = ROOT.parent / "fixtures/wait-what-workspace"
        original = json.loads((workspace / "input.json").read_text())
        value = post("/runs/wait", {"assistant_id": "wait-what", "input": {"messages": original["conversation"]},
                    "config": {"configurable": {"workdir": str(workspace)}}})
        assert value.get("messages") and "__error__" not in value, value
        last = value["messages"][-1]["content"]
        reply = last if isinstance(last, str) else "\n".join(b["text"] for b in last if b.get("type") == "text")
        observations.append({"graph_id": "wait-what", "reply": reply, "loaded_and_called": True})
    return {"entry": "CLI Agent Server", "server": server, "observations": observations,
            "semantic_review": "required for model responses"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.server), ensure_ascii=False, indent=2))
