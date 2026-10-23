"""Explicit full literature run using existing graph or isolated omp source execution."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from unittest.mock import patch

import httpx2 as httpx

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
APP = ROOT.parent / "generated/literature-analysis-graph"
SOURCE = APP / "source/literature-analysis"
PAPER = REPO / "tests/acceptance/literature-analysis-attention/input/mineru/attention-is-all-you-need.md"
BASE_URL = "https://192.168.13.111:10100/v1"
PAYLOAD = {"source_path": str(PAPER), "language": "zh-CN", "score_only": False,
           "identifier": "arXiv:1706.03762"}
PYTHON = "uv run --project /home/joshua/.ar --locked --no-sync -- python -B"


def safe_detail(exc):
    text = str(exc)
    secret = os.environ.get("OPENCODEX_API_AUTH_TOKEN")
    return text.replace(secret, "[redacted]")[:2000] if secret else text[:2000]


def graph_run(work):
    os.environ.update(MODEL_PROVIDER="openai", MODEL_ID="gpt-6.1-sol", MODEL_BASE_URL=BASE_URL,
        MODEL_API_KEY_ENV="OPENCODEX_API_AUTH_TOKEN", RUNTIME_PYTHON=PYTHON,
        MODEL_OPTIONS=json.dumps({"use_responses_api": True, "reasoning_effort": "medium",
            "max_tokens": 32768, "timeout": 300, "store": False}),
        SSL_CERT_FILE=os.environ["NODE_EXTRA_CA_CERTS"])
    spec = importlib.util.spec_from_file_location("literature_sol_medium", APP / "skill_graph/graph.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    requests = []
    original_send = httpx.Client.send

    def send(client, request, *args, **kwargs):
        body = json.loads(request.content) if request.content else {}
        item = {"method": request.method, "url": str(request.url), "model": body.get("model"),
                "reasoning": body.get("reasoning"), "store": body.get("store")}
        requests.append(item)
        with (work / "requests.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(item) + "\n")
        response = original_send(client, request, *args, **kwargs)
        item["status_code"] = response.status_code
        return response

    try:
        with patch.object(httpx.Client, "send", new=send):
            state = module.make_graph().invoke(PAYLOAD, {"configurable": {
                "working_dir": str(work), "model_label": "gpt-6.1-sol"}, "recursion_limit": 300})
        result = state["result"]
    except Exception as exc:
        result = module.failure(type(exc).__name__, safe_detail(exc))
    (work / "observed-final-response.txt").write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    valid = bool(requests) and all(r["url"] == BASE_URL + "/responses" and r["model"] == "gpt-6.1-sol"
                                 and r["reasoning"]["effort"] == "medium" for r in requests)
    return {"result": result, "requests": requests, "requested_transport_verified": valid,
            "execution": "failed" if result.get("error") else "executed"}


def omp_run(work):
    prompt = f"""请完整执行 {SOURCE / 'SKILL.md'} 定义的 literature-analysis 技能。
