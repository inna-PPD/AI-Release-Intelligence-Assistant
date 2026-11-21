"""MCP-сервер «Contoso Release Tracker» (кейс 3, крок 2): трекер релізів і дефектів лише для читання.

Запуск окремо (stdio):   python -m src.mcp_server.tracker_server
Агент запускає його сам як підпроцес і підключається як MCP-клієнт (src/agent/mcp_client.py).

Обмеження — на сервері, незалежно від того, що просить клієнт:
- лише читання: 3 інструменти, жодного запису, SQL, shell чи читання довільних файлів;
  дані — два фіксовані файли data/tracker/*.json, завантажені при старті;
- валідація входу: формат версії X.Y.Z, id DEF-123, severity і status — з переліку; невідомі аргументи відхиляються;
- команда клієнта задається при запуску (TRACKER_TEAM), а не аргументом інструмента — агент не може «попросити» чужу;
  дефекти інших команд → ACCESS_DENIED (аналог 403);
- відповідь обмежена 50 записами; схема відповіді (output_schema) описана моделями src/tracker/models.py.
Помилки повертаються як is_error з кодом на початку (ACCESS_DENIED / NOT_FOUND / INVALID_ARGUMENTS),
щоб клієнт міг відрізнити «немає доступу» від «немає даних».
"""

import logging
import os
from typing import Annotated, Literal

from pydantic import Field

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from src.tracker.models import DefectListOut, DefectOut, ReleaseOut
from src.tracker.service import AccessDenied, NotFound, TrackerService

MAX_ROWS = 50
Version = Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$", description="Версія X.Y.Z, напр. 1.5.2")]

logging.basicConfig(level=logging.WARNING)  # stdout зайнятий протоколом MCP; логи — у stderr
log = logging.getLogger("tracker-mcp")

class StrictMCPServer(MCPServer):
    """MCPServer за замовчуванням мовчки ігнорує невідомі аргументи — тут вони відхиляються:
    спроба передати, напр., path чи team не має проходити непоміченою."""

    async def call_tool(self, name, arguments, context=None):
        tool = self._tool_manager.get_tool(name)
        if tool is not None:
            extra = set(arguments or {}) - set(tool.parameters.get("properties", {}))
            if extra:
                log.warning("rejected unknown arguments %s for %s", sorted(extra), name)
                raise ToolError(f"INVALID_ARGUMENTS: невідомі аргументи {sorted(extra)} для {name}")
        return await super().call_tool(name, arguments, context)


TEAM = os.getenv("TRACKER_TEAM", "procurement")
tracker = TrackerService(team=TEAM)
server = StrictMCPServer(
    name="contoso-release-tracker",
    instructions="Read-only трекер релізів і дефектів Contoso Procurement. Доступні лише дефекти команди клієнта.",
    version="1.0.0",
)


def _call(fn, *args):
    try:
        return fn(*args)
    except AccessDenied as e:
        log.warning("ACCESS_DENIED team=%s: %s", TEAM, e)
        raise ToolError(f"ACCESS_DENIED: {e}") from e
    except NotFound as e:
        raise ToolError(f"NOT_FOUND: {e}") from e
    except ValueError as e:
        raise ToolError(f"INVALID_ARGUMENTS: {e}") from e


@server.tool(description="Картка релізу Contoso Procurement: статус, дата релізу (null — не призначена), solution, середовища.")
def get_release(version: Version) -> ReleaseOut:
    return ReleaseOut(**_call(tracker.get_release, version))


@server.tool(description="Дефекти команди клієнта з фільтрами за версією, severity і статусом (до 50 записів).")
def list_defects(version: Version | None = None,
                 severity: Literal["critical", "high", "medium", "low"] | None = None,
                 status: Literal["open", "resolved"] | None = None) -> DefectListOut:
    out = _call(tracker.list_defects, version, severity, status)
    return DefectListOut(**{**out, "defects": out["defects"][:MAX_ROWS]})


@server.tool(description="Один дефект за id (DEF-123). Дефект іншої команди → ACCESS_DENIED.")
def get_defect(defect_id: Annotated[str, Field(pattern=r"^DEF-\d{1,5}$", description="Id дефекту, напр. DEF-107")]) -> DefectOut:
    return DefectOut(**_call(tracker.get_defect, defect_id))


if __name__ == "__main__":
    server.run()  # stdio
