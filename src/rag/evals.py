"""Evals відповідей RAG: тестсет → відповіді → оцінки → метрики → поріг для CI.

Детерміновані scoring-функції (без LLM):
- refusal_ok     — «не знаю» там, де відповіді немає, і відповідь там, де вона є;
- source_hit     — серед процитованих джерел є очікуваний документ;
- key_facts      — частка ключових фактів еталона у відповіді (альтернативи через «|»);
- no_forbidden   — у відповіді немає заборонених фактів (напр. значення із застарілої версії);
- citations_ok   — кожне твердження має джерело.
LLM-as-a-judge (інша модель, ніж генератор):
- judge          — correct / partial / incorrect відносно еталона (1 / 0.5 / 0); калібрується на ручній розмітці;
- faithfulness   — частка тверджень, підтверджених процитованими джерелами.
"""

import json
import statistics
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.config import ROOT, load_config
from src.evaluation.metrics import percentile
from src.extraction.pipeline import cost_usd
from src.extraction.prompts import load_prompt
from src.llm import LLMError, SamplingParams, make_client
from src.rag.answer import RagPipeline

RESULTS = ROOT / "evals" / "results"
CALIBRATION = ROOT / "evals" / "calibration" / "hand_grades.json"
VERDICT_SCORE = {"correct": 1.0, "partial": 0.5, "incorrect": 0.0}


class JudgeVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: Literal["correct", "partial", "incorrect"]
    reason: str = Field(description="Коротко (до 25 слів): чого бракує або що не так")


class ClaimCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    index: int
    supported: bool
    reason: str = Field(description="До 15 слів")


class FaithfulnessCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claims: list[ClaimCheck]


# ---------- детерміновані оцінки ----------

def has_fact(text: str, fact: str) -> bool:
    return any(alt.strip().lower() in text.lower() for alt in fact.split("|"))


def deterministic_scores(item: dict, answer: dict) -> dict:
    answerable = item["category"] == "answerable"
    answered = answer["status"] == "answered"
    scores = {"refusal_ok": float(answered == answerable)}
    if answerable:
        cited_docs = {s["chunk_id"].split("#")[0] for s in answer["sources"] if s["id"] in answer["cited"]}
        scores["source_hit"] = float(bool(cited_docs & set(item["expected_sources"])))
        facts = item["key_facts"]
        scores["key_facts"] = sum(has_fact(answer["answer"], f) for f in facts) / len(facts) if facts else 1.0
        scores["no_forbidden"] = float(not any(has_fact(answer["answer"], f) for f in item["forbidden_facts"]))
    if answered:
        scores["citations_ok"] = float(bool(answer["claims"]) and all(c["sources"] for c in answer["claims"]))
    return scores


# ---------- LLM-as-a-judge ----------

class Judge:
    def __init__(self):
        models = load_config()
        self.model_cfg = models["models"]["judge"]
        self.client = make_client(self.model_cfg, models)
        self.correctness = load_prompt("rag_judge/v1")
        self.faithfulness = load_prompt("rag_faithfulness/v1")
        # 600 токенів обрізали JSON на відповідях з багатьма твердженнями → невалідна відповідь судді
        self.params = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=2000)
        self.tokens_in = self.tokens_out = 0

    def _call(self, messages, schema):
        for _ in range(2):  # одна повторна спроба, якщо JSON невалідний
            r = self.client.generate_structured(messages, schema, self.params)
            self.tokens_in += r.tokens_in
            self.tokens_out += r.tokens_out
            try:
                return schema.model_validate_json(r.raw_text)
            except ValidationError:
                continue
        raise LLMError("суддя повернув невалідний JSON двічі")

    def judge(self, question: str, reference: str, answer: str) -> JudgeVerdict:
        return self._call(self.correctness.messages_for(question=question, reference=reference, answer=answer), JudgeVerdict)

    def faithful(self, answer: dict) -> FaithfulnessCheck:
        by_id = {s["id"]: s for s in answer["sources"]}
        sources = "\n\n".join(f"[{sid}] {by_id[sid]['title']} › {by_id[sid]['section']}\n{by_id[sid]['text']}"
                              for sid in answer["cited"])
        claims = "\n".join(f"{i} · {c['statement']} · {', '.join(c['sources'])}" for i, c in enumerate(answer["claims"], 1))
        return self._call(self.faithfulness.messages_for(sources=sources, claims=claims), FaithfulnessCheck)

    @property
    def cost(self) -> float:
        return cost_usd(self.tokens_in, self.tokens_out, self.model_cfg["price_per_1m_tokens"]) or 0.0


# ---------- прогін ----------

