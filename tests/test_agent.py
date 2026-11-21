"""Агент без мережі: скриптована «модель» перевіряє запобіжники циклу, а не якість LLM."""

import json

import pytest

from src.agent.faults import break_schema, parse_faults
from src.agent.loop import Agent, Limits
from src.agent.tools import ToolContext, load_tools
from src.extraction.prompts import load_prompt
from src.llm import ChatResult, SamplingParams, ToolCall
from src.tracker.service import TrackerService, idempotency_key

PRICE = {"input": 0.15, "output": 0.60}


class FakeLLM:
    """Відповідає за сценарієм: список ChatResult або функцій (messages, tool_choice) → ChatResult."""

    name = "fake"

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def chat(self, messages, tools, params, tool_choice="auto"):
        self.calls.append({"messages": [dict(m) for m in messages], "tool_choice": tool_choice})
        step = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        return step(messages, tool_choice) if callable(step) else step


def call(name, args, cid="c1"):
    return ChatResult("", [ToolCall(cid, name, json.dumps(args) if isinstance(args, dict) else args)], 100, 20, 1)


def final(text="Готово."):
    return ChatResult(text, [], 100, 20, 1)


def make_agent(tmp_path, script, confirm=None, faults=None, **limits):
    tracker = TrackerService(tickets_path=tmp_path / "tickets.json")
    tools, _ = load_tools("v2")
    lim = Limits(**{"backoff_s": 0.01, "tool_timeout_s": 1, **limits})
    agent = Agent(FakeLLM(script), tools, ToolContext(tracker=tracker), load_prompt("agent_system/v2"), lim,
                  SamplingParams(), PRICE, confirm=confirm, faults=faults)
    return agent, tracker


def tool_messages(agent):
    return [m["content"] for m in agent.llm.calls[-1]["messages"] if m["role"] == "tool"]


def test_happy_path_tool_then_answer(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"}), final("Випущено 2026-08-25 [tracker]")])
    res = agent.run("Коли вийшов 1.5.2?")
    assert res.status == "answered" and res.stop_reason == "answered" and res.steps == 2
    assert '"release_date": "2026-08-25"' in tool_messages(agent)[0]


def test_invalid_args_returned_to_model_and_fixed(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5"}), call("get_release", {"version": "1.5.0"}, "c2"),
                                     final()])
    res = agent.run("Реліз 1.5?")
    assert [c["outcome"] for c in res.tool_calls] == ["INVALID_ARGUMENTS", "ok"]
    assert res.status == "answered"


@pytest.mark.parametrize("raw", ["{не json", json.dumps({"version": "1.5.2", "extra": 1})])
def test_broken_json_and_extra_fields_are_invalid_arguments(tmp_path, raw):
    agent, _ = make_agent(tmp_path, [call("get_release", raw), final()])
    res = agent.run("x")
    assert res.tool_calls[0]["outcome"] == "INVALID_ARGUMENTS"


def test_unknown_tool_and_tool_exception_do_not_crash(tmp_path):
    agent, tracker = make_agent(tmp_path, [call("drop_database", {}), call("list_defects", {}, "c2"), final()])
    tracker.list_defects = lambda *a: 1 / 0
    res = agent.run("x")
    assert [c["outcome"] for c in res.tool_calls] == ["UNKNOWN_TOOL", "TOOL_ERROR"]
    assert res.status == "answered"


def test_persistent_503_retries_safe_call_then_unavailable(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"}), final("Сервіс недоступний")],
                          faults="503:get_release", tool_retries=2)
    res = agent.run("x")
    assert res.tool_calls[0]["attempts"] == 3 and res.tool_calls[0]["outcome"] == "SERVICE_UNAVAILABLE"
    assert tool_messages(agent)[0].startswith("SERVICE_UNAVAILABLE")


