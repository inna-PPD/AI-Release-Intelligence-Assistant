import json

from src.config import ROOT
from src.rag.evals import check_thresholds, deterministic_scores, has_fact, summarize


def answer(status="answered", text="Потрібен pac CLI 1.44 [S1]", cited=("S1",), doc="contoso-install-guide-1.5", claims=None):
    return {"status": status, "answer": text, "cited": list(cited),
            "sources": [{"id": "S1", "chunk_id": f"{doc}#000"}, {"id": "S2", "chunk_id": "other-doc#001"}],
            "claims": claims if claims is not None else ([{"statement": "1.44", "sources": ["S1"]}] if status == "answered" else []),
            "meta": {"latency_ms": 100, "cost_usd": 0.0004}}


ITEM = {"category": "answerable", "key_facts": ["1.44", "ContosoCore_Invoices"], "forbidden_facts": ["1.32"],
        "expected_sources": ["contoso-install-guide-1.5"]}


def test_has_fact_alternatives():
    assert has_fact("виходить щомісяця", "monthly|щомісяця")
    assert not has_fact("раз на рік", "monthly|щомісяця")


def test_deterministic_scores_answerable():
    s = deterministic_scores(ITEM, answer())
    assert s == {"refusal_ok": 1.0, "source_hit": 1.0, "key_facts": 0.5, "no_forbidden": 1.0, "citations_ok": 1.0}
    wrong_doc = deterministic_scores(ITEM, answer(doc="contoso-install-guide-1.4", text="pac CLI 1.32 [S1]"))
    assert wrong_doc["source_hit"] == 0.0 and wrong_doc["no_forbidden"] == 0.0 and wrong_doc["key_facts"] == 0.0


def test_refusal_scores():
    unanswerable = {"category": "unanswerable", "key_facts": [], "forbidden_facts": [], "expected_sources": []}
    assert deterministic_scores(unanswerable, answer(status="not_found", text="У документах цього немає."))["refusal_ok"] == 1.0
    assert deterministic_scores(unanswerable, answer())["refusal_ok"] == 0.0           # вигадав відповідь
    false_refusal = deterministic_scores(ITEM, answer(status="not_found", text="У документах цього немає.", cited=()))
    assert false_refusal["refusal_ok"] == 0.0 and false_refusal["source_hit"] == 0.0


def test_summary_and_thresholds():
    rows = [
        {"category": "answerable", "scores": {"refusal_ok": 1.0, "source_hit": 1.0, "key_facts": 1.0, "judge": 1.0}, "answer": answer()},
        {"category": "unanswerable", "scores": {"refusal_ok": 0.0}, "answer": answer()},
    ]
    s = summarize(rows, judge_cost=0.01)
    assert s["refusal_accuracy"] == 0.5 and s["correct_refusals"] == 0.0 and s["false_refusals"] == 0.0
    assert round(s["cost_per_1000_questions_usd"], 2) == 0.40
    assert check_thresholds(s, {"refusal_accuracy": 0.8, "source_hit": 0.8, "failed_max": 0}) == ["refusal_accuracy = 0.5 < 0.8"]


def test_testset_is_valid():
    items = [json.loads(line) for line in (ROOT / "evals" / "testset.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(items) >= 20 and len({i["id"] for i in items}) == len(items)
    assert sum(i["category"] == "unanswerable" for i in items) >= 3
    assert {"version", "similar"} <= {i["trap"] for i in items}
    for i in items:
        if i["category"] == "answerable":
            assert i["key_facts"] and i["expected_sources"], i["id"]
