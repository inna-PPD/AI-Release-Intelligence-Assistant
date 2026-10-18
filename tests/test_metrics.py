import copy
import json

from src.config import ROOT
from src.evaluation.metrics import FIELDS, evaluate_run, fuzzy_f1, score_document, text_score
from src.schema import DefectReport

GOLDEN = {
    row["id"]: row["expected"]
    for row in json.loads((ROOT / "data" / "golden" / "golden_set.json").read_text(encoding="utf-8"))
}


def test_golden_set_matches_schema():
    assert len(GOLDEN) == 10
    for expected in GOLDEN.values():
        DefectReport.model_validate(expected)


def test_perfect_prediction_scores_one():
    for expected in GOLDEN.values():
        assert all(v == 1.0 for v in score_document(copy.deepcopy(expected), expected).values())


def test_failed_document_scores_zero():
    assert set(score_document(None, GOLDEN["syn-001"]).values()) == {0.0}


def test_field_errors_are_detected():
    expected = GOLDEN["syn-010"]
    predicted = copy.deepcopy(expected)
    predicted["environments"] = ["uat"]             # пропущено test
    predicted["release_version"] = "v1.5.1"         # нормалізується до 1.5.1
    predicted["components"][0]["name"] = "Approval flow V2"  # нечіткий збіг назви
    scores = score_document(predicted, expected)
    assert scores["environments"] == 0.0
    assert scores["release_version"] == 1.0
    assert scores["components.name"] == 1.0


def test_fuzzy_and_text_helpers():
    assert fuzzy_f1([], [], 0.8) == 1.0
    assert fuzzy_f1(["a"], [], 0.8) == 0.0
    assert text_score(None, None) == 1.0
    assert text_score("щось", None) == 0.0
    assert text_score("Новий запис з тим самим номером інвойсу", "новий запис з тим самим номером") == 1.0


def test_evaluate_run_aggregates():
    records = [
        {"run_id": "r", "doc_id": "syn-001", "model": "m", "prompt_version": "p/v1", "sampling": {"name": "A"},
         "status": "ok", "latency_ms": 100, "cost_usd": 0.001, "output": GOLDEN["syn-001"]},
        {"run_id": "r", "doc_id": "syn-002", "model": "m", "prompt_version": "p/v1", "sampling": {"name": "A"},
         "status": "failed", "latency_ms": 0, "cost_usd": 0.0, "output": None},
    ]
    m = evaluate_run(records, GOLDEN)
    assert m["valid_pct"] == 50 and m["failed"] == 1
    assert m["golden_docs"] == 1 and m["field_accuracy"] == 1.0
    assert m["cost_per_1000_usd"] == 0.5
    assert set(m["fields"]) == set(FIELDS)
