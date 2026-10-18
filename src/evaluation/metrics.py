"""Метрики кейсу 1: точність по полях на golden set, % валідних, latency p50/p95, вартість на 1000 документів.

Як оцінюється кожне поле (бал 0..1 на документ):
- is_defect, severity, release_version, is_regression — точний збіг (null == null теж збіг);
- environments, components.type — збіг множин;
- components.name — F1 з нечітким збігом назв;
- steps_to_reproduce — F1 з нечітким збігом кроків;
- expected_result, actual_result — обидва null, або покриття слів еталону ≥ 50%.
title не оцінюється: вільний текст, перевіряється вручну.
Документ зі статусом failed отримує 0 по всіх полях.
"""

import re
import statistics
from difflib import SequenceMatcher

FIELDS = [
    "is_defect", "components.type", "components.name", "environments", "severity",
    "release_version", "steps_to_reproduce", "expected_result", "actual_result", "is_regression",
]
NAME_THRESHOLD = 0.8
STEP_THRESHOLD = 0.6
TEXT_RECALL_THRESHOLD = 0.5


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def fuzzy_f1(predicted: list[str], expected: list[str], threshold: float) -> float:
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    unmatched = list(expected)
    hits = 0
    for p in predicted:
        best = max(unmatched, key=lambda e: _similar(p, e), default=None)
        if best is not None and _similar(p, best) >= threshold:
            unmatched.remove(best)
            hits += 1
    precision, recall = hits / len(predicted), hits / len(expected)
    return 0.0 if hits == 0 else 2 * precision * recall / (precision + recall)


def _words(s: str) -> set[str]:
    return {w for w in re.findall(r"\w+", s.lower()) if len(w) >= 3}


def text_score(predicted: str | None, expected: str | None) -> float:
    if predicted is None or expected is None:
        return float(predicted is None and expected is None)
    words = _words(expected)
    if not words:
        return 1.0
    return float(len(words & _words(predicted)) / len(words) >= TEXT_RECALL_THRESHOLD)


def _version(v: str | None) -> str | None:
    return v.strip().lower().lstrip("v") if v else None


def score_document(predicted: dict | None, expected: dict) -> dict[str, float]:
    if predicted is None:
        return dict.fromkeys(FIELDS, 0.0)
    p_names = [c["name"] for c in predicted["components"] if c["name"]]
    e_names = [c["name"] for c in expected["components"] if c["name"]]
    return {
        "is_defect": float(predicted["is_defect"] == expected["is_defect"]),
        "components.type": float({c["type"] for c in predicted["components"]} == {c["type"] for c in expected["components"]}),
        "components.name": fuzzy_f1(p_names, e_names, NAME_THRESHOLD),
        "environments": float(set(predicted["environments"]) == set(expected["environments"])),
        "severity": float(predicted["severity"] == expected["severity"]),
        "release_version": float(_version(predicted["release_version"]) == _version(expected["release_version"])),
        "steps_to_reproduce": fuzzy_f1(predicted["steps_to_reproduce"], expected["steps_to_reproduce"], STEP_THRESHOLD),
        "expected_result": text_score(predicted["expected_result"], expected["expected_result"]),
        "actual_result": text_score(predicted["actual_result"], expected["actual_result"]),
        "is_regression": float(predicted["is_regression"] == expected["is_regression"]),
    }


def percentile(values: list[int], p: int) -> int:
    if len(values) < 2:
        return values[0] if values else 0
    return int(statistics.quantiles(values, n=100, method="inclusive")[p - 1])


def evaluate_run(records: list[dict], golden: dict[str, dict]) -> dict:
    """Зведені метрики одного прогону (один файл results/*.jsonl)."""
    n = len(records)
    statuses = {s: sum(r["status"] == s for r in records) for s in ("ok", "repaired", "failed")}
    latencies = [r["latency_ms"] for r in records if r["status"] != "failed"]
    costs = [r["cost_usd"] for r in records]
    first = records[0]

    scored = [score_document(r["output"], golden[r["doc_id"]]) for r in records if r["doc_id"] in golden]
    field_acc = {f: statistics.mean(s[f] for s in scored) for f in FIELDS} if scored else {}

    return {
        "run_id": first["run_id"],
        "model": first["model"],
        "prompt": first["prompt_version"],
        "sampling": first["sampling"]["name"],
        "docs": n,
        "valid_pct": (statuses["ok"] + statuses["repaired"]) / n * 100,
        "ok": statuses["ok"],
        "repaired": statuses["repaired"],
        "failed": statuses["failed"],
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "cost_per_1000_usd": None if None in costs else sum(costs) / n * 1000,
        "golden_docs": len(scored),
        "field_accuracy": statistics.mean(field_acc.values()) if field_acc else None,
        "fields": field_acc,
    }
