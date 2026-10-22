import json
import os
from pathlib import Path
from typing import Literal, TypedDict

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel

SOURCE = Path(__file__).resolve().parents[1] / "source/mixed-retrieval"


class Evidence(BaseModel):
    status: Literal["sufficient", "insufficient"]
    report: str
    used_keys: list[str]


class State(TypedDict, total=False):
    question: str
    catalog: str
    output_dir: str
    keys: list[str]
    status: str
    report: str
    used_keys: list[str]
    approved: bool
    path: str
    error: dict


def failure(status, code, path, detail):
    return {"status": status, "error": {"code": code, "path": str(path), "detail": str(detail)}}


def gather(state):
    missing = [key for key in ("question", "catalog") if key not in state]
    if missing:
        reply = interrupt({"question": "Provide missing task inputs", "fields": missing})
        return {key: reply[key] for key in missing}
    return {}


def validate(state):
    question = state.get("question", "")
    if not isinstance(question, str) or not question.strip():
        return failure("error", "invalid-input", "question", "Expected a nonempty question")
    try:
        catalog = json.loads(Path(state["catalog"]).read_text(encoding="utf-8"))
        if not isinstance(catalog, dict) or not all(isinstance(v, str) for v in catalog.values()):
            return failure("error", "invalid-catalog", state["catalog"], "Expected string-valued JSON object")
        return {"keys": list(catalog), "status": "validated"}
    except (OSError, ValueError, KeyError) as exc:
        return failure("error", "invalid-catalog", state.get("catalog"), exc)


class LookupFailure(Exception):
    pass


def retrieve(state, config):
    @tool
    def lookup(key: str) -> str:
        """Read one evidence entry by its catalog key. Use only available keys."""
        try:
            return json.loads(Path(state["catalog"]).read_text(encoding="utf-8"))[key]
        except (OSError, ValueError, KeyError) as exc:
            raise LookupFailure(str(exc)) from exc

    model = init_chat_model(os.environ["MODEL_ID"], model_provider=os.environ["MODEL_PROVIDER"],
                            base_url=os.environ["MODEL_BASE_URL"],
                            api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]], max_retries=0,
                            **json.loads(os.environ.get("MODEL_OPTIONS", "{}")))
    instructions = (SOURCE / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[2]
    agent = create_agent(model=model, tools=[lookup],
                        system_prompt=instructions + "\nYou perform the retrieval stage only. The graph will handle approval and writing. Available keys: " + json.dumps(state["keys"]),
                        response_format=ToolStrategy(Evidence, handle_errors=False))
    try:
        response = agent.invoke({"messages": [{"role": "user", "content": state["question"]}]}, config)
    except LookupFailure as exc:
        return failure("failed", "lookup-error", state["catalog"], exc)
    result = response["structured_response"]
    return result.model_dump()


def confirm(state):
    output_dir = state.get("output_dir")
    if not output_dir:
        output_dir = interrupt({"question": "Which output directory should receive report.md?"})
    approved = interrupt({"question": "Write report.md?", "report": state["report"],
                          "used_keys": state["used_keys"],
                          "path": str(Path(output_dir) / "report.md")}) is True
    return {"approved": approved, "output_dir": output_dir,
            "status": "approved" if approved else "cancelled"}


def write(state):
    path = Path(state["output_dir"]) / "report.md"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8") as stream:
            stream.write(state["report"])
        return {"status": "ok", "path": str(path)}
    except OSError as exc:
        return failure("error", "write-error", path, exc)


def make_graph(config=None, *, checkpointer=None, store=None):
    builder = StateGraph(State)
    for name, node in [("gather", gather), ("validate", validate), ("retrieve", retrieve), ("confirm", confirm), ("write", write)]:
        builder.add_node(name, node)
    builder.add_edge(START, "gather")
    builder.add_edge("gather", "validate")
    builder.add_conditional_edges("validate", lambda s: "retrieve" if s["status"] == "validated" else END)
    builder.add_conditional_edges("retrieve", lambda s: "confirm" if s["status"] == "sufficient" else END)
    builder.add_conditional_edges("confirm", lambda s: "write" if s["approved"] else END)
    builder.add_edge("write", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def cli_graph(config):
    return make_graph(config)