def load_testset(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_item(item: dict, answer: dict, judge: Judge) -> dict:
    scores = deterministic_scores(item, answer)
    extra, errors = {}, []
    if item["category"] == "answerable":
        if answer["status"] == "answered":
            try:
                v = judge.judge(item["question"], item["expected_answer"], answer["answer"])
                scores["judge"] = VERDICT_SCORE[v.verdict]
                extra["judge"] = v.model_dump()
            except LLMError as e:  # збій судді не валить прогін; оцінка відсутня й видна в звіті
                errors.append(f"judge: {e}")
        else:
            scores["judge"] = 0.0  # відмовився відповідати, хоча відповідь є
            extra["judge"] = {"verdict": "incorrect", "reason": f"status {answer['status']} — відповідь є в документах"}
    if answer["status"] == "answered" and answer["claims"]:
        try:
            f = judge.faithful(answer)
            scores["faithfulness"] = sum(c.supported for c in f.claims) / max(len(f.claims), 1)
            extra["faithfulness"] = [c.model_dump() for c in f.claims]
        except LLMError as e:
            errors.append(f"faithfulness: {e}")
    return {"scores": scores, **extra, **({"judge_errors": errors} if errors else {})}


def mean_of(rows: list[dict], key: str) -> float | None:
    values = [r["scores"][key] for r in rows if key in r["scores"]]
    return statistics.mean(values) if values else None


def summarize(rows: list[dict], judge_cost: float) -> dict:
    answerable = [r for r in rows if r["category"] == "answerable"]
    unanswerable = [r for r in rows if r["category"] == "unanswerable"]
    latencies = [r["answer"]["meta"]["latency_ms"] for r in rows]
    costs = [r["answer"]["meta"].get("cost_usd") or 0.0 for r in rows]
    return {
        "questions": len(rows),
        "refusal_accuracy": mean_of(rows, "refusal_ok"),
        "correct_refusals": mean_of(unanswerable, "refusal_ok"),        # «не знаю» на питаннях без відповіді
        "false_refusals": 1 - (mean_of(answerable, "refusal_ok") or 0),  # «не знаю», хоча відповідь є
        "source_hit": mean_of(answerable, "source_hit"),
        "key_facts": mean_of(answerable, "key_facts"),
        "no_forbidden": mean_of(answerable, "no_forbidden"),
        "citations_ok": mean_of(rows, "citations_ok"),
        "judge_correctness": mean_of(answerable, "judge"),
        "faithfulness": mean_of(rows, "faithfulness"),
        "failed": sum(r["answer"]["status"] == "failed" for r in rows),
        "judge_errors": sum(bool(r.get("judge_errors")) for r in rows),
        "latency_p50_ms": percentile(latencies, 50),
        "latency_p95_ms": percentile(latencies, 95),
        "cost_per_1000_questions_usd": statistics.mean(costs) * 1000,
        "judge_cost_usd": judge_cost,
    }


def check_thresholds(summary: dict, thresholds: dict) -> list[str]:
    failures = []
    for key, limit in thresholds.items():
        if key == "failed_max":
            if summary["failed"] > limit:
                failures.append(f"failed = {summary['failed']} > {limit}")
        elif summary.get(key) is None or summary[key] < limit:
            failures.append(f"{key} = {summary.get(key)} < {limit}")
    return failures


def run_rag_eval(rag_cfg: dict) -> tuple[dict, list[str]]:
    ev = rag_cfg["evals"]
    testset = load_testset(ROOT / ev["testset"])
    pipeline, judge = RagPipeline(rag_cfg), Judge()
    rows = []
    for item in testset:
        answer = pipeline.ask(item["question"]).to_dict()
        row = {"id": item["id"], "category": item["category"], "trap": item["trap"], "question": item["question"],
               "expected_answer": item["expected_answer"], "answer": answer, **evaluate_item(item, answer, judge)}
        rows.append(row)
        s = row["scores"]
        print(f"  {item['id']} [{answer['status']:9}] " + " ".join(f"{k}={v:.2f}" for k, v in s.items()))
    pipeline.retriever.close()

    summary = summarize(rows, judge.cost)
    summary.update(prompt=pipeline.prompt.id, prompt_sha=pipeline.prompt.sha, model=pipeline.client.name, judge=judge.client.name)
    failures = check_thresholds(summary, ev["thresholds"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "rag_answers.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (RESULTS / "rag_metrics.json").write_text(json.dumps({"summary": summary, "thresholds": ev["thresholds"],
                                                          "failures": failures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "rag_metrics.md").write_text(report(rows, summary, ev["thresholds"], failures), encoding="utf-8")
    write_grading_sheet(rows)
    return summary, failures


def fmt(v) -> str:
    return "—" if v is None else f"{v:.2f}"


def report(rows: list[dict], summary: dict, thresholds: dict, failures: list[str]) -> str:
    s = summary
    lines = [
        "# Evals відповідей RAG", "",
        f"Модель: `{s['model']}` · промпт: `{s['prompt']}` (sha {s['prompt_sha']}) · суддя: `{s['judge']}` · питань: {s['questions']}", "",
        "| Метрика | Значення | Поріг CI |", "|---|---|---|",
    ]
    names = {
        "refusal_accuracy": "«не знаю» там, де треба (усі питання)", "correct_refusals": "правильні відмови (питання без відповіді)",
        "false_refusals": "хибні відмови (відповідь є, а сказав «не знаю»)", "source_hit": "правильне джерело в цитатах",
        "key_facts": "ключові факти у відповіді", "no_forbidden": "без фактів зі застарілих версій", "citations_ok": "кожне твердження з джерелом",
        "judge_correctness": "LLM-суддя: правильність", "faithfulness": "faithfulness (твердження підтверджені джерелами)",
    }
    for key, name in names.items():
        lines.append(f"| {name} | {fmt(s[key])} | {thresholds.get(key, '—')} |")
    lines += [f"| failed | {s['failed']} | ≤ {thresholds.get('failed_max', '—')} |",
              f"| збої судді (оцінку не отримано) | {s['judge_errors']} | — |",
              f"| latency p50 / p95 | {s['latency_p50_ms']} / {s['latency_p95_ms']} мс | — |",
              f"| вартість відповідей на 1000 питань | ${s['cost_per_1000_questions_usd']:.2f} | — |",
              f"| вартість судді за прогін | ${s['judge_cost_usd']:.4f} | — |", "",
              "**Результат CI:** " + ("✅ усі пороги пройдено" if not failures else "❌ " + "; ".join(failures)), "",
              "## По питаннях", "",
              "| ID | Тип | Статус | refusal | джерело | факти | суддя | faithful | Відповідь |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        sc = r["scores"]
        lines.append(f"| {r['id']} | {r['category']} · {r['trap']} | {r['answer']['status']} | {fmt(sc.get('refusal_ok'))} | "
                     f"{fmt(sc.get('source_hit'))} | {fmt(sc.get('key_facts'))} | {fmt(sc.get('judge'))} | {fmt(sc.get('faithfulness'))} | "
                     f"{r['answer']['answer'][:110].replace('|', '/').replace(chr(10), ' ')} |")
    return "\n".join(lines) + "\n"


# ---------- калібрування судді на ручній розмітці ----------

def write_grading_sheet(rows: list[dict]) -> None:
    """Аркуш для ручної оцінки: відповіді БЕЗ вердикту судді, щоб він не впливав на людину. Не перезаписує вже заповнене."""
    if CALIBRATION.exists():
        return
    items = [{"id": r["id"], "question": r["question"], "reference": r["expected_answer"], "answer": r["answer"]["answer"],
              "human_verdict": None, "human_note": ""}
             for r in rows if r["category"] == "answerable" and r["answer"]["status"] == "answered"]
    CALIBRATION.parent.mkdir(parents=True, exist_ok=True)
    CALIBRATION.write_text(json.dumps({"instructions": "human_verdict: correct | partial | incorrect — за тими ж правилами, що й суддя "
                                       "(prompts/rag_judge/v1.md). Вердикт судді тут навмисно не показано.",
                                       "items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def calibrate() -> str:
    grades = json.loads(CALIBRATION.read_text(encoding="utf-8"))["items"]
    judged = {json.loads(line)["id"]: json.loads(line) for line in (RESULTS / "rag_answers.jsonl").read_text(encoding="utf-8").splitlines()}
    # пара рахується, лише якщо людина оцінювала ту саму відповідь, що й суддя (після нового прогону відповіді змінюються)
    stale = [g["id"] for g in grades if g["id"] in judged and g["answer"] != judged[g["id"]]["answer"]["answer"]]
    pairs = [(g["human_verdict"], judged[g["id"]]["judge"]["verdict"], g) for g in grades
             if g["human_verdict"] in VERDICT_SCORE and g["id"] in judged and "judge" in judged[g["id"]] and g["id"] not in stale]
    if not pairs:
        raise ValueError(f"Немає заповнених human_verdict у {CALIBRATION.relative_to(ROOT)}")
    exact = sum(h == j for h, j, _ in pairs) / len(pairs)
    passfail = sum((h == "correct") == (j == "correct") for h, j, _ in pairs) / len(pairs)
    labels = list(VERDICT_SCORE)
    p_o = exact
    p_e = sum((sum(h == l for h, _, _ in pairs) / len(pairs)) * (sum(j == l for _, j, _ in pairs) / len(pairs)) for l in labels)
    kappa = (p_o - p_e) / (1 - p_e) if p_e < 1 else 1.0
    lines = ["# Калібрування LLM-судді на ручній розмітці", "",
             f"Оцінено вручну: **{len(pairs)}** відповідей (`evals/calibration/hand_grades.json`), суддя — `rag_judge/v1`.", "",
             "| Метрика | Значення |", "|---|---|",
             f"| Точний збіг вердикту (correct / partial / incorrect) | {exact:.0%} |",
             f"| Збіг «правильно / неправильно» (correct vs решта) | {passfail:.0%} |",
             f"| Cohen's κ | {kappa:.2f} |", "",
             *([f"⚠ Не враховано (відповідь змінилась після ручної оцінки): {', '.join(stale)}", ""] if stale else []),
             "## Розбіжності", "", "| ID | Людина | Суддя | Пояснення судді | Примітка людини |", "|---|---|---|---|---|"]
    for h, j, g in pairs:
        if h != j:
            lines.append(f"| {g['id']} | {h} | {j} | {judged[g['id']]['judge']['reason'][:120]} | {g.get('human_note', '')} |")
    text = "\n".join(lines) + "\n"
    (RESULTS / "judge_calibration.md").write_text(text, encoding="utf-8")
    return text
