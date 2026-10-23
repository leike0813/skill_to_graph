"""Fixed source workflow with scoped semantic agents and DB-owned context."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
from typing import TypedDict

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph

APP = Path(__file__).resolve().parents[1]
SOURCE = APP / "source/literature-analysis"
spec = importlib.util.spec_from_file_location("literature_local_prompts", APP / "skill_graph/prompts.py")
prompts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompts)
STAGES = tuple(prompts.DUTIES)
FINAL_FILES = {"digest.md", "references.json", "citation_analysis.json", "citation_analysis.md",
               "literature_matching_metadata.json", "literature_score.json", "literature-analysis.result.json"}


class State(TypedDict, total=False):
    source_path: str
    language: str
    identifier: str
    score_only: bool
    working_dir: str
    db_path: str
    action: str
    runtime: dict
    result: dict


def model():
    return init_chat_model(os.environ["MODEL_ID"], model_provider=os.environ["MODEL_PROVIDER"],
        base_url=os.environ["MODEL_BASE_URL"], api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]],
        max_retries=0, **json.loads(os.environ.get("MODEL_OPTIONS", "{}")))


def log(work, kind, **fields):
    with (work / "graph-events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), "kind": kind, **fields}, ensure_ascii=False) + "\n")


def runtime(work, action, arguments):
    command = shlex.split(os.environ["RUNTIME_PYTHON"]) + [str(SOURCE / "scripts/run_analysis.py"), action] + arguments
    proc = subprocess.run(command, cwd=work, capture_output=True, text=True)
    try:
        value = json.loads(proc.stdout)
    except ValueError as exc:
        raise RuntimeError(f"{action} returned non-JSON: {proc.stderr[-2000:]}") from exc
    log(work, "runtime", action=action, exit_code=proc.returncode, response=value)
    return value


def failure(code, message):
    return {**{key: "" for key in ["digest_path", "references_path", "citation_analysis_path",
        "literature_matching_metadata_path", "literature_score_path"]},
        "provenance": {"generated_at": "", "input_hash": "", "model": ""},
        "warnings": [], "error": {"code": code, "message": str(message)}}


def outcome(value):
    if value.get("error"):
        error = value["error"]
        return {"action": "failed", "runtime": value,
                "result": failure(error.get("code", "runtime_error"), error.get("message", error))}
    if "digest_path" in value and "provenance" in value:
        return {"action": "completed", "runtime": value, "result": value}
    action = {"prepare_references_workset": "persist_references", "prepare_citation_workset": "persist_citation_analysis"}.get(
        value.get("next_action"), value.get("next_action"))
    if action not in (*STAGES, "finalize_outputs"):
        raise RuntimeError(f"Unknown source next_action: {action}")
    return {"action": action, "runtime": value}


def context(db):
    """Read public run settings from the original runtime SSOT, not incoming state."""
    with closing(sqlite3.connect(f"file:{db}?mode=ro", uri=True)) as connection:
        values = dict(connection.execute("SELECT key,value FROM runtime_inputs"))
    return {key: values[key] for key in ["language", "model", "score_only", "identifier"] if key in values}


def initialize(state, config):
    settings = config.get("configurable", {})
    work = Path(settings["working_dir"]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    db = work / ".literature_analysis_tmp/literature_analysis.db"
    if db.exists():
        value = runtime(work, "status", ["--db-path", str(db)])
        if value.get("workflow_state", {}).get("current_stage") == "stage_8_completed":
            value = runtime(work, "finalize_outputs", ["--db-path", str(db)])
    else:
        args = ["--source-path", str(Path(state["source_path"]).resolve()), "--language", state.get("language", "zh-CN"),
                "--working-dir", str(work), "--output-dir", str(work / "artifacts"),
                "--model", settings.get("model_label", os.environ["MODEL_ID"])]
        if state.get("identifier"):
            args += ["--identifier", state["identifier"]]
        if state.get("score_only", False):
            args.append("--score-only")
        value = runtime(work, "init_runtime", args)
    return {"working_dir": str(work), "db_path": str(db), **outcome(value)}


def draft_path(work, path):
    target = (work / path).resolve()
    if not target.is_relative_to(work) or target.name in FINAL_FILES or target.name.startswith("scoring_review_form.") or target.is_relative_to(work / "artifacts") or target.suffix != ".json":
        raise ValueError("Choose a JSON draft inside this run, outside public artifacts")
    return target


def stage_node(action):
    def execute(state, config):
        work, db = Path(state["working_dir"]), Path(state["db_path"])
        settings = context(db)
        last = state["runtime"]
        submitted = False

        @tool
        def read_context(kind: str = "source", start_line: int = 1, line_count: int = 500) -> str:
            """Read DB-owned normalized source (numbered), outline, or scopes; settings are already in your input."""
            if action == "persist_citation_analysis" and kind == "source":
                return json.dumps({"error": "batch_evidence_only", "detail": "Citation semantics use runtime citation_work_packages, not a new full-source scan."})
            with closing(sqlite3.connect(f"file:{db}?mode=ro", uri=True)) as connection:
                connection.row_factory = sqlite3.Row
                if kind == "source":
                    content = connection.execute("SELECT content FROM source_documents WHERE doc_key='normalized_source'").fetchone()[0]
                    return "\n".join(f"{i+1}: {line}" for i, line in enumerate(content.splitlines()) if start_line-1 <= i < start_line-1+line_count)
                query = {"outline": "SELECT * FROM outline_nodes ORDER BY position", "scopes": "SELECT * FROM section_scopes"}
                return json.dumps([dict(row) for row in connection.execute(query[kind])], ensure_ascii=False)

        @tool
        def read_text(path: str, start_line: int = 1, line_count: int = 500) -> str:
            """Read a stage reference, runtime work package, draft or rendered output, without changing it."""
            target = (work / path).resolve()
            if not target.is_file() and not Path(path).is_absolute():
                target = (SOURCE / path).resolve()
            if not (target.is_relative_to(work) or target.is_relative_to(SOURCE / "references")):
                return json.dumps({"error": "outside_stage_resources"})
            if target.name in {"source.md", "source_meta.json"} or target.suffix == ".db":
                return json.dumps({"error": "db_truth_only", "detail": "Use read_context for allowed DB evidence and runtime batches for citation semantics."})
            try:
                lines = target.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError) as exc:
                return json.dumps({"error": type(exc).__name__, "detail": str(exc)})
            log(work, "read", action=action, path=str(target))
            return "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines) if start_line-1 <= i < start_line-1+line_count)

        @tool
        def write_draft(path: str, content: str) -> str:
            """Serialize your completed semantic decisions to a JSON draft; no DB or public artifact edits."""
            try:
                target = draft_path(work, path)
                value = json.loads(content)
            except (ValueError, OSError) as exc:
                return json.dumps({"error": type(exc).__name__, "detail": str(exc)})
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
            log(work, "draft", action=action, path=str(target))
            return str(target)

        @tool
        def fill_scoring_draft(path: str, decisions_json: str) -> str:
            """Fill editable score fields, preserving locked values/order. decisions_json is an object with paper_type, paper_type_reason, dimension_reviews (array of objects with dimension_key/summary/confidence), criterion_reviews (array of objects with criterion_key/applicable/score/reason/evidence_quotes). Include every original key once; do not use maps keyed by ID."""
            try:
                target = draft_path(work, path)
                draft, choices = json.loads(target.read_text()), json.loads(decisions_json)
                if choices["paper_type"] not in {item["paper_type"] for item in draft["paper_type_choices"]}:
                    raise ValueError("Select one original paper_type")
                for item in draft["paper_type_choices"]:
                    item["selected"] = item["paper_type"] == choices["paper_type"]
                draft["paper_type_reason"] = choices["paper_type_reason"]
                for field, key, allowed in [("dimension_reviews", "dimension_key", {"summary", "confidence"}),
                                             ("criterion_reviews", "criterion_key", {"applicable", "score", "reason", "evidence_quotes"})]:
                    rows = choices[field]
                    if not isinstance(rows, list) or not all(isinstance(item, dict) for item in rows):
                        raise ValueError(f"{field} must be an array of objects containing {key}")
                    updates = {item[key]: item for item in rows}
                    if len(updates) != len(rows) or set(updates) != {item[key] for item in draft[field]}:
                        raise ValueError(f"{field} must contain each original {key} exactly once")
                    for item in draft[field]:
                        for name in allowed:
                            if name in updates[item[key]]:
                                item[name] = updates[item[key]][name]
                target.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
            except (TypeError, KeyError, ValueError, OSError) as exc:
                return json.dumps({"error": "invalid_scoring_decisions", "detail": str(exc)})
            return str(target)

        @tool
        def run_stage(payload_path: str = "") -> str:
            """Prepare/submit the current stage. Source-permitted corrections can resubmit after a successful submission. Only this tool writes DB."""
            nonlocal last, submitted
            if action in {"persist_analysis_plan", "persist_digest"} and not payload_path:
                return json.dumps({"error": "payload_required", "detail": "Form a semantic payload and write_draft before submitting."})
            args = ["--db-path", str(db)]
            if payload_path:
                args += ["--payload-file", str(draft_path(work, payload_path))]
            last = runtime(work, action, args)
            submitted = submitted or bool(payload_path)
            return json.dumps(last, ensure_ascii=False)

        @tool
        def delegate_batches(batch_paths: list[str]) -> str:
            """Send the runtime's exact batches to independent same-model read-only agents; return drafts, never submit or render."""
            available = {str((work / p).resolve()) for field in ["reference_core_batch_paths", "metadata_evidence_batch_paths", "citation_batch_paths"] for p in last.get(field, [])}
            if any(str((work / path).resolve()) not in available for path in batch_paths):
                raise ValueError("Only the current runtime-returned batch paths can be delegated")

            def review(path):
                target = (work / path).resolve()
                batch = json.loads(target.read_text())

                @tool
                def read_batch() -> str:
                    """Read only this assigned runtime batch and its source evidence/contract."""
                    return json.dumps(batch, ensure_ascii=False)

                agent = create_agent(model=model(), tools=[read_batch], system_prompt=prompts.BATCH)
                response = agent.invoke({"messages": [{"role": "user", "content": json.dumps({"language": settings["language"], "task": "审核本批次并返回约定 JSON draft"}, ensure_ascii=False)}]}, {"recursion_limit": 40})
                content = response["messages"][-1].content
                draft = content if isinstance(content, str) else "\n".join(b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text")
                log(work, "batch-review", action=action, batch_path=str(target), model=os.environ["MODEL_ID"], language=settings["language"], draft=draft)
                return {"batch_path": str(target), "draft": draft}

            with ThreadPoolExecutor(max_workers=3) as pool:
                return json.dumps(list(pool.map(review, batch_paths)), ensure_ascii=False)

        tools = [read_context, read_text, write_draft, run_stage]
        if action == "persist_literature_score":
            tools.append(fill_scoring_draft)
        if action in {"persist_references", "persist_citation_analysis"}:
            tools.append(delegate_batches)
        agent = create_agent(model=model(), tools=tools, system_prompt=prompts.COMMON + "\n\n" + prompts.DUTIES[action])
        log(work, "stage-start", action=action, settings=settings, tools=[t.name for t in tools])
        try:
            response = agent.invoke({"messages": [{"role": "user", "content": json.dumps({"runtime_inputs": settings, "stage_runtime": last}, ensure_ascii=False)}]}, config)
        except Exception as exc:
            log(work, "stage-failure", action=action, code=type(exc).__name__, detail=str(exc))
            return {"action": "failed", "result": failure(type(exc).__name__, str(exc)), "runtime": last}
        log(work, "stage-return", action=action, message_count=len(response["messages"]))
        if not submitted and not last.get("error"):
            raise RuntimeError(f"Stage {action} returned without a semantic submission")
        return outcome(last)
    return execute


def finalize(state):
    work, db = Path(state["working_dir"]), state["db_path"]
    value = runtime(work, "finalize_outputs", ["--db-path", db])
    if value.get("error"):
        status = runtime(work, "status", ["--db-path", db])
        repairs = {"outline_nodes": "persist_analysis_plan", "section_scopes.references_scope": "persist_analysis_plan",
                   "section_scopes.citation_scope": "persist_analysis_plan", "digest_slots": "persist_digest",
                   "digest_section_summaries": "persist_digest", "literature_score": "persist_literature_score",
                   "reference_items": "persist_references", "citation_timeline": "persist_citation_analysis",
                   "citation_summary": "persist_citation_analysis"}
        needed = {repairs[key] for key in status.get("missing_prerequisites", []) if key in repairs}
        for action in STAGES:
            if action in needed:
                # The source explicitly routes missing persisted state back to its owning stage.
                return {"action": action, "runtime": status}
    return outcome(value)


def make_graph(config=None):
    builder = StateGraph(State)
    builder.add_node("init_runtime", initialize)
    for action in STAGES:
        builder.add_node(action, stage_node(action))
    builder.add_node("finalize_outputs", finalize)
    builder.add_edge(START, "init_runtime")
    for action in ["init_runtime", *STAGES, "finalize_outputs"]:
        builder.add_conditional_edges(action, lambda state: END if state["action"] in {"completed", "failed"} else state["action"])
    return builder.compile()
