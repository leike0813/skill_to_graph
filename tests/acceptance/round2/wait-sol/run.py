"""User-selected gpt-6.1-sol comparison; keeps earlier models and records untouched."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from unittest.mock import patch

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
APP = ROOT.parent / "generated/wait-what-graph"
FIXTURE = REPO / "tests/fixtures/wait-what-workspace"
CONVERSATION = json.loads((FIXTURE / "input.json").read_text())["conversation"]


def graph_run(number):
    os.environ.update(MODEL_PROVIDER="openai", MODEL_ID="gpt-6.1-sol",
        MODEL_BASE_URL="https://192.168.13.111:10100/v1", MODEL_API_KEY_ENV="OPENCODEX_API_AUTH_TOKEN",
        MODEL_OPTIONS=json.dumps({"use_responses_api": True, "reasoning_effort": "medium",
                                  "max_tokens": 8192, "timeout": 90, "store": False}),
        SSL_CERT_FILE=os.environ["NODE_EXTRA_CA_CERTS"])
    spec = importlib.util.spec_from_file_location("wait_sol_graph", APP / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    trace_spec = importlib.util.spec_from_file_location("wait_sol_trace", ROOT.parent / "wait-diagnosis/probe.py")
    trace_module = importlib.util.module_from_spec(trace_spec)
    trace_spec.loader.exec_module(trace_module)
    trace = trace_module.Trace()
    requests = []
    original_send = httpx.Client.send

    def send(client, request, *args, **kwargs):
        body = json.loads(request.content) if request.content else {}
        requests.append({"method": request.method, "url": str(request.url), "model": body.get("model"),
                         "reasoning": body.get("reasoning"), "store": body.get("store")})
        return original_send(client, request, *args, **kwargs)

    with tempfile.TemporaryDirectory(prefix="wait-sol-graph-") as temp:
        work = Path(temp)
        shutil.copy2(FIXTURE / "GLOSSARY.md", work / "GLOSSARY.md")
        started = time.time()
        config = {"configurable": {"workdir": str(work)}, "recursion_limit": 30, "callbacks": [trace]}
        record = {"entry": "generated-graph", "model": "gpt-6.1-sol", "reasoning_effort": "medium",
                  "input": CONVERSATION, "certificate_verification": "existing NODE_EXTRA_CA_CERTS bundle"}
        try:
            with patch.object(httpx.Client, "send", new=send):
                value = module.make_graph(config).invoke({"messages": CONVERSATION}, config)
            content = value["messages"][-1].content
            record["reply"] = content if isinstance(content, str) else "\n".join(b["text"] for b in content if b.get("type") == "text")
            record["tool_results"] = [{"name": m.name, "content": m.content} for m in value["messages"] if m.type == "tool"]
            assert requests and all(r["url"].endswith("/v1/responses") and r["model"] == "gpt-6.1-sol" and r["reasoning"]["effort"] == "medium" for r in requests)
            assert [m["content"] for m in trace.first_request[1:]] == [m["content"] for m in CONVERSATION]
        except Exception as exc:
            record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
        record.update(elapsed_seconds=time.time()-started, requests=requests,
                      first_request=trace.first_request, tool_calls=trace.tools)
    return record


def omp_run(number):
    with tempfile.TemporaryDirectory(prefix="wait-sol-omp-") as temp:
        work = Path(temp)
        shutil.copytree(APP / "source/wait-what", work / "wait-what")
        shutil.copy2(FIXTURE / "GLOSSARY.md", work / "GLOSSARY.md")
        prompt = (f"Execute the explicitly invoked Agent Skill at {work / 'wait-what/SKILL.md'}. "
                  "Read its instructions and the applicable glossary. The task conversation is role-tagged data below; "
                  "its final user message invokes the Skill. Return the Skill response.\n\n"
                  + json.dumps(CONVERSATION, ensure_ascii=False, indent=2))
        command = ["omp", "-p", "--model", "openai-codex/gpt-6.1-sol", "--thinking", "medium",
            "--config", str(ROOT / "omp-config.yml"), "--cwd", str(work), "--session-dir", str(work / "sessions"),
            "--no-title", "--no-lsp", "--no-extensions", "--no-skills", "--no-rules", "--tools", "read,find",
            "--system-prompt", "You execute explicitly invoked Agent Skills. Follow the supplied Skill and conversation. Read task resources when needed.",
            "--mode", "json", "--max-time", "3m", "--approval-mode", "yolo", prompt]
        log_fd, log_name = tempfile.mkstemp(prefix=f"wait-sol-omp-{number}-", suffix=".jsonl")
        os.close(log_fd)
        log = Path(log_name)
        stderr = log.with_suffix(".stderr")
        started = time.time()
        record = {"entry": "omp-source", "model": "openai-codex/gpt-6.1-sol", "reasoning_effort": "medium",
                  "input": CONVERSATION, "raw_log": str(log)}
        try:
            with log.open("w") as output, stderr.open("w") as errors:
                proc = subprocess.run(command, stdout=output, stderr=errors, timeout=200)
            record["exit_code"] = proc.returncode
            messages = []
            for line in log.read_text().splitlines():
                event = json.loads(line)
                if event.get("type") == "message_end":
                    messages.append(event["message"])
            final = next(m for m in reversed(messages) if m.get("role") == "assistant" and m.get("stopReason") == "stop")
            record.update(provider=final.get("provider"), api=final.get("api"), observed_model=final.get("model"),
                reply="\n".join(b["text"] for b in final["content"] if b.get("type") == "text"),
                tool_calls=[{"name": b["name"], "arguments": b["arguments"]} for m in messages for b in m.get("content", []) if b.get("type") == "toolCall"],
                tool_results=[m for m in messages if m.get("role") == "toolResult"])
            assert proc.returncode == 0 and final["model"] == "gpt-6.1-sol" and final["provider"] == "openai-codex"
        except Exception as exc:
            record["error"] = {"type": type(exc).__name__, "detail": str(exc)}
            record["stderr_tail"] = stderr.read_text()[-1500:] if stderr.exists() else ""
        record["elapsed_seconds"] = time.time()-started
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=["graph", "omp"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--start-number", type=int, default=1)
    args = parser.parse_args()
    for number in range(args.start_number, args.start_number + args.repetitions):
        with (ROOT / f"{args.entry}-{number}.json").open("x") as stream:
            record = graph_run(number) if args.entry == "graph" else omp_run(number)
            json.dump(record, stream, ensure_ascii=False, indent=2)
            print(json.dumps({"entry": args.entry, "repetition": number, "error": record.get("error"), "reply": record.get("reply")}, ensure_ascii=False), flush=True)
        if record.get("error"):
            break
