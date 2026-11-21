"""MCP-сервер трекера: справжній підпроцес через stdio, без мережі й LLM."""

import json

import pytest

from src.agent.mcp_client import McpError, McpTracker
from src.agent.tools import ToolContext, load_tools
from src.tracker.service import AccessDenied, NotFound
from tests.test_agent import FakeLLM, call, final, make_agent

TOOLS = ["get_release", "list_defects", "get_defect"]


@pytest.fixture(scope="module")
def mcp():
    client = McpTracker("procurement", TOOLS)
    yield client
    client.close()


def test_server_exposes_only_read_tools(mcp):
    assert sorted(mcp.server_tools) == sorted(TOOLS)   # жодного create_ticket, SQL чи читання файлів


def test_input_schema_validates_formats(mcp):
    props = mcp.server_tools["get_release"]["properties"]
    assert props["version"]["pattern"] == r"^\d+\.\d+\.\d+$"


def test_read_release_and_defects(mcp):
    assert mcp.call("get_release", {"version": "1.5.2"})["release_date"] == "2026-08-25"
    out = mcp.call("list_defects", {"version": "1.5.2", "status": "open"})
    assert out["team"] == "procurement" and {d["id"] for d in out["defects"]} == {"DEF-107", "DEF-108", "DEF-109"}


def test_other_team_defect_is_access_denied(mcp):
    with pytest.raises(AccessDenied, match="finance"):
        mcp.call("get_defect", {"defect_id": "DEF-111"})


def test_other_team_defects_not_listed(mcp):
    ids = {d["id"] for d in mcp.call("list_defects", {})["defects"]}
    assert "DEF-111" not in ids and "DEF-112" not in ids


def test_not_found(mcp):
    with pytest.raises(NotFound):
        mcp.call("get_release", {"version": "9.9.9"})


@pytest.mark.parametrize("name,args", [
    ("get_release", {"version": "1.5"}),                          # формат версії
    ("get_release", {"version": "1.5.2", "path": "/etc/passwd"}),  # невідомий аргумент
    ("list_defects", {"team": "finance"}),                        # спроба обійти доступ аргументом
    ("get_defect", {"defect_id": "../../.env"}),                  # спроба шляху
])
def test_invalid_or_extra_arguments_rejected(mcp, name, args):
    with pytest.raises((ValueError, McpError)):
        mcp.call(name, args)


def test_unknown_tool(mcp):
    with pytest.raises(McpError, match="run_sql"):
        mcp.call("run_sql", {"q": "select 1"})


def test_agent_uses_mcp_and_explains_access_denied(tmp_path, mcp):
    agent, tracker = make_agent(tmp_path, [call("get_defect", {"defect_id": "DEF-111"}), final("Немає доступу")])
    agent.base_ctx.mcp = mcp
    tracker.get_defect = lambda *a: pytest.fail("агент мав піти в MCP, а не в локальний трекер")
    res = agent.run("DEF-111?")
    assert res.tool_calls[0]["outcome"] == "ACCESS_DENIED"
    assert json.dumps(res.trace, ensure_ascii=False).count("ACCESS_DENIED") >= 1


def test_faults_wrap_mcp_calls(tmp_path, mcp):
    agent, _ = make_agent(tmp_path, [call("get_release", {"version": "1.5.2"}), final()], faults="schema:get_release")
    agent.base_ctx.mcp = mcp
    res = agent.run("x")
    assert res.tool_calls[0]["outcome"] == "SCHEMA_ERROR"
