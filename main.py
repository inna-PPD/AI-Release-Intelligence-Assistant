"""AI Release Intelligence Assistant — точка входу.

    python main.py run                                    # усі моделі × усі конфіги семплінгу + метрики
    python main.py run --models provider --sampling A --limit 3
    python main.py eval                                   # перерахувати метрики з results/*.jsonl
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from src.config import ROOT, load_config
from src.evaluation.metrics import FIELDS, evaluate_run
from src.extraction.pipeline import load_documents, run_extraction
from src.extraction.prompts import load_prompt
from src.llm import LLMError, SamplingParams, make_client
from src.schema import DefectReport

GOLDEN_PATH = ROOT / "data" / "golden" / "golden_set.json"


def load_golden() -> dict[str, dict]:
    rows = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    unreviewed = sum(not r.get("reviewed") for r in rows)
    if unreviewed:
        print(f"⚠ golden set: {unreviewed} з {len(rows)} записів ще не перевірені вручну (reviewed: false)")
    return {r["id"]: r["expected"] for r in rows}


def load_results(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fmt(value, spec: str = ".2f", empty: str = "—") -> str:
    return empty if value is None else format(value, spec)


def print_summary(m: dict) -> None:
    print(f"  валідних {m['valid_pct']:.0f}% (ok {m['ok']}, repaired {m['repaired']}, failed {m['failed']})"
          f" · p50 {m['p50_ms']} ms · p95 {m['p95_ms']} ms · ${fmt(m['cost_per_1000_usd'], '.4f')} / 1000 док."
          f" · field accuracy {fmt(m['field_accuracy'])} ({m['golden_docs']} golden)")


def write_report_tables(metrics: list[dict], results_dir: Path) -> None:
    summary_cols = ["model", "prompt", "sampling", "docs", "valid_pct", "failed", "p50_ms", "p95_ms",
                    "cost_per_1000_usd", "field_accuracy"]
    with (results_dir / "metrics.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", *summary_cols, *FIELDS])
        for m in metrics:
            writer.writerow([m["run_id"], *(m[c] for c in summary_cols), *(m["fields"].get(fl) for fl in FIELDS)])

    lines = [
        "## Зведена таблиця",
        "",
        "| Модель | Промпт | Семплінг | Валідних | Failed | p50, мс | p95, мс | $ / 1000 док. | Field accuracy |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in metrics:
        lines.append(f"| {m['model']} | {m['prompt']} | {m['sampling']} | {m['valid_pct']:.0f}% | {m['failed']} "
                     f"| {m['p50_ms']} | {m['p95_ms']} | {fmt(m['cost_per_1000_usd'], '.4f')} | {fmt(m['field_accuracy'])} |")
    lines += ["", "## Точність по полях (golden set)", "",
              "| Поле | " + " | ".join(f"{m['model']} · {m['prompt'].split('/')[-1]} · {m['sampling']}" for m in metrics) + " |",
              "|---|" + "---|" * len(metrics)]
    for field in FIELDS:
        lines.append(f"| {field} | " + " | ".join(fmt(m["fields"].get(field)) for m in metrics) + " |")
    (results_dir / "metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_run(args, config: dict) -> int:
    ex = config["extraction"]
    prompt = load_prompt(args.prompt or ex["prompt"])
    docs = load_documents([ROOT / p for p in config["data"]["inputs"]])
    if args.limit:
        docs = docs[: args.limit]
    golden = load_golden()
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
            print_summary(evaluate_run(records, golden))
            print(f"  → {out_path.relative_to(ROOT)}")
    return exit_code


def cmd_eval(args, config: dict) -> int:
    results_dir = ROOT / config["data"]["results_dir"]
    paths = [Path(p) for p in args.files] if args.files else sorted(results_dir.glob("*.jsonl"))
    if not paths:
        print("Немає результатів у results/ — спершу запустіть: python main.py run")
        return 1
    golden = load_golden()
    metrics = []
    for path in paths:
        m = evaluate_run(load_results(path), golden)
        print(f"\n{path.name}")
        print_summary(m)
        metrics.append(m)
    write_report_tables(metrics, results_dir)
    print(f"\nТаблиці для звіту: {(results_dir / 'metrics.md').relative_to(ROOT)}, {(results_dir / 'metrics.csv').relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Release Intelligence Assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="прогнати extraction і зберегти результати в results/")
    run.add_argument("--models", help="ключі з config/models.yaml через кому, напр. provider,local")
    run.add_argument("--sampling", help="конфіги семплінгу через кому, напр. A,B")
    run.add_argument("--prompt", help="версія промпту, напр. extract_defect/v1 (за замовчуванням — з конфігу)")
    run.add_argument("--limit", type=int, help="обробити лише перші N документів")
    ev = sub.add_parser("eval", help="порахувати метрики для results/*.jsonl і зберегти metrics.md / metrics.csv")
    ev.add_argument("files", nargs="*", help="конкретні файли результатів (за замовчуванням — усі)")
    args = parser.parse_args()

    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")  # кирилиця в консолі Windows
    config = load_config()
    return cmd_run(args, config) if args.command == "run" else cmd_eval(args, config)


if __name__ == "__main__":
    sys.exit(main())
