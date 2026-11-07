"""Вимірювання якості пошуку: recall@k і MRR@10 на питаннях з відомим правильним чанком.

Правильний чанк задається не chunk_id, а парою (doc_id, фраза, яку чанк містить) — так та сама розмітка
працює для будь-якої chunking-стратегії й не ламається при перенарізанні.
"""

import json
from pathlib import Path

from src.config import ROOT
from src.rag.search import Retriever

# (стратегія chunking, промпти embedding-моделі, режими пошуку)
CONFIGS = [
    ("structure", True, ["vector", "bm25", "hybrid", "hybrid_rerank"]),
    ("structure", False, ["vector"]),
    ("fixed", True, ["vector", "hybrid", "hybrid_rerank"]),
]


def load_questions(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_relevant(chunk: dict, question: dict) -> bool:
    return any(chunk["doc_id"] == r["doc_id"] and r["contains"].lower() in chunk["text"].lower()
               for r in question["relevant"])


def first_relevant_rank(hits, question: dict) -> int | None:
    return next((rank for rank, h in enumerate(hits, 1) if is_relevant(h.chunk, question)), None)


def evaluate(cfg: dict) -> list[dict]:
    rc = cfg["retrieval_eval"]
    questions = load_questions(ROOT / rc["questions"])
    max_k = max(rc["ks"])
    results = []
    for strategy, prompts, modes in CONFIGS:
        retriever = Retriever(cfg, strategy=strategy, prompts=prompts)
        for mode in modes:
            ranks = {q["id"]: first_relevant_rank(retriever.search(q["question"], mode=mode, k=max_k), q) for q in questions}
            row = {
                "strategy": strategy, "prompts": prompts, "mode": mode, "questions": len(questions),
                **{f"recall@{k}": sum(r is not None and r <= k for r in ranks.values()) / len(questions) for k in rc["ks"]},
                "mrr@10": sum(1 / r for r in ranks.values() if r) / len(questions),
                "ranks": ranks,
            }
            results.append(row)
            print(f"  {strategy:9} prompts={prompts!s:5} {mode:13} recall@1 {row['recall@1']:.2f} "
                  f"@5 {row['recall@5']:.2f} @10 {row['recall@10']:.2f} MRR {row['mrr@10']:.2f}")
        retriever.close()
    return results


def report(results: list[dict], questions: list[dict], ks: list[int]) -> str:
    lines = ["# Якість пошуку (retrieval)", "",
             f"{len(questions)} питань з відомим правильним чанком — `evals/retrieval_questions.jsonl`. "
             "Hit = у top-k є чанк потрібного документа, що містить ключову фразу.", "",
             "| Chunking | Промпти embeddings | Пошук | " + " | ".join(f"recall@{k}" for k in ks) + " | MRR@10 |",
             "|---|---|---|" + "---|" * len(ks) + "---|"]
    for r in results:
        lines.append(f"| {r['strategy']} | {'так' if r['prompts'] else 'ні'} | {r['mode']} | "
                     + " | ".join(f"{r[f'recall@{k}']:.2f}" for k in ks) + f" | {r['mrr@10']:.2f} |")
    lines += ["", "## Ранг першого правильного чанка по питаннях (— = не знайдено в top-10)", "",
              "| Питання | Тип | " + " | ".join(f"{r['strategy'][:6]}·{r['mode']}{'' if r['prompts'] else '·plain'}" for r in results) + " |",
              "|---|---|" + "---|" * len(results)]
    for q in questions:
        lines.append(f"| {q['id']} {q['question'][:60]} | {q['type']} | "
                     + " | ".join(str(r["ranks"][q["id"]] or "—") for r in results) + " |")
    return "\n".join(lines) + "\n"


def run_retrieval_eval(cfg: dict) -> Path:
    results = evaluate(cfg)
    questions = load_questions(ROOT / cfg["retrieval_eval"]["questions"])
    out_dir = ROOT / "evals" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "retrieval_metrics.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    path = out_dir / "retrieval_metrics.md"
    path.write_text(report(results, questions, cfg["retrieval_eval"]["ks"]), encoding="utf-8")
    return path
