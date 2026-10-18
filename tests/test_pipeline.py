import json

import pytest
from pydantic import ValidationError

from src.extraction.pipeline import cost_usd, extract_one
from src.extraction.prompts import load_prompt
from src.llm import LLMError, LLMResult, SamplingParams
from src.schema import DefectReport

VALID = {
    "title": "Не зберігається заявка",
    "is_defect": True,
    "components": [{"type": "canvas_app", "name": "Заявки на закупівлю"}],
    "environments": ["uat"],
    "severity": "high",
    "release_version": "1.4.2",
    "steps_to_reproduce": ["Відкрити застосунок", "Натиснути Save"],
    "expected_result": "Заявка створюється",
    "actual_result": "Something went wrong",
    "is_regression": None,
}
INVALID = {**VALID, "environments": ["staging"]}
DOC = {"id": "t-1", "text": "flow впав на {UAT}"}


class FakeClient:
    """Повертає заздалегідь задані відповіді й запам'ятовує отримані повідомлення."""

    name = "fake/model"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate_structured(self, messages, schema, params):
        self.calls.append(messages)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return LLMResult(raw_text=json.dumps(reply), tokens_in=100, tokens_out=50, latency_ms=10, model=self.name)


@pytest.fixture
def prompt():
    return load_prompt("extract_defect/v1")


def test_schema_rejects_unknown_enum():
    DefectReport.model_validate(VALID)
    with pytest.raises(ValidationError):
        DefectReport.model_validate(INVALID)


def test_prompt_versions_have_distinct_hashes():
    v1, v2 = load_prompt("extract_defect/v1"), load_prompt("extract_defect/v2")
    assert len(v1.sha) == 12 and v1.sha != v2.sha
    assert load_prompt("extract_defect/v1").sha == v1.sha  # стабільний між запусками


def test_prompt_keeps_braces_in_text(prompt):
    messages = prompt.messages(DOC["text"])
    assert "flow впав на {UAT}" in messages[1]["content"]


def test_ok_on_first_attempt(prompt):
    part = extract_one(FakeClient([VALID]), prompt, DOC, DefectReport, SamplingParams(), repair_attempts=1)
    assert part["status"] == "ok" and part["attempts"] == 1
    assert part["output"]["environments"] == ["uat"]


def test_repaired_after_invalid(prompt):
    client = FakeClient([INVALID, VALID])
    part = extract_one(client, prompt, DOC, DefectReport, SamplingParams(), repair_attempts=1)
    assert part["status"] == "repaired" and part["attempts"] == 2
    assert part["tokens_in"] == 200  # токени обох спроб враховано
    assert part["error"].startswith("repaired after validation: 1 errors, first: environments.0")
    assert "не пройшла валідацію" in client.calls[1][-1]["content"]


def test_failed_after_repair_exhausted(prompt):
    part = extract_one(FakeClient([INVALID, INVALID]), prompt, DOC, DefectReport, SamplingParams(), repair_attempts=1)
    assert part["status"] == "failed" and part["output"] is None
    assert part["error"].startswith("validation")


def test_failed_on_llm_error(prompt):
    part = extract_one(FakeClient([LLMError("timeout")]), prompt, DOC, DefectReport, SamplingParams(), repair_attempts=1)
    assert part["status"] == "failed" and part["error"] == "llm: timeout"


def test_cost():
    assert cost_usd(1_000_000, 1_000_000, {"input": 0.15, "output": 0.60}) == pytest.approx(0.75)
    assert cost_usd(10, 10, {"input": None, "output": None}) is None
