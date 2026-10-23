"""Run the source's autonomous rephrasing task with caller-supplied resources."""
import json
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool

SOURCE = Path(__file__).resolve().parents[1] / "source/wait-what/SKILL.md"


def make_graph(config=None):
    model = init_chat_model(
        os.environ["MODEL_ID"],
        model_provider=os.environ["MODEL_PROVIDER"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]],
        max_retries=0,
        **json.loads(os.environ.get("MODEL_OPTIONS", "{}")),
    )

    def task_path(runtime, path):
        candidate = Path(path).expanduser()
        workdir = Path(runtime.config["configurable"]["workdir"]).expanduser()
        return (candidate if candidate.is_absolute() else workdir / candidate).resolve()

    @tool
    def read_file(path: str, runtime: ToolRuntime) -> str:
        """Read a task file, such as GLOSSARY.md or GLOSSARY-MAP.md."""
        try:
            return task_path(runtime, path).read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            return json.dumps({"error": type(exc).__name__, "detail": str(exc)})

    @tool
    def list_files(runtime: ToolRuntime, path: str = ".") -> list[str] | dict:
        """List a task directory to locate applicable glossary files."""
        try:
            return [p.name for p in sorted(task_path(runtime, path).iterdir())]
        except (OSError, ValueError) as exc:
            return {"error": type(exc).__name__, "detail": str(exc)}

    instructions = SOURCE.read_text(encoding="utf-8").split("---", 2)[2].strip()

    @dynamic_prompt
    def source_prompt(request):
        messages = request.state["messages"]
        trigger = max((i for i, message in enumerate(messages) if message.type == "human"),
                      default=len(messages))
        passage = next((m.content for m in reversed(messages[:trigger]) if m.type == "ai"), None)
        return (instructions + "\n\nThis is an explicit invocation. Re-pitch the assistant passage"
                " below, using the conversation for context. Read the applicable task glossary"
                " with the supplied tools. Preserve the passage's claims, timing and uncertainty."
                "\nAssistant passage:\n" + json.dumps(passage, ensure_ascii=False))

    return create_agent(model=model, tools=[read_file, list_files], middleware=[source_prompt])
