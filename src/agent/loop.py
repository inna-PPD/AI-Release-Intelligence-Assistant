"""Цикл агента з контролем виконання.

питання → [модель → tool calls → валідація → (підтвердження людини) → виклик з таймаутом/повторами → перевірка
схеми відповіді] × N → відповідь з джерелами.

Що гарантує код (а не промпт):
- ліміти: кроків, токенів, $, таймаут на інструмент і на весь запит; причина зупинки — stop_reason у trace;
  на м'якому ліміті модель отримує останній крок без нових інструментів і дає частковий результат;
- невалідні аргументи, винятки, таймаути, зламаний формат відповіді повертаються моделі текстом з кодом помилки;
- повтори з backoff лише для безпечних (read-only) інструментів;
- дія з побічним ефектом — лише після confirm() від людини; значення grounded_args мають бути в словах користувача;
- той самий виклик з тими самими аргументами — не більше max_same_call разів (захист від зациклення).
"""

import json
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import asdict, dataclass, field, replace
from typing import Callable

from pydantic import ValidationError

from src.agent.faults import FaultInjector, TransientToolError
from src.agent.tools import SourceRegistry, ToolContext, ToolSpec
from src.extraction.pipeline import cost_usd
from src.extraction.prompts import Prompt
from src.ingest.chunking import count_tokens
from src.llm import LLMError, SamplingParams
from src.tracker.service import AccessDenied, NotFound

CITE_RE = re.compile(r"\[(S\d+)\]")
LIMIT_NOTE = ("Ліміт запиту вичерпано ({reason}). Нових інструментів викликати не можна. Дай частковий результат: "
              "що вдалося з'ясувати (з джерелами) і що лишилось неперевіреним. Почни з «Частковий результат:».")
_POOL = ThreadPoolExecutor(max_workers=8, thread_name_prefix="tool")


@dataclass
class Limits:
    max_steps: int = 8
    max_tokens_total: int = 40000
    max_cost_usd: float = 0.01
    soft_limit: float = 0.8
    tool_timeout_s: float = 15
    request_timeout_s: float = 120
    tool_retries: int = 2
    backoff_s: float = 0.5
    max_same_call: int = 2


@dataclass
class AgentResult:
    question: str
    answer: str
    status: str                       # answered | partial | failed
    stop_reason: str                  # answered | max_steps | budget_tokens | budget_usd | timeout | llm_error
    steps: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    tool_calls: list[dict] = field(default_factory=list)    # name, args, outcome, attempts
    side_effects: list[dict] = field(default_factory=list)  # виконані дії з побічним ефектом
    confirmations: list[dict] = field(default_factory=list)
    sources: dict = field(default_factory=dict)             # S-id → документ, розділ (лише процитовані)
    trace: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def render(self) -> str:
        lines = [self.answer]
        if self.sources:
            lines += ["", "Джерела:"]
            for sid, s in self.sources.items():
                ver = s.get("version") or s.get("date") or ""
                lines.append(f"[{sid}] {s['title']} › {s['section']}" + (f" ({ver})" if ver else ""))
        lines.append(f"\n— {self.stop_reason} · кроків {self.steps} · ${self.cost_usd:.4f} · {self.latency_ms} мс")
        return "\n".join(lines)


Confirm = Callable[[str, dict], bool]


