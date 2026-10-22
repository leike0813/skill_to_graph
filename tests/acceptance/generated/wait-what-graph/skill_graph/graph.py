import json
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool

SOURCE = Path(__file__).resolve().parents[1] / "source/wait-what"


def make_graph(config=None):
    model = init_chat_model(os.environ["MODEL_ID"], model_provider=os.environ["MODEL_PROVIDER"],
                            base_url=os.environ["MODEL_BASE_URL"],
                            api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]], max_retries=0,
                            **json.loads(os.environ.get("MODEL_OPTIONS", "{}")))

    @tool
    def read_file(path: str, runtime: ToolRuntime) -> str:
        """Read a task-context file relative to the task working directory, including mapped glossaries."""
        workdir = Path(runtime.config["configurable"]["workdir"]).resolve()
        try:
            return (workdir / path).read_text(encoding="utf-8")
        except OSError as exc:
            return json.dumps({"error": type(exc).__name__, "detail": str(exc)})

    @tool
    def list_files(runtime: ToolRuntime, path: str = ".") -> list[str] | dict:
        """List a task directory to find GLOSSARY.md or GLOSSARY-MAP.md."""
        workdir = Path(runtime.config["configurable"]["workdir"]).resolve()
        try:
            return [str(p.relative_to(workdir)) for p in sorted((workdir / path).iterdir())]
        except (OSError, ValueError) as exc:
            return {"error": type(exc).__name__, "detail": str(exc)}

    instructions = (SOURCE / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]

    @dynamic_prompt
    def source_prompt(request):
        messages = request.state["messages"]
        trigger = max((i for i, m in enumerate(messages) if m.type == "human"), default=len(messages))
        passage = next((m.content for m in reversed(messages[:trigger]) if m.type == "ai"), None)
        return instructions + "\nSource passage to re-pitch:\n" + json.dumps(passage, ensure_ascii=False) + "\nRephrase this passage. Keep its events, tense, causal relations and uncertainty. Give a little context from the conversation, rather than a new explanation of how such a system would usually work. Before replying, check that each factual claim comes from the passage or its context and that the wording is simple."

    return create_agent(model=model, tools=[read_file, list_files],
                        middleware=[source_prompt])
