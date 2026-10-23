import json
import os
from pathlib import Path
from typing import Literal, TypedDict

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field

SOURCE = Path(__file__).resolve().parents[1] / "source/mixed-retrieval"


class Evidence(BaseModel):
    status: Literal["sufficient", "insufficient"]
    report: str = Field(description="Direct answer only, with [key] evidence for each conclusion. No unsupported details or commentary on irrelevant catalog entries. Empty if insufficient.")
    used_keys: list[str] = Field(description="Exactly the inspected evidence keys cited in the report. Empty if the report is empty.")


class State(TypedDict, total=False):
    question: str
    catalog: str
    output_dir: str
    keys: list[str]
    needs_input: bool
    status: str
    report: str
    used_keys: list[str]
    approved: bool
    path: str
    error: dict


def failure(status: str, code: str, path, detail) -> dict:
    return {"status": status,
            "error": {"code": code, "path": str(path) if path is not None else None,
                      "detail": str(detail)}}


def collect(state: State):
    missing = [key for key in ("question", "catalog")
               if not isinstance(state.get(key), str)]
    if not missing:
        return {"needs_input": False}
    reply = interrupt({
        "question": "提供 question 和 catalog；缺失时不要猜路径。",
        "fields": missing,
    })
    received = ({key: reply[key] for key in missing
                 if isinstance(reply, dict) and isinstance(reply.get(key), str)
                 and reply[key].strip()}
                if isinstance(reply, dict) else {})
    return {**received, "needs_input": bool(set(missing) - set(received))}


def validate(state: State):
    question = state.get("question")
    if not isinstance(question, str) or not question.strip():
        return failure("error", "invalid-question", "question", "Question must not be blank")
    catalog_path = state.get("catalog")
    if not isinstance(catalog_path, str) or not catalog_path.strip():
        return failure("error", "invalid-catalog", "catalog", "Catalog path must not be blank")
    try:
        catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return failure("error", "invalid-catalog", catalog_path, exc)
    if not isinstance(catalog, dict) or not all(isinstance(value, str) for value in catalog.values()):
        return failure("error", "invalid-catalog", catalog_path,
                       "Catalog must be a JSON object with string values")
    return {"keys": list(catalog), "status": "validated"}


class LookupFailure(Exception):
    pass


RETRIEVAL_INSTRUCTIONS = """You perform only the evidence-retrieval stage of the source task.

Answer the supplied question from the local evidence catalog. Choose which keys to inspect and
how many calls to make. Read evidence only with the lookup(key) tool. Do not use external search
or network retrieval, and do not answer by reading the catalog through another route.

After each lookup, decide semantically whether the evidence collected so far is sufficient.
Continue with another available key while it may still help. Stop when the evidence is sufficient,
or when the catalog cannot support an answer. The stopping condition is evidence sufficiency, not
a fixed number of lookups or report length. If sufficient, write a report that answers the
question directly and marks every conclusion with the evidence key it rests on in square brackets.
Every cited conclusion must be supported by the actual retrieved text. Do not expand a short
entry with remembered implementation details, extra capabilities, or advice.
Before returning, check each claim against its cited entry and remove unsupported details.
Report only the answer, without commentary on irrelevant entries. used_keys contains exactly
the inspected keys cited in the report; with an empty report it is an empty list.
If insufficient, stop and return status insufficient with an empty report.

Return exactly the structured fields status (sufficient or insufficient), report, and used_keys
(the inspected keys that support the report). A lookup tool failure stops this stage; do not retry.
"""


def retrieve(state: State, config):
    catalog_path = state["catalog"]

    @tool
    def lookup(key: str) -> str:
        """Read one catalog entry by key. This is the only evidence-reading route."""
        try:
            catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
            return catalog[key]
        except (OSError, ValueError, KeyError) as exc:
            raise LookupFailure(str(exc)) from exc

    options = json.loads(os.environ.get("MODEL_OPTIONS", "{}"))
    model = init_chat_model(
        os.environ["MODEL_ID"],
        model_provider=os.environ["MODEL_PROVIDER"],
        base_url=os.environ["MODEL_BASE_URL"],
        api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]],
        max_retries=0,
        **options,
    )
    prompt = (
        RETRIEVAL_INSTRUCTIONS
        + "\nQuestion:\n" + state["question"].strip()
        + "\nAvailable catalog keys (evidence text remains available only through lookup):\n"
        + json.dumps(state["keys"], ensure_ascii=False)
    )
    agent = create_agent(
        model=model,
        tools=[lookup],
        system_prompt=prompt,
        response_format=ToolStrategy(Evidence, handle_errors=False),
    )
    try:
        response = agent.invoke(
            {"messages": [{"role": "user", "content": state["question"]}]}, config)
    except LookupFailure as exc:
        return failure("failed", "lookup-error", catalog_path, exc)
    except GraphRecursionError as exc:
        return failure("failed", "execution-limited", "retrieval", exc)
    result = response.get("structured_response")
    if not isinstance(result, Evidence):
        return failure("failed", "model-output", "retrieval",
                       "The retrieval model did not return the required structured result")
    result = result.model_dump()
    if result["status"] == "insufficient":
        result["report"] = ""
    return result


def confirm(state: State):
    output_dir = state.get("output_dir")
    while not (isinstance(output_dir, str) and output_dir.strip()):
        reply = interrupt({
            "question": "提供 output_dir；报告写入前必须先确定目录。",
            "field": "output_dir",
        })
        output_dir = (reply.get("output_dir") if isinstance(reply, dict)
                      else reply if isinstance(reply, str) else None)
    target = Path(output_dir).expanduser().resolve() / "report.md"
    approved = interrupt({
        "question": "回复 true 批准写入 report.md，回复 false 放弃。",
        "report": state["report"],
        "used_keys": state["used_keys"],
        "path": str(target),
    }) is True
    return {"output_dir": output_dir, "approved": approved,
            "status": "approved" if approved else "cancelled"}


def write(state: State):
    target = Path(state["output_dir"]).expanduser().resolve() / "report.md"
    if target.exists():
        return failure("error", "file-exists", target, "Refusing to overwrite an existing report.md")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("x", encoding="utf-8") as stream:
            stream.write(state["report"])
    except OSError as exc:
        return failure("error", "write-error", target, exc)
    return {"status": "ok", "path": str(target)}


def cancel(state: State):
    return {"status": "cancelled"}


def make_graph(config=None, *, checkpointer=None, store=None):
    builder = StateGraph(State)
    builder.add_node("collect", collect)
    builder.add_node("validate", validate)
    builder.add_node("retrieve", retrieve)
    builder.add_node("confirm", confirm)
    builder.add_node("write", write)
    builder.add_node("cancel", cancel)
    builder.add_edge(START, "collect")
    builder.add_conditional_edges("collect",
                                  lambda state: "collect" if state["needs_input"] else "validate")
    builder.add_conditional_edges("validate",
                                  lambda state: "retrieve" if state["status"] == "validated" else END)
    builder.add_conditional_edges("retrieve",
                                  lambda state: "confirm" if state["status"] == "sufficient" else END)
    builder.add_conditional_edges("confirm",
                                  lambda state: "write" if state["approved"] else "cancel")
    builder.add_edge("write", END)
    builder.add_edge("cancel", END)
    return builder.compile(checkpointer=checkpointer, store=store)


def cli_graph(config):
    return make_graph(config)