def test_single_503_recovers_with_backoff(tmp_path):
    agent, _ = make_agent(tmp_path, [call("list_defects", {"version": "1.5.2"}), final()], faults="503x1:list_defects")
    res = agent.run("x")
    assert res.tool_calls[0]["attempts"] == 2 and res.tool_calls[0]["outcome"] == "ok"


def test_timeout_is_cut_by_tool_timeout(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"}), final()], faults="timeout:get_release",
                          tool_timeout_s=0.2, tool_retries=0)
    res = agent.run("x")
    assert res.tool_calls[0]["outcome"] == "SERVICE_UNAVAILABLE"
    assert any(e.get("status") == "timeout" for e in res.trace)


def test_changed_api_format_is_schema_error_not_silent_none(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"}), final()], faults="schema:get_release")
    res = agent.run("x")
    assert res.tool_calls[0]["outcome"] == "SCHEMA_ERROR"
    assert "release_date" in tool_messages(agent)[0] and "2026-08-25" not in tool_messages(agent)[0]


def test_access_denied_for_other_team(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_defect", {"defect_id": "DEF-111"}), final()])
    res = agent.run("DEF-111?")
    assert res.tool_calls[0]["outcome"] == "ACCESS_DENIED"
    assert "конвертац" not in tool_messages(agent)[0]


TICKET = {"title": "Нагадування не надходить", "version": "1.5.2", "severity": "high", "description": "Approval Flow v2"}
Q_TICKET = "Створи тікет: у 1.5.2 нагадування не надходить, severity high"


def test_side_effect_requires_human_confirmation(tmp_path):
    asked = []
    agent, tracker = make_agent(tmp_path, [call("create_ticket", TICKET), final()],
                                confirm=lambda tool, args: asked.append(tool) or False)
    res = agent.run(Q_TICKET)
    assert asked == ["create_ticket"] and res.tool_calls[0]["outcome"] == "DECLINED"
    assert tracker.tickets() == [] and res.side_effects == []


def test_side_effect_without_confirm_callback_is_never_executed(tmp_path):
    agent, tracker = make_agent(tmp_path, [call("create_ticket", TICKET), final()], confirm=None)
    agent.run(Q_TICKET)
    assert tracker.tickets() == []


def test_side_effect_approved_creates_one_ticket(tmp_path):
    agent, tracker = make_agent(tmp_path, [call("create_ticket", TICKET), final()], confirm=lambda t, a: True)
    res = agent.run(Q_TICKET)
    assert len(tracker.tickets()) == 1 and res.side_effects[0]["result"]["status"] == "created"


def test_lost_response_retry_does_not_duplicate(tmp_path):
    agent, tracker = make_agent(tmp_path, [call("create_ticket", TICKET), call("create_ticket", TICKET, "c2"), final()],
                                confirm=lambda t, a: True, faults="lost_responsex1:create_ticket")
    res = agent.run(Q_TICKET)
    assert len(tracker.tickets()) == 1
    # повтор у циклі знайшов тікет, створений першою спробою, — для користувача це «створено», а не «вже існує»
    assert res.side_effects[0]["result"]["status"] == "created" and res.tool_calls[0]["attempts"] == 2


def test_version_not_named_by_user_is_not_guessed(tmp_path):
    asked = []
    agent, tracker = make_agent(tmp_path, [call("create_ticket", TICKET), final("Яка версія?")],
                                confirm=lambda t, a: asked.append(t) or True)
    res = agent.run("Заведи баг: нагадування не надходить, severity high")
    assert res.tool_calls[0]["outcome"] == "MISSING_INFO" and asked == [] and tracker.tickets() == []


def test_max_steps_forces_final_answer_without_tools(tmp_path):
    n = iter(range(100))
    agent, _ = make_agent(tmp_path, [lambda m, tc: final("Частковий результат: …") if tc == "none"
                                     else call("list_defects", {"severity": ["critical", "high", "medium", "low"][next(n) % 4]})],
                          max_steps=4, max_same_call=10)
    res = agent.run("перевір усе")
    assert res.stop_reason == "max_steps" and res.status == "partial" and res.steps == 4
    assert agent.llm.calls[-1]["tool_choice"] == "none"


def test_repeated_identical_call_is_blocked(tmp_path):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"})] * 3 + [final()], max_same_call=2)
    res = agent.run("x")
    assert [c["outcome"] for c in res.tool_calls] == ["ok", "ok", "REPEATED_CALL"]


def test_budget_usd_stops_with_partial_result(tmp_path):
    expensive = ChatResult("", [ToolCall("c", "list_defects", "{}")], 50_000, 0, 1)   # $0.0075 за крок
    agent, _ = make_agent(tmp_path, [lambda m, tc: final("Частковий результат") if tc == "none" else expensive],
                          max_cost_usd=0.01, max_tokens_total=10**7, max_same_call=10)
    res = agent.run("x")
    assert res.stop_reason == "budget_usd" and res.status == "partial" and res.steps == 2


def test_token_budget_counts_next_call_context(tmp_path):
    agent, tracker = make_agent(tmp_path, [call("list_defects", {}), final()], max_tokens_total=8000)
    one = tracker.list_defects()["defects"][0]
    tracker.list_defects = lambda *a: {"team": "procurement", "count": 300, "defects": [one] * 300}  # ~15k токенів
    res = agent.run("x")
    assert res.stop_reason == "budget_tokens" and res.steps == 1 and len(agent.llm.calls) == 1
    assert res.answer.startswith("Частковий результат")


def test_forced_final_with_empty_content_still_returns_partial_text(tmp_path):
    agent, _ = make_agent(tmp_path, [call("list_defects", {})], max_steps=1)
    res = agent.run("x")
    assert res.stop_reason == "max_steps" and res.answer.startswith("Частковий результат")


def test_citations_map_to_registered_sources(tmp_path):
    class Hit:
        def __init__(self, i):
            self.chunk = {"chunk_id": f"d#{i}", "doc_id": "contoso-runbook", "title": "Runbook", "section": f"Розділ {i}",
                          "text": "30 хвилин"}
            self.scores = {"rerank": 2.0 - i * 5}   # другий — нижче порогу «не знаю»

    class Retriever:
        def search(self, *a, **k):
            return [Hit(0), Hit(1)]

    agent, _ = make_agent(tmp_path, [call("search_docs", {"query": "severity critical"}), final("30 хвилин [S1]")])
    agent.base_ctx.retriever = Retriever()
    res = agent.run("x")
    assert list(res.sources) == ["S1"] and res.sources["S1"]["section"] == "Розділ 0"
    assert '"source_id": "S2"' not in tool_messages(agent)[0]


def test_tool_descriptions_live_outside_code():
    tools, version = load_tools("v2")
    assert version == "agent_tools/v2" and len(tools) >= 2
    for t in tools.values():
        schema = t.openai_schema()["function"]
        assert "ВИКЛИКАЙ" in schema["description"] or "ACCESS_DENIED" in schema["description"]
        assert all("description" in p for p in schema["parameters"]["properties"].values())


def test_faults_parsing_and_schema_break():
    f = parse_faults("503x1:list_defects,timeout,lost_responsex1:create_ticket")
    assert [(x.kind, x.tool, x.times) for x in f] == [("503", "list_defects", 1), ("timeout", None, None),
                                                       ("lost_response", "create_ticket", 1)]
    with pytest.raises(ValueError):
        parse_faults("boom")
    assert "releaseDate" in break_schema({"version": "1", "release_date": "x"})


def test_idempotency_key_ignores_case_and_spaces():
    assert idempotency_key("Нагадування  НЕ надходить", "1.5.2") == idempotency_key("нагадування не надходить", "1.5.2")
    assert idempotency_key("a", "1.5.2") != idempotency_key("a", "1.5.3")