先读该 SKILL.md，在相应阶段按需读取包内参考和 runtime JIT。不要修改源 Skill 或论文。
任务 payload：{json.dumps(PAYLOAD, ensure_ascii=False)}
当前 cwd 是本组独立任务目录 {work}，作为 init_runtime 的 working_dir；产物放 artifacts/，
独立 DB 和结果镜像留在 cwd。model provenance 填 opencodex-hub/gpt-6.1-sol。
Python 使用 {PYTHON} {SOURCE / 'scripts/run_analysis.py'} ...，保持 cwd，不安装或升级依赖。
从头执行完整流程：计划、digest、评分、参考文献、metadata evidence review、citation semantic review、runtime 渲染。
默认按 runtime 预切 batch 路径委派 task agent。主执行与所有 task 均使用 opencodex-hub/gpt-6.1-sol，
思考强度 medium。主 agent 唯一写 DB；subagent 只读分配批次，只产 draft，不运行 runtime 或渲染。
语义判断由真实模型完成；脚本只做源允许的读取、序列化、合并、校验和渲染，不以规则生成摘要或评分。
源校验错误按其正式修正路径处理，不修改源代码、DB、公开产物来假造通过。
只在当前任务目录写入，读取仅限指定源包、论文和本次批次。不要读取旧组结果或其他项目，
不要读取凭据文件或打印环境。可以按源规则访问公开 bibliography API；metadata evidence review 不联网。
这是后台已授权执行，无需向用户提问。不启动服务器、不提交 Git。完成后原样输出 runtime 最终 stdout JSON，
不加围栏或解释，不截短字段；未完成则如实按源错误契约报告。
"""
    (ROOT / "control-prompt.md").write_text(prompt, encoding="utf-8")
    fd, name = tempfile.mkstemp(prefix="literature-sol-medium-omp-", suffix=".jsonl")
    os.close(fd)
    log = Path(name)
    errors = log.with_suffix(".stderr")
    sessions = Path(tempfile.mkdtemp(prefix="literature-sol-medium-sessions-"))
    command = ["omp", "-p", "--model", "opencodex-hub/gpt-6.1-sol", "--thinking", "medium",
        "--smol", "opencodex-hub/gpt-6.1-sol:medium", "--slow", "opencodex-hub/gpt-6.1-sol:medium",
        "--plan", "opencodex-hub/gpt-6.1-sol:medium", "--config", str(ROOT / "omp-config.yml"),
        "--cwd", str(work), "--session-dir", str(sessions), "--no-title", "--no-lsp", "--no-extensions",
        "--no-skills", "--no-rules", "--mode", "json", "--max-time", "60m", "--approval-mode", "yolo", prompt]
    record = {"raw_log": str(log), "stderr_log": str(errors), "sessions": str(sessions),
              "model": "opencodex-hub/gpt-6.1-sol", "thinking": "medium"}
    with (ROOT / "omp-process.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    try:
        with log.open("w") as out, errors.open("w") as err:
            proc = subprocess.run(command, stdout=out, stderr=err, timeout=3660)
        record["exit_code"] = proc.returncode
        messages = []
        with log.open() as stream:
            for line in stream:
                event = json.loads(line)
                if event.get("type") == "message_end":
                    messages.append(event["message"])
        final = next(m for m in reversed(messages) if m.get("role") == "assistant" and m.get("stopReason") == "stop")
        reply = final["content"] if isinstance(final["content"], str) else "\n".join(
            b["text"] for b in final["content"] if isinstance(b, dict) and b.get("type") == "text")
        (work / "observed-final-response.txt").write_text(reply, encoding="utf-8")
        record.update(provider=final.get("provider"), observed_model=final.get("model"), api=final.get("api"),
            tool_calls=[{"name": b["name"], "arguments": b["arguments"]} for m in messages
                        for b in m.get("content", []) if isinstance(b, dict) and b.get("type") == "toolCall"])
        try:
            record["result"] = json.loads(reply)
        except ValueError:
            record["final_response_not_json"] = True
        record["execution"] = "executed" if proc.returncode == 0 else "failed"
    except Exception as exc:
        record.update(error={"type": type(exc).__name__, "detail": safe_detail(exc)}, execution="failed")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entry", choices=["graph", "omp"])
    args = parser.parse_args()
    work = ROOT / ("graph-run" if args.entry == "graph" else "control")
    work.mkdir(exist_ok=False)
    assert PAPER.is_file() and (SOURCE / "SKILL.md").is_file()
    assert not (work / ".literature_analysis_tmp/literature_analysis.db").exists()
    started = time.time()
    with (ROOT / f"{args.entry}-result.json").open("x", encoding="utf-8") as stream:
        result = graph_run(work) if args.entry == "graph" else omp_run(work)
        record = {"entry": args.entry, "input": PAYLOAD, "working_dir": str(work),
                  "started_at_epoch": started, "elapsed_seconds": time.time() - started, **result}
        json.dump(record, stream, ensure_ascii=False, indent=2)
    print(json.dumps({"entry": args.entry, "execution": record["execution"],
                      "error": record.get("error") or record.get("result", {}).get("error"),
                      "elapsed_seconds": record["elapsed_seconds"]}, ensure_ascii=False), flush=True)
