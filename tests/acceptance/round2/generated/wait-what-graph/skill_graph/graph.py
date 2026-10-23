import json
import os
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool

SOURCE = Path(__file__).resolve().parents[1] / "source/wait-what"


def task_path(runtime: ToolRuntime, path: str) -> Path:
    """Resolve a task-context path: relative paths sit under the workdir, absolute paths stand."""
    workdir = Path(runtime.config["configurable"]["workdir"]).expanduser().resolve()
    candidate = Path(path).expanduser()
    return candidate.resolve() if candidate.is_absolute() else (workdir / candidate).resolve()


def make_graph(config=None):
    options = json.loads(os.environ.get("MODEL_OPTIONS", "{}"))
    model = init_chat_model(
        os.environ["MODEL_ID"],
        model_provider=os.environ["MODEL_PROVIDER"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]],
        max_retries=0,
        **options,
    )

    @tool
    def read_file(path: str, runtime: ToolRuntime) -> str:
        """Read a task-context file, including GLOSSARY.md or GLOSSARY-MAP.md."""
        try:
            candidate = task_path(runtime, path)
            return candidate.read_text(encoding="utf-8")
        except (OSError, ValueError) as exc:
            return json.dumps({"error": type(exc).__name__, "detail": str(exc)})

    @tool
    def list_files(runtime: ToolRuntime, path: str = ".") -> list[str] | dict:
        """List a task-context directory to locate glossary files."""
        try:
            root = task_path(runtime, path)
            return [item.name for item in sorted(root.iterdir())]
        except (OSError, ValueError) as exc:
            return {"error": type(exc).__name__, "detail": str(exc)}

    instructions = (SOURCE / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2].strip()

    @dynamic_prompt
    def source_prompt(request):
        messages = request.state["messages"]
        trigger = max((index for index, message in enumerate(messages)
                       if message.type == "human"), default=len(messages))
        passage = next((message.content for message in reversed(messages[:trigger])
                        if message.type == "ai"), None)
        return (
            instructions
            + "\n\nRephrase only the assistant passage below. Earlier user questions give the"
              " topic, not evidence for claims or timing. Read the workdir glossary with the"
              " tools; use GLOSSARY-MAP.md when it selects among glossaries."
              " Give a little context,"
              " then the same claims in simple words. Preserve the passage's explicit timing"
              " and uncertainty; do not infer additional steps, consequences, or user tasks."
              " A saved record describes a state, not a new saving step."
              " Use simple verbs such as wait, link, continue, make, and write; explain jargon"
              " in plain words while keeping the glossary's domain names."
              " Check each statement against the passage before returning."
            + "\nAssistant passage to re-pitch:\n"
            + json.dumps(passage, ensure_ascii=False)
        )

    return create_agent(model=model, tools=[read_file, list_files],
                        middleware=[source_prompt])

