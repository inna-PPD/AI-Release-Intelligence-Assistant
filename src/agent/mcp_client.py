"""MCP-клієнт агента: запускає MCP-сервер трекера підпроцесом (stdio) і викликає його інструменти.

Цикл агента синхронний і викликає інструменти в потоках з таймаутом, а MCP SDK асинхронний. Тому сесія живе
у власному потоці з event loop, а call() — синхронна обгортка (run_coroutine_threadsafe).
Помилки сервера (is_error) перетворюються на ті самі винятки, що й у локального трекера, — цикл агента
обробляє їх однаково: ACCESS_DENIED → AccessDenied, NOT_FOUND → NotFound, INVALID_ARGUMENTS → ValueError.
"""

import asyncio
import os
import sys
import threading
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, stdio_client
from src.config import ROOT
from src.tracker.service import AccessDenied, NotFound

SERVER_MODULE = "src.mcp_server.tracker_server"
LOG_PATH = ROOT / "runtime" / "mcp_server.log"


class McpError(Exception):
    """Сервер повернув помилку без відомого коду або впав."""


class McpTracker:
    def __init__(self, team: str, expected_tools: list[str], start_timeout_s: float = 30):
        self.team = team
        self.expected = expected_tools
        self.server_tools: dict[str, dict] = {}
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, name="mcp-client", daemon=True)
        self._thread.start()
        self._stack: AsyncExitStack | None = None
        self._session: ClientSession | None = None
        self._run(self._connect(), start_timeout_s)

    def _run(self, coro, timeout: float | None):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result(timeout)

    async def _connect(self):
        params = StdioServerParameters(
            command=sys.executable, args=["-m", SERVER_MODULE], cwd=str(ROOT),
            env={**os.environ, "TRACKER_TEAM": self.team, "PYTHONIOENCODING": "utf-8"})
        self._stack = AsyncExitStack()
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        errlog = self._stack.enter_context(LOG_PATH.open("a", encoding="utf-8"))  # stderr сервера: журнал відмов доступу
        read, write = await self._stack.enter_async_context(stdio_client(params, errlog=errlog))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        tools = (await self._session.list_tools()).tools
        self.server_tools = {t.name: t.input_schema for t in tools}
        missing = set(self.expected) - set(self.server_tools)
        if missing:
            raise McpError(f"MCP-сервер не надає інструменти {sorted(missing)}; є: {sorted(self.server_tools)}")

    def call(self, name: str, arguments: dict, timeout: float | None = None) -> dict:
        args = {k: v for k, v in arguments.items() if v is not None}
        result = self._run(self._session.call_tool(name, args, read_timeout_seconds=timeout), timeout)
        if result.is_error:
            text = " ".join(getattr(c, "text", "") for c in result.content)
            for code, exc in (("ACCESS_DENIED", AccessDenied), ("NOT_FOUND", NotFound), ("INVALID_ARGUMENTS", ValueError)):
                if code in text:
                    raise exc(text.split(code + ":", 1)[-1].strip())
            raise McpError(text or "MCP-сервер повернув помилку")
        if result.structured_content is None:
            raise McpError("MCP-сервер не повернув структуровану відповідь")
        # MCPServer загортає dict-відповідь у {"result": …}, якщо тип повернення — не модель
        sc = result.structured_content
        return sc["result"] if set(sc) == {"result"} and isinstance(sc["result"], dict) else sc

    def close(self):
        if self._stack is not None:
            try:
                self._run(self._stack.aclose(), 10)
            except Exception:  # noqa: BLE001 — закриття підпроцесу не має валити завершення програми
                pass
            self._stack = None
        self._loop.call_soon_threadsafe(self._loop.stop)
