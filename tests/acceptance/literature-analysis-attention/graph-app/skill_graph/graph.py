"""Keep runtime stage ownership explicit and delegate semantic work to real agents."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import sqlite3
import subprocess
from typing import Any, TypedDict

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph import END, START, StateGraph

SOURCE = Path(__file__).resolve().parents[1] / "source/literature-analysis"
SCRIPT = SOURCE / "scripts/run_analysis.py"
STAGES = ["persist_analysis_plan", "persist_digest", "persist_literature_score",
          "persist_references", "persist_citation_analysis", "finalize_outputs"]
GUIDES = {"persist_analysis_plan": "source_and_plan.md", "persist_digest": "digest_generation.md",
          "persist_literature_score": "paper_scoring.md", "persist_references": "reference_extraction.md",
          "persist_citation_analysis": "citation_analysis.md", "finalize_outputs": "finalization_and_recovery.md"}


class State(TypedDict, total=False):
    source_path: str
    language: str
    score_only: bool
    identifier: str
    working_dir: str
    db_path: str
    action: str
    runtime: dict
    result: dict


def model():
    return init_chat_model(os.environ["MODEL_ID"], model_provider=os.environ["MODEL_PROVIDER"],
        base_url=os.environ["MODEL_BASE_URL"], api_key=os.environ[os.environ["MODEL_API_KEY_ENV"]],
        max_retries=0, **json.loads(os.environ.get("MODEL_OPTIONS", "{}")))


def log(work, event):
    with (work / "graph-events.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(), **event}, ensure_ascii=False) + "\n")


def runtime(work, action, arguments):
    command = shlex.split(os.environ["RUNTIME_PYTHON"]) + [str(SCRIPT), action] + arguments
    proc = subprocess.run(command, cwd=work, text=True, capture_output=True)
    try:
        value = json.loads(proc.stdout)
    except ValueError as exc:
        raise RuntimeError(f"Runtime {action} did not return JSON: {proc.stderr[-2000:]}") from exc
    log(work, {"kind": "runtime", "action": action, "exit_code": proc.returncode,
               "response": value})
    return value


def final_failure(code, message):
    return {"digest_path": "", "references_path": "", "citation_analysis_path": "",
            "literature_matching_metadata_path": "", "literature_score_path": "",
            "provenance": {"generated_at": "", "input_hash": "", "model": os.environ.get("MODEL_ID", "")},
            "warnings": [], "error": {"code": code, "message": str(message)}}


def outcome(value, db):
    if "digest_path" in value and "provenance" in value:
        return {"runtime": value, "result": value, "action": "completed"}
    if value.get("error"):
        issue = value["error"]
        return {"runtime": value, "result": final_failure(issue.get("code", "runtime_error"), issue.get("message", issue)),
                "action": "failed", "db_path": str(db)}
    action = value.get("next_action", "")
    action = {"prepare_references_workset": "persist_references", "prepare_citation_workset": "persist_citation_analysis"}.get(action, action)
    if action not in STAGES:
        raise RuntimeError(f"Unrecognized runtime action: {action}")
    return {"runtime": value, "action": action, "db_path": str(db)}


def initialize(state, config):
    settings = config.get("configurable", {})
    work = Path(settings["working_dir"]).resolve()
    work.mkdir(parents=True, exist_ok=True)
    db = work / ".literature_analysis_tmp/literature_analysis.db"
    if db.exists():
        value = runtime(work, "status", ["--db-path", str(db)])
        mirror = work / "literature-analysis.result.json"
        if value.get("next_action") == "completed" and mirror.is_file():
            result = json.loads(mirror.read_text())
            return {"working_dir": str(work), "db_path": str(db), "action": "completed", "result": result, "runtime": value}
    else:
        args = ["--source-path", str(Path(state["source_path"]).resolve()), "--language", state.get("language", "zh-CN"),
                "--working-dir", str(work), "--output-dir", str(work / "artifacts"),
                "--model", settings.get("model_label", os.environ["MODEL_ID"])]
        if state.get("identifier"):
            args += ["--identifier", state["identifier"]]
        if state.get("score_only", False):
            args += ["--score-only"]
        value = runtime(work, "init_runtime", args)
    return {"working_dir": str(work), **outcome(value, db)}


def stage_node(action):
    def execute(state, config):
        work, db = Path(state["working_dir"]), Path(state["db_path"])
        last = state["runtime"]
        submitted = False

        @tool
        def read_text(path: str, start_line: int = 1, line_count: int = 500) -> str:
            """Read a stage guide, runtime work package or local draft. Relative resources resolve in the run directory then the copied Skill package."""
            target = work / path
            if not target.is_file() and not Path(path).is_absolute():
                target = SOURCE / path
            try:
                content = target.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError) as exc:
                return json.dumps({"error": type(exc).__name__, "path": str(target), "detail": str(exc)})
            log(work, {"kind": "read", "action": action, "path": str(target)})
            return "\n".join(f"{i+1}: {line}" for i, line in enumerate(content)
                             if start_line-1 <= i < start_line-1+line_count)

        @tool
        def normalized_source(start_line: int = 1, line_count: int = 500) -> str:
            """Read the DB-owned normalized source with 1-based line numbers; use it for all paper judgments."""
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
                row = connection.execute("SELECT content FROM source_documents WHERE doc_key='normalized_source'").fetchone()
            return "\n".join(f"{i+1}: {line}" for i, line in enumerate(row[0].splitlines())
                             if start_line-1 <= i < start_line-1+line_count)

        @tool
        def write_json(path: str, content: str) -> str:
            """Serialize completed LLM decisions or merged batch drafts as JSON in the run directory, never public artifacts or DB."""
            target = (work / path).resolve()
            if not target.is_relative_to(work) or target.name in {"digest.md", "references.json", "citation_analysis.json", "citation_analysis.md", "literature_matching_metadata.json", "literature_score.json", "literature-analysis.result.json"}:
                return "Choose a draft path inside the run directory, not a public artifact filename."
            try:
                data = json.loads(content)
            except ValueError as exc:
                return json.dumps({"error": "invalid_json", "detail": str(exc)})
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            log(work, {"kind": "draft", "action": action, "path": str(target)})
            return str(target)

        @tool
        def fill_scoring_draft(path: str, decisions_json: str) -> str:
            """Apply LLM scoring decisions to the prepared form while retaining locked fields and order. decisions: paper_type, paper_type_reason, dimension_reviews and criterion_reviews with semantic fields only."""
            target = (work / path).resolve()
            if action != "persist_literature_score" or not target.is_relative_to(work):
                raise ValueError("Only edit the scoring form inside this run")
            draft = json.loads(target.read_text())
            decisions = json.loads(decisions_json)
            for choice in draft["paper_type_choices"]:
                choice["selected"] = choice["paper_type"] == decisions["paper_type"]
            draft["paper_type_reason"] = decisions["paper_type_reason"]
            for field, key, allowed in [("dimension_reviews", "dimension_key", {"summary", "confidence"}),
                                         ("criterion_reviews", "criterion_key", {"applicable", "score", "reason", "evidence_quotes"})]:
                updates = {r[key]: r for r in decisions[field]}
                for review in draft[field]:
                    for name in allowed:
                        if name in updates[review[key]]:
                            review[name] = updates[review[key]][name]
            target.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
            log(work, {"kind": "scoring-decisions", "path": str(target)})
            return str(target)

        @tool
        def run_runtime(payload_path: str = "") -> str:
            """Prepare or submit ONLY the current stage through run_analysis.py. Main agent is the sole DB writer. Read errors and repair according to the source Skill."""
            nonlocal last, submitted
            if action in {"persist_analysis_plan", "persist_digest"} and not payload_path:
                return json.dumps({"error": "payload_file_required", "detail": "This is a submit-only stage. Read normalized source, form your semantic payload, write_json to a draft path, then call run_runtime with that path."})
            if submitted and ("digest_path" in last or last.get("next_action") not in {action, ""}) and not last.get("error"):
                return "The stage has advanced; return control to the graph."
            args = ["--db-path", str(db)]
            if payload_path:
                args += ["--payload-file", str((work / payload_path).resolve())]
            last = runtime(work, action, args)
            submitted = submitted or bool(payload_path)
            return json.dumps(last, ensure_ascii=False)

        @tool
        def delegate_batches(batch_paths: list[str]) -> str:
            """Delegate the runtime's existing batches to separate same-model agents. Each worker reads only its assigned batch, returns a draft, and cannot call runtime, DB, network or final rendering."""
            def review(path):
                batch_path = (work / path).resolve()
                batch = json.loads(batch_path.read_text())

                @tool
                def read_batch() -> str:
                    """Read the only assigned local review batch including its source evidence, prompt and return shape."""
                    return json.dumps(batch, ensure_ascii=False)

                agent = create_agent(model=model(), tools=[read_batch], system_prompt=
                    "You are one literature-analysis batch reviewer. Read your assigned batch first. Follow its prompt and return shape, use only its local evidence, keep stable keys and locked fields, return ONLY the requested JSON draft. Do not add metadata beyond local evidence. No DB, runtime, network, final artifacts, global summary or timeline. You have only a read_batch tool. File writing is unavailable; return JSON directly.")
                response = agent.invoke({"messages": [{"role": "user", "content": "Review the assigned runtime batch and return its JSON draft."}]},
                                        {"recursion_limit": 40})
                content = response["messages"][-1].content
                text = content if isinstance(content, str) else "\n".join(x["text"] for x in content if isinstance(x, dict) and x.get("type") == "text")
                log(work, {"kind": "batch-review", "action": action, "batch_path": str(batch_path),
                           "model": os.environ["MODEL_ID"], "draft": text})
                return {"batch_path": str(batch_path), "draft": text}
            with ThreadPoolExecutor(max_workers=3) as pool:
                drafts = list(pool.map(review, batch_paths))
            return json.dumps(drafts, ensure_ascii=False)

        instructions = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
        guide = (SOURCE / "references" / GUIDES[action]).read_text(encoding="utf-8")
        prompt = (instructions + "\n\nCurrent stage guide:\n" + guide +
            f"\n\nYou own ONLY stage {action}. Working directory: {work}. DB: {db}. "
            "The graph initialized runtime and enforces the fixed stage order; do not reinitialize it. "
            "Use normalized_source for paper content; do not substitute the original file after init. "
            "Read stage work packages and prepare when required. Make semantic decisions yourself. "
            "write_json serializes your decisions; fill_scoring_draft retains locked form fields. "
            "When runtime returns batch paths, call delegate_batches with those exact paths, merge returned drafts with stable-key coverage checks, and submit once per round. "
            "Do not hand-review delegated batches, fabricate semantics using code, or ask the user. "
            "run_runtime is the only DB writer and can only call this stage. Fix payload validation according to source recovery rules. "
            "After successful submission advances next_action or returns final stdout JSON, return control. "
            "If runtime reports irrecoverable failure, stop and report it. Never report completed without runtime evidence. "
            "Final artifacts are rendered exclusively by runtime. Output language follows DB runtime inputs.")
        tools = [read_text, normalized_source, write_json, run_runtime, delegate_batches]
        if action == "persist_literature_score":
            tools.append(fill_scoring_draft)
        agent = create_agent(model=model(), tools=tools, system_prompt=prompt)
        log(work, {"kind": "stage-start", "action": action})
        response = agent.invoke({"messages": [{"role": "user", "content": json.dumps(last, ensure_ascii=False)}]}, config)
        log(work, {"kind": "stage-return", "action": action, "message_count": len(response["messages"])})
        if "digest_path" not in last and (not submitted or last.get("next_action") == action) and not last.get("error"):
            status = runtime(work, "status", ["--db-path", str(db)])
            if status.get("next_action") == action:
                raise RuntimeError(f"Agent returned before stage {action} was complete; DB retained for source-defined recovery")
            last = status
        return outcome(last, db)
    return execute


def make_graph(config=None):
    builder = StateGraph(State)
    builder.add_node("init_runtime", initialize)
    for stage in STAGES:
        builder.add_node(stage, stage_node(stage))
    builder.add_edge(START, "init_runtime")
    for stage in ["init_runtime", *STAGES]:
        builder.add_conditional_edges(stage, lambda state: END if state["action"] in {"completed", "failed"} else state["action"])
    return builder.compile()
