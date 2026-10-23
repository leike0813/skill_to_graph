"""Compare source-only and generated prompts with identical model, history and tools."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
APP = ROOT.parent / "generated/wait-what-graph"
WORK = REPO / "tests/fixtures/wait-what-workspace"


class Trace(BaseCallbackHandler):
    def __init__(self):
        self.first_request = None
        self.tools = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if self.first_request is None:
            self.first_request = [{"role": m.type, "content": m.content} for m in messages[0]]

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tools.append({"name": serialized.get("name"), "input": input_str})


def run(arm, repetitions, neutral_context=False, isolated=False):
    os.environ.update(MODEL_PROVIDER="anthropic", MODEL_ID="MiniMax-M3.1-Flash",
        MODEL_BASE_URL="https://api.minimax.cn/anthropic", MODEL_API_KEY_ENV="MINIMAX_CN_API_KEY",
        MODEL_OPTIONS=json.dumps({"max_tokens": 16384, "reasoning_effort": "high", "thinking": {"type": "adaptive"}}))
    spec = importlib.util.spec_from_file_location("wait_diagnostic", APP / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = (APP / "source/wait-what/SKILL.md").read_text().split("---", 2)[2].strip()
    conversation = json.loads((WORK / "input.json").read_text())["conversation"]
    if neutral_context:
        conversation[0]["content"] = "Please explain the task workflow."
    label = arm + ("-neutral" if neutral_context else "")
    work = WORK
    if isolated:
        work = Path(tempfile.mkdtemp(prefix="wait-what-graph-control-"))
        shutil.copy2(WORK / "GLOSSARY.md", work / "GLOSSARY.md")
        label += "-isolated"

    def source_agent(*, model, tools, middleware):
        # Change only the prompt; preserve the generated adapter's model and tool closures.
        return create_agent(model=model, tools=tools, system_prompt=source)

    for number in range(1, repetitions + 1):
        with (ROOT / f"{label}-{number}.json").open("x") as stream:
            started = time.time()
            trace = Trace()
            config = {"configurable": {"workdir": str(work)}, "recursion_limit": 30, "callbacks": [trace]}
            result = {"arm": label, "repetition": number, "model": os.environ["MODEL_ID"],
                      "model_options": json.loads(os.environ["MODEL_OPTIONS"]), "input": conversation}
            try:
                if arm == "source":
                    with patch.object(module, "create_agent", side_effect=source_agent):
                        graph = module.make_graph(config)
                else:
                    graph = module.make_graph(config)
                value = graph.invoke({"messages": conversation}, config)
                content = value["messages"][-1].content
                result["reply"] = content if isinstance(content, str) else "\n".join(b["text"] for b in content if b.get("type") == "text")
                result["tool_results"] = [{"name": m.name, "content": m.content} for m in value["messages"] if m.type == "tool"]
                assert trace.first_request[0]["role"] == "system"
                assert source in trace.first_request[0]["content"]
                assert [m["content"] for m in trace.first_request[1:]] == [m["content"] for m in conversation]
            except Exception as exc:
                result["error"] = {"type": type(exc).__name__, "detail": str(exc)}
            result.update(first_request=trace.first_request, tool_calls=trace.tools, elapsed_seconds=time.time()-started)
            json.dump(result, stream, ensure_ascii=False, indent=2)
            print(json.dumps({"arm": arm, "repetition": number, "error": result.get("error"), "reply": result.get("reply")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=["source", "current"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--neutral-context", action="store_true")
    parser.add_argument("--isolated", action="store_true")
    args = parser.parse_args()
    run(args.arm, args.repetitions, args.neutral_context, args.isolated)