class Agent:
    def __init__(self, llm, tools: dict[str, ToolSpec], ctx: ToolContext, prompt: Prompt, limits: Limits,
                 params: SamplingParams, price: dict, confirm: Confirm | None = None, faults: str | None = None,
                 meta: dict | None = None):
        self.llm, self.tools, self.base_ctx, self.prompt = llm, tools, ctx, prompt
        self.limits, self.params, self.price = limits, params, price
        self.confirm = confirm
        self.faults_spec = faults
        self.meta = meta or {}
        self.schemas = [t.openai_schema() for t in tools.values()]
        self.schema_tokens = count_tokens(json.dumps(self.schemas, ensure_ascii=False))

    # ------------------------------------------------------------------ run
    def run(self, question: str) -> AgentResult:
        L = self.limits
        start = time.perf_counter()
        deadline = start + L.request_timeout_s
        ctx = replace(self.base_ctx, registry=SourceRegistry())
        faults = FaultInjector(self.faults_spec)
        res = AgentResult(question, "", "failed", "", meta={**self.meta, "faults": self.faults_spec or None})
        calls_seen: Counter = Counter()
        messages = self.prompt.messages_for(question=question)

        def ev(kind: str, **data):
            res.trace.append({"t_ms": int((time.perf_counter() - start) * 1000), "step": res.steps, "type": kind, **data})

        for step in range(1, L.max_steps + 1):
            # бюджет рахуємо з урахуванням наступного виклику: результати інструментів уже лежать у messages
            next_in = count_tokens(json.dumps(messages, ensure_ascii=False)) + self.schema_tokens
            if res.tokens_in + res.tokens_out + next_in > L.max_tokens_total and step > 1:
                ev("guard", action="hard_stop", reason="budget_tokens", next_call_tokens=next_in)
                res.stop_reason, res.status = "budget_tokens", "partial"
                res.answer = (f"Частковий результат: запит зупинено (бюджет токенів: наступний крок потребував би "
                              f"~{next_in} токенів)." + self._progress(res))
                break
            forced = self._limit_reason(res, step, deadline, soft=True, next_in=next_in)
            if forced:
                ev("guard", action="final_without_tools", reason=forced)
                messages.append({"role": "system", "content": LIMIT_NOTE.format(reason=forced)})
            res.steps = step
            try:
                r = self.llm.chat(messages, self.schemas, self.params, tool_choice="none" if forced else "auto")
            except LLMError as e:
                ev("llm", error=str(e))
                res.stop_reason, res.status = "llm_error", "failed"
                res.answer = "Модель недоступна, відповісти зараз не можу." + self._progress(res)
                break
            res.tokens_in += r.tokens_in
            res.tokens_out += r.tokens_out
            res.cost_usd = cost_usd(res.tokens_in, res.tokens_out, self.price)
            ev("llm", tokens_in=r.tokens_in, tokens_out=r.tokens_out, latency_ms=r.latency_ms,
               tool_calls=[c.name for c in r.tool_calls], content=r.content[:500])

            if forced or not r.tool_calls:
                res.answer = r.content.strip()
                if forced and not res.answer:  # модель проігнорувала tool_choice=none — частковий результат з коду
                    res.answer = f"Частковий результат: запит зупинено ({forced})." + self._progress(res)
                res.stop_reason = forced or "answered"
                res.status = "partial" if forced else "answered"
                break

            messages.append({"role": "assistant", "content": r.content or None, "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": c.arguments}}
                for c in r.tool_calls]})
            for call in r.tool_calls:
                content = self._execute(call, ctx, faults, calls_seen, question, deadline, res, ev)
                messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

            hard = self._limit_reason(res, step, deadline, soft=False)
            if hard:
                ev("guard", action="hard_stop", reason=hard)
                res.stop_reason, res.status = hard, "partial"
                res.answer = f"Частковий результат: запит зупинено ({hard})." + self._progress(res)
                break

        res.latency_ms = int((time.perf_counter() - start) * 1000)
        cited = dict.fromkeys(CITE_RE.findall(res.answer))
        res.sources = {sid: ctx.registry.sources[sid] for sid in cited if sid in ctx.registry.sources}
        unknown = [sid for sid in cited if sid not in ctx.registry.sources]
        if unknown:
            ev("check", error=f"посилання на неіснуючі джерела {unknown}")
        ev("stop", reason=res.stop_reason)
        return res

    def _limit_reason(self, res: AgentResult, step: int, deadline: float, soft: bool, next_in: int = 0) -> str | None:
        L = self.limits
        k = L.soft_limit if soft else 1.0
        if soft and step == L.max_steps:
            return "max_steps"
        if res.tokens_in + res.tokens_out + next_in >= k * L.max_tokens_total:
            return "budget_tokens"
        if res.cost_usd >= k * L.max_cost_usd:
            return "budget_usd"
        left = deadline - time.perf_counter()
        if left <= (min(20.0, 0.2 * L.request_timeout_s) if soft else 0):
            return "timeout"
        return None

    @staticmethod
    def _progress(res: AgentResult) -> str:
        done = [f"{c['name']} → {c['outcome']}" for c in res.tool_calls]
        return (" Встиг виконати: " + "; ".join(done) + ".") if done else ""

    # -------------------------------------------------------------- execute
    def _execute(self, call, ctx, faults, calls_seen, question, deadline, res, ev) -> str:
        L = self.limits
        log = {"name": call.name, "args": call.arguments, "outcome": "", "attempts": 0}
        res.tool_calls.append(log)

        def fail(code: str, msg: str, **extra) -> str:
            log["outcome"] = code
            ev("tool", name=call.name, args=call.arguments, error=code, detail=msg, **extra)
            return f"{code}: {msg}"

        spec = self.tools.get(call.name)
        if spec is None:
            return fail("UNKNOWN_TOOL", f"інструмента {call.name} немає; доступні: {', '.join(self.tools)}")
        try:
            raw_args = json.loads(call.arguments or "{}")
        except json.JSONDecodeError as e:
            return fail("INVALID_ARGUMENTS", f"аргументи не є валідним JSON ({e.msg}); надішли JSON-об'єкт")
        key = call.name + json.dumps(raw_args, sort_keys=True, ensure_ascii=False)
        calls_seen[key] += 1
        if calls_seen[key] > L.max_same_call:
            return fail("REPEATED_CALL", "цей виклик з тими самими аргументами вже був; використай попередній "
                                         "результат, зміни запит або відповідай з тим, що є")
        try:
            args = spec.args_model.model_validate(raw_args)
        except ValidationError as e:
            errs = "; ".join(f"{'.'.join(map(str, x['loc'])) or 'args'}: {x['msg']}" for x in e.errors())
            return fail("INVALID_ARGUMENTS", f"{errs}. Виправ аргументи за схемою {call.name} і виклич ще раз")

        for name in spec.grounded_args:
            value = getattr(args, name)
            if value and str(value) not in question:
                return fail("MISSING_INFO", f"{name}={value!r} користувач не називав; не вгадуй — перепитай користувача")

        if spec.side_effect:
            approved = bool(self.confirm and self.confirm(spec.name, args.model_dump()))
            res.confirmations.append({"tool": spec.name, "args": args.model_dump(), "approved": approved})
            ev("confirm", name=spec.name, args=args.model_dump(), approved=approved)
            if not approved:
                return fail("DECLINED", "людина не підтвердила дію; її НЕ виконано")

        attempts = 1 + (L.tool_retries if spec.safe_to_retry else 0)
        error: TransientToolError | None = None
        for attempt in range(attempts):
            log["attempts"] = attempt + 1
            timeout = min(L.tool_timeout_s, max(0.1, deadline - time.perf_counter()))
            t0 = time.perf_counter()
            future = _POOL.submit(faults.call, spec.name, lambda: spec.fn(args, ctx), timeout)
            try:
                out = future.result(timeout=timeout)
            except FutureTimeout:
                error = TransientToolError("timeout", f"немає відповіді за {timeout:.0f} с")
            except TransientToolError as e:
                error = e
            except AccessDenied as e:
                return fail("ACCESS_DENIED", f"{e}. Не шукай ці дані іншими інструментами")
            except NotFound as e:
                return fail("NOT_FOUND", str(e))
            except ValueError as e:
                return fail("INVALID_ARGUMENTS", str(e))
            except Exception as e:  # noqa: BLE001 — будь-який виняток інструмента не валить агента
                return fail("TOOL_ERROR", f"{type(e).__name__}: {e}")
            else:
                latency = int((time.perf_counter() - t0) * 1000)
                try:
                    spec.output_model.model_validate(out)
                except ValidationError as e:
                    errs = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()[:3])
                    return fail("SCHEMA_ERROR", f"відповідь {call.name} не відповідає очікуваній схемі ({errs}); "
                                                "дані ненадійні — не підставляй значення", latency_ms=latency)
                log["outcome"] = "ok"
                if spec.side_effect and attempt > 0 and out.get("status") == "already_exists":
                    # перша спроба виконалась, але відповідь загубилась: тікет створив саме цей запит
                    out = {**out, "status": "created"}
                    ev("guard", action="recovered_after_retry", name=call.name, detail="already_exists → created")
                if spec.side_effect:
                    res.side_effects.append({"tool": spec.name, "args": args.model_dump(), "result": out})
                ev("tool", name=call.name, args=call.arguments, ok=True, attempts=attempt + 1, latency_ms=latency,
                   result=json.dumps(out, ensure_ascii=False)[:800])
                return json.dumps(out, ensure_ascii=False)
            ev("tool", name=call.name, args=call.arguments, error="transient", status=error.status, attempt=attempt + 1)
            if attempt < attempts - 1:
                pause = L.backoff_s * 2 ** attempt
                if time.perf_counter() + pause >= deadline:
                    break
                time.sleep(pause)

        if spec.side_effect:
            return fail("SERVICE_UNAVAILABLE", f"{call.name}: {error.status} — результат невідомий (дія могла "
                                               "виконатись). Повторний виклик з тими самими даними безпечний: "
                                               "ключ ідемпотентності не створить дубль")
        return fail("SERVICE_UNAVAILABLE", f"{call.name} недоступний ({error.status}) після {log['attempts']} спроб. "
                                           "Скажи користувачу, що сервіс недоступний; не відповідай за нього з пам'яті")
