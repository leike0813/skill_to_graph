"""Controlled model responses test routing; local lookup and file writes remain real."""
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from live_scenarios import load, ToolEvidence


class ModelDouble(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def call(name, args, identifier):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": identifier, "type": "tool_call"}])


def main():
    app, module = load("mixed-retrieval")
    # Model construction is replaced; no credential, provider, or network access is used.
    with tempfile.TemporaryDirectory(prefix="mixed-double-") as temp:
        root = Path(temp)
        source = str(app / "source/mixed-retrieval/examples/catalog.json")
        responses = [call("lookup", {"key": "alpha"}, "1"), call("lookup", {"key": "beta"}, "2"),
                     call("Evidence", {"status": "sufficient", "report": "Nodes and edges control the task [alpha]. Checkpoints store progress [beta].", "used_keys": ["alpha", "beta"]}, "3")]
        observer = ToolEvidence()
        config = {"configurable": {"thread_id": "loop"}, "callbacks": [observer]}
        fake = ModelDouble(responses=responses)
        with patch.object(module, "init_chat_model", return_value=fake), patch.dict(module.os.environ, {
            "MODEL_ID": "double", "MODEL_PROVIDER": "double", "MODEL_BASE_URL": "unused",
            "MODEL_API_KEY_ENV": "DOUBLE_KEY", "DOUBLE_KEY": "synthetic-not-a-key"}):
            graph = module.make_graph(checkpointer=InMemorySaver())
            pending = graph.invoke({"question": "Explain control and saved progress", "catalog": source,
                                    "output_dir": str(root / "success")}, config)
            assert "__interrupt__" in pending and not (root / "success").exists()
            final = graph.invoke(Command(resume=True), config)
            assert final["status"] == "ok"
            assert [x["name"] for x in observer.calls] == ["lookup", "lookup"]
            assert (root / "success/report.md").read_text() == final["report"]
            print(json.dumps({"evidence_kind": "double", "scenario": "semantic-loop-routing", "outcome": "passed", "tools": observer.calls}))

            error_model = ModelDouble(responses=[call("lookup", {"key": "absent"}, "bad")])
            observer = ToolEvidence()
            with patch.object(module, "init_chat_model", return_value=error_model):
                final = module.make_graph().invoke({"question": "Find evidence", "catalog": source,
                    "output_dir": str(root / "failure")}, {"callbacks": [observer]})
                assert final["status"] == "failed" and not (root / "failure").exists(), final
                assert len(observer.calls) == 1
            print(json.dumps({"evidence_kind": "double", "scenario": "lookup-failure-stops", "outcome": "passed", "status": final["status"], "tool_calls": len(observer.calls)}))

            for catalog in [source, str(root / "missing.json")]:
                final = module.make_graph().invoke({"question": "", "catalog": catalog, "output_dir": str(root / "invalid")})
                assert final["status"] == "error" and not (root / "invalid").exists()
            print(json.dumps({"evidence_kind": "real-local-runtime", "scenario": "input-validation", "outcome": "passed"}))

            existing = root / "existing"
            existing.mkdir()
            (existing / "report.md").write_text("keep")
            graph = module.make_graph(checkpointer=InMemorySaver())
            cfg = {"configurable": {"thread_id": "existing"}}
            graph.invoke({"question": "Explain control and saved progress", "catalog": source,
                          "output_dir": str(existing)}, cfg)
            final = graph.invoke(Command(resume=True), cfg)
            assert final["status"] == "error" and (existing / "report.md").read_text() == "keep"
            print(json.dumps({"evidence_kind": "double", "scenario": "existing-file-protected", "outcome": "passed"}))


if __name__ == "__main__":
    main()
