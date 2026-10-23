"""Explicit real-model invocation of the second-round literature graph."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent


def load():
    path = ROOT / "generated/literature-analysis-graph/skill_graph/graph.py"
    spec = importlib.util.spec_from_file_location("round2_literature", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configure():
    os.environ.update(MODEL_PROVIDER="anthropic", MODEL_ID="MiniMax-M3.1-Flash",
        MODEL_BASE_URL="https://api.minimax.cn/anthropic", MODEL_API_KEY_ENV="MINIMAX_CN_API_KEY",
        MODEL_OPTIONS=json.dumps({"max_tokens": 32768, "reasoning_effort": "high", "thinking": {"type": "adaptive"}}),
        RUNTIME_PYTHON="uv run --project /home/joshua/.ar --locked --no-sync -- python -B")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default="literature-run")
    parser.add_argument("--record", required=True)
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()
    record = Path(args.record).resolve()
    record.parent.mkdir(parents=True, exist_ok=True)
    with record.open("x", encoding="utf-8") as stream:
        configure()
        module = load()
        work = (ROOT / args.run).resolve()
        work.mkdir(parents=True, exist_ok=True)
        payload = {"source_path": str(ROOT.parent / "literature-analysis-attention/input/mineru/attention-is-all-you-need.md"),
                   "language": "zh-CN", "score_only": args.score_only, "identifier": "arXiv:1706.03762"}
        started = time.time()
        try:
            state = module.make_graph().invoke(payload, {"configurable": {
                "working_dir": str(work), "model_label": "minimax-code-cn/MiniMax-M3.1-Flash"}, "recursion_limit": 300})
            result = state["result"]
        except Exception as exc:
            result = module.failure(type(exc).__name__, str(exc))
        json.dump({"elapsed_seconds": time.time()-started, "evidence_kind": "live-model", "input": payload,
                   "work": str(work), "result": result}, stream, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
