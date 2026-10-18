"""AI Release Intelligence Assistant — точка входу.

    python main.py run                                    # усі моделі × усі конфіги семплінгу
    python main.py run --models provider --sampling A --limit 3
"""

import argparse
import statistics
import sys

from src.config import ROOT, load_config
from src.extraction.pipeline import load_documents, run_extraction
from src.extraction.prompts import load_prompt
from src.llm import LLMError, SamplingParams, make_client
from src.schema import DefectReport


def percentile(values: list[int], p: float) -> int:
    if len(values) < 2:
        return values[0] if values else 0
    return int(statistics.quantiles(values, n=100, method="inclusive")[int(p) - 1])


def print_summary(records: list[dict]) -> None:
    statuses = {s: sum(r["status"] == s for r in records) for s in ("ok", "repaired", "failed")}
    latencies = [r["latency_ms"] for r in records if r["status"] != "failed"]
    costs = [r["cost_usd"] for r in records if r["cost_usd"] is not None]
    valid = (statuses["ok"] + statuses["repaired"]) / len(records) * 100
    print(f"  статуси: {statuses}  → валідних {valid:.0f}%")
    if latencies:
        print(f"  latency: p50 {percentile(latencies, 50)} ms, p95 {percentile(latencies, 95)} ms")
    if costs:
        print(f"  вартість: ${sum(costs):.5f} за прогін, ≈ ${sum(costs) / len(records) * 1000:.4f} на 1000 документів")


def cmd_run(args, config: dict) -> int:
    ex = config["extraction"]
    prompt = load_prompt(args.prompt or ex["prompt"])
    docs = load_documents([ROOT / p for p in config["data"]["inputs"]])
    if args.limit:
        docs = docs[: args.limit]
    model_keys = args.models.split(",") if args.models else list(config["models"])
    sampling_keys = args.sampling.split(",") if args.sampling else list(config["sampling"])
    print(f"Документів: {len(docs)} | промпт: {prompt.id} | моделі: {model_keys} | семплінг: {sampling_keys}")

    exit_code = 0
    for model_key in model_keys:
        model_cfg = config["models"][model_key]
        try:
            client = make_client(model_cfg, config)
        except LLMError as e:
            print(f"\n[{model_key}] пропущено: {e}")
            exit_code = 1
            continue
        for sampling_key in sampling_keys:
            params = SamplingParams(**config["sampling"][sampling_key], max_tokens=ex["max_tokens"])
            print(f"\n[{model_key}] {client.name} · семплінг {sampling_key} {config['sampling'][sampling_key]}")
            out_path, records = run_extraction(
                client, prompt, docs, DefectReport, sampling_key, params,
                ex["repair_attempts"], model_cfg["price_per_1m_tokens"], ROOT / config["data"]["results_dir"],
            )
            print_summary(records)
            print(f"  → {out_path.relative_to(ROOT)}")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Release Intelligence Assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="прогнати extraction і зберегти результати в results/")
    run.add_argument("--models", help="ключі з config/models.yaml через кому, напр. provider,local")
    run.add_argument("--sampling", help="конфіги семплінгу через кому, напр. A,B")
    run.add_argument("--prompt", help="версія промпту, напр. extract_defect/v1 (за замовчуванням — з конфігу)")
    run.add_argument("--limit", type=int, help="обробити лише перші N документів")
    args = parser.parse_args()

    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # кирилиця в консолі Windows
    config = load_config()
    return cmd_run(args, config)


if __name__ == "__main__":
    sys.exit(main())
