"""Імітація збоїв інструментів для перевірки агента (FAULTS=...).

Формат: елементи через кому, кожен `вид[xN][:інструмент]`:
    timeout              — інструмент «зависає» довше за таймаут виклику
    429, 503             — сервіс відповідає Too Many Requests / Service Unavailable
    schema               — API змінив формат: поле перейменоване (перевіряє схема відповіді)
    lost_response        — дія виконалась, але відповідь загубилась (обрив зв'язку) → перевірка ідемпотентності
    xN                   — лише перші N викликів (напр. 503x1 — один збій, далі працює)
    :інструмент          — лише цей інструмент; без нього — усі
Приклади: FAULTS=timeout:search_docs · FAULTS=503x1:list_defects · FAULTS=schema:get_release
"""

import copy
import time
from dataclasses import dataclass

KINDS = {"timeout", "429", "503", "schema", "lost_response"}


class TransientToolError(Exception):
    """Тимчасовий збій (timeout / 429 / 503): безпечний виклик можна повторити."""

    def __init__(self, status: str, message: str = ""):
        super().__init__(message or status)
        self.status = status


@dataclass
class Fault:
    kind: str
    tool: str | None = None
    times: int | None = None   # None — завжди
    fired: int = 0

    def applies(self, tool: str) -> bool:
        return (self.tool is None or self.tool == tool) and (self.times is None or self.fired < self.times)


def parse_faults(spec: str | None) -> list[Fault]:
    faults = []
    for item in filter(None, (s.strip() for s in (spec or "").split(","))):
        head, _, tool = item.partition(":")
        kind, _, times = head.partition("x")
        if kind not in KINDS:
            raise ValueError(f"FAULTS: невідомий вид збою {kind!r}; можливі: {sorted(KINDS)}")
        faults.append(Fault(kind, tool or None, int(times) if times else None))
    return faults


def break_schema(obj):
    """Імітує зміну формату API: перейменовує поле в першому записі (release_date → releaseDate тощо)."""
    obj = copy.deepcopy(obj)
    target = obj
    for key in ("results", "defects"):
        if isinstance(obj, dict) and obj.get(key):
            target = obj[key][0]
            break
    preferred = [k for k in ("release_date", "severity", "text", "status") if k in target]
    key = preferred[0] if preferred else next(iter(target))
    parts = key.split("_")
    target[parts[0] + "".join(p.title() for p in parts[1:]) + ("V2" if len(parts) == 1 else "")] = target.pop(key)
    return obj


class FaultInjector:
    def __init__(self, spec: str | None):
        self.faults = parse_faults(spec)

    def call(self, tool: str, fn, timeout_s: float):
        """Викликає fn() з урахуванням збоїв для цього інструмента."""
        fault = next((f for f in self.faults if f.applies(tool)), None)
        if fault is None:
            return fn()
        fault.fired += 1
        if fault.kind == "timeout":
            time.sleep(timeout_s + 0.5)   # справжнє «зависання» — його має перервати таймаут циклу агента
            return fn()
        if fault.kind in ("429", "503"):
            raise TransientToolError(fault.kind, f"HTTP {fault.kind} (FAULTS)")
        if fault.kind == "lost_response":
            fn()                           # дія виконана…
            raise TransientToolError("timeout", "з'єднання обірвалось після виклику (FAULTS)")  # …відповідь втрачена
        return break_schema(fn())          # schema
