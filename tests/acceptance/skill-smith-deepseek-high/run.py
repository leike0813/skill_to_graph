"""Explicit live comparison with fresh records; never starts a service."""
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
from langchain_core.callbacks import BaseCallbackHandler

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
APP = ROOT / "generated/wait-what-graph"
FIXTURE = REPO / "tests/fixtures/wait-what-workspace"
CONVERSATION = json.loads((FIXTURE / "input.json").read_text(encoding="utf-8"))["conversation"]
GRAPH_MODEL = "combo/deepseek-v4.1-flash"
OMP_MODEL = "commandcode/deepseek/deepseek-v4.1-flash"
BASE_URL = "https://192.168.13.111:10100/v1"


def safe_error(exc):
    detail = str(exc)
    for name in ("OPENCODEX_API_AUTH_TOKEN", "COMMAND_CODE_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            detail = detail.replace(secret, "[redacted]")
    return {"type": type(exc).__name__, "detail": detail[:2000]}


class Trace(BaseCallbackHandler):
    def __init__(self):
        self.first_request = None
        self.tools = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if self.first_request is None:
            self.first_request = [{"role": m.type, "content": m.content} for m in messages[0]]

    def on_tool_start(self, serialized, input_str, **kwargs):
        self.tools.append({"name": serialized.get("name"), "input": input_str})


def graph_run(number):
    os.environ.update(
        MODEL_PROVIDER="openai", MODEL_ID=GRAPH_MODEL, MODEL_BASE_URL=BASE_URL,
        MODEL_API_KEY_ENV="OPENCODEX_API_AUTH_TOKEN",
        MODEL_OPTIONS=json.dumps({"use_responses_api": True, "reasoning_effort": "high",
                                  "max_tokens": 8192, "timeout": 180, "store": False}),
        SSL_CERT_FILE=os.environ["NODE_EXTRA_CA_CERTS"],
    )
    spec = importlib.util.spec_from_file_location("wait_deepseek_graph", APP / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    trace = Trace()
    requests = []
    original_send = httpx.Client.send

    def send(client, request, *args, **kwargs):
        body = json.loads(request.content) if request.content else {}
        metadata = {"method": request.method, "url": str(request.url), "model": body.get("model"),
                    "reasoning": body.get("reasoning"), "store": body.get("store")}
        requests.append(metadata)
        response = original_send(client, request, *args, **kwargs)
        metadata["status_code"] = response.status_code
        return response

    with tempfile.TemporaryDirectory(prefix="skill-smith-graph-") as temp:
        work = Path(temp)
        shutil.copy2(FIXTURE / "GLOSSARY.md", work / "GLOSSARY.md")
        started = time.time()
        config = {"configurable": {"workdir": str(work)}, "recursion_limit": 30, "callbacks": [trace]}
        record = {"entry": "generated-graph", "repetition": number, "model": GRAPH_MODEL,
                  "reasoning_effort": "high", "input": CONVERSATION,
                  "certificate_verification": "existing NODE_EXTRA_CA_CERTS bundle"}
        try:
            with patch.object(httpx.Client, "send", new=send):
                value = module.make_graph(config).invoke({"messages": CONVERSATION}, config)
            content = value["messages"][-1].content
            record["reply"] = content if isinstance(content, str) else "\n".join(
                b["text"] for b in content if b.get("type") == "text")
            record["tool_results"] = [{"name": m.name, "content": m.content}
                                      for m in value["messages"] if m.type == "tool"]
            record["response_metadata"] = value["messages"][-1].response_metadata
            assert requests and all(r["method"] == "POST" and r["url"] == BASE_URL + "/responses"
                and r["model"] == GRAPH_MODEL and r["reasoning"]["effort"] == "high" for r in requests)
            assert [m["content"] for m in trace.first_request[1:]] == [m["content"] for m in CONVERSATION]
            source = (APP / "source/wait-what/SKILL.md").read_text(encoding="utf-8").split("---", 2)[2].strip()
            assert source in trace.first_request[0]["content"]
            record["execution"] = "executed"
        except Exception as exc:
            record.update(error=safe_error(exc), execution="failed")
        record.update(elapsed_seconds=time.time() - started, requests=requests,
                      first_request=trace.first_request, tool_calls=trace.tools)
    return record


def omp_run(number):
    with tempfile.TemporaryDirectory(prefix="skill-smith-omp-") as temp:
        work = Path(temp)
        shutil.copytree(APP / "source/wait-what", work / "wait-what")
        shutil.copy2(FIXTURE / "GLOSSARY.md", work / "GLOSSARY.md")
        prompt = (f"Execute the explicitly invoked Agent Skill at {work / 'wait-what/SKILL.md'}. "
                  "Read its instructions and the applicable glossary. The task conversation is role-tagged data below; "
                  "its final user message invokes the Skill. Return the Skill response.\n\n"
                  + json.dumps(CONVERSATION, ensure_ascii=False, indent=2))
        command = ["omp", "-p", "--model", OMP_MODEL, "--thinking", "high",
            "--config", str(ROOT / "omp-config.yml"), "--cwd", str(work), "--session-dir", str(work / "sessions"),
            "--no-title", "--no-lsp", "--no-extensions", "--no-skills", "--no-rules", "--tools", "read,find",
            "--system-prompt", "You execute explicitly invoked Agent Skills. Follow the supplied Skill and conversation. Read task resources when needed.",
            "--mode", "json", "--max-time", "5m", "--approval-mode", "yolo", prompt]
        fd, name = tempfile.mkstemp(prefix=f"skill-smith-omp-{number}-", suffix=".jsonl")
        os.close(fd)
        log = Path(name)
        stderr = log.with_suffix(".stderr")
        started = time.time()
        record = {"entry": "omp-source", "repetition": number, "model": OMP_MODEL,
                  "reasoning_effort": "high", "input": CONVERSATION, "raw_log": str(log)}
        try:
            with log.open("w") as output, stderr.open("w") as errors:
                proc = subprocess.run(command, stdout=output, stderr=errors, timeout=320)
            record["exit_code"] = proc.returncode
            messages = [event["message"] for line in log.read_text().splitlines()
                        if (event := json.loads(line)).get("type") == "message_end"]
            finals = [m for m in messages if m.get("role") == "assistant" and m.get("stopReason") == "stop"]
            if not finals:
                raise RuntimeError("No completed assistant message; inspect local raw log")
            final = finals[-1]
            record.update(provider=final.get("provider"), api=final.get("api"), observed_model=final.get("model"),
                reply="\n".join(b["text"] for b in final["content"] if b.get("type") == "text"),
                tool_calls=[{"name": b["name"], "arguments": b["arguments"]} for m in messages
                            for b in m.get("content", []) if b.get("type") == "toolCall"],
                tool_results=[m for m in messages if m.get("role") == "toolResult"])
            assert proc.returncode == 0 and final["model"] == "deepseek/deepseek-v4.1-flash" and final["provider"] == "commandcode"
            record["execution"] = "executed"
        except Exception as exc:
            record.update(error=safe_error(exc), execution="failed")
        record["elapsed_seconds"] = time.time() - started
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=["graph", "omp"])
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    for number in range(1, args.repetitions + 1):
        with (ROOT / f"{args.entry}-{number}.json").open("x", encoding="utf-8") as stream:
            record = graph_run(number) if args.entry == "graph" else omp_run(number)
            json.dump(record, stream, ensure_ascii=False, indent=2)
            print(json.dumps({"entry": args.entry, "repetition": number, "error": record.get("error"),
                              "reply": record.get("reply")}, ensure_ascii=False), flush=True)
        if record.get("error"):
            break
