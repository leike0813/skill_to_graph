"""Explicit real MiniMax probes; only run after model and credential authorization."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain_core.callbacks import BaseCallbackHandler

ROOT = Path(__file__).resolve().parent


class ToolEvidence(BaseCallbackHandler):
    def __init__(self):
        self.calls = []

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.calls.append({"name": serialized.get("name"), "input": input_str})


def configure():
    os.environ.update(MODEL_PROVIDER="anthropic", MODEL_ID="MiniMax-M3.1-Flash",
                      MODEL_BASE_URL="https://api.minimax.cn/anthropic",
                      MODEL_API_KEY_ENV="MINIMAX_CN_API_KEY",
                      MODEL_OPTIONS=json.dumps({"max_tokens": 16384, "reasoning_effort": "low",
                                                "thinking": {"type": "adaptive"}}))
    if not os.environ.get("MINIMAX_CN_API_KEY"):
        raise RuntimeError("MINIMAX_CN_API_KEY is required")


def load(name):
    app = ROOT / "generated" / (name + "-graph")
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), app / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return app, module


def mixed_cases():
    app, module = load("mixed-retrieval")
    results = []
    with tempfile.TemporaryDirectory(prefix="mixed-live-") as temp:
        root = Path(temp)
        for name, question, reply in [
            ("sufficient", "Explain both what controls a LangGraph task and how its progress is stored. Cite evidence keys.", True),
            ("reject", "How does LangGraph control a task? Cite its evidence.", False),
            ("insufficient", "What is the price of a train ticket from Mars to Venus in 2099?", None),
        ]:
            output = root / name
            graph = module.make_graph(checkpointer=InMemorySaver())
            observer = ToolEvidence()
            config = {"configurable": {"thread_id": name}, "recursion_limit": 40, "callbacks": [observer]}
            value = graph.invoke({"question": question, "catalog": str(app / "source/mixed-retrieval/examples/catalog.json"),
                                  "output_dir": str(output)}, config)
            assert not output.exists(), "File side effect before approval"
            if reply is None:
                assert value["status"] == "insufficient" and "__interrupt__" not in value, value
                assert value["report"] == ""
            else:
                assert "__interrupt__" in value, value
                assert value["used_keys"] and value["report"], value
                value = graph.invoke(Command(resume=reply), config)
                assert value["status"] == ("ok" if reply else "cancelled"), value
                if reply:
                    assert (output / "report.md").read_text() == value["report"]
                else:
                    assert not output.exists()
            results.append({"scenario": name, "status": value["status"],
                            "used_keys": value["used_keys"], "report": value["report"],
                            "tools": observer.calls,
                            "before_approval_no_output": True})
    return results


def wait_what_case():
    options = json.loads(os.environ.get("MODEL_OPTIONS", "{}"))
    options["reasoning_effort"] = "high"
    os.environ["MODEL_OPTIONS"] = json.dumps(options)
    _, module = load("wait-what")
    workspace = ROOT.parent / "fixtures/wait-what-workspace"
    original = json.loads((workspace / "input.json").read_text())
    config = {"configurable": {"workdir": str(workspace.resolve())}, "recursion_limit": 30}
    graph = module.make_graph(config)
    value = graph.invoke({"messages": original["conversation"]}, config)
    tools = [{"name": m.name, "content": m.content} for m in value["messages"] if m.type == "tool"]
    assert tools, "No context tool use observed"
    content = value["messages"][-1].content
    reply = content if isinstance(content, str) else "\n".join(b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text")
    return {"scenario": "wait-what", "tools": tools, "reply": reply,
            "judgement": "pending semantic and language review"}


def main():
    configure()
    print(json.dumps({"evidence_kind": "live-model", "model": os.environ["MODEL_ID"],
                      "base_url": os.environ["MODEL_BASE_URL"], "mixed": mixed_cases(),
                      "wait_what": wait_what_case()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
