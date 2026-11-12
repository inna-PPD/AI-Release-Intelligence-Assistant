"""RAG-відповідь з джерелами.

питання → hybrid + rerank → поріг «не знаю» → бюджет контексту → LLM (structured output: твердження → джерела)
→ валідація посилань (1 спроба виправлення) → відповідь із переліком джерел.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.config import load_config
from src.extraction.pipeline import cost_usd
from src.extraction.prompts import load_prompt
from src.ingest.chunking import count_tokens
from src.llm import LLMError, SamplingParams, make_client
from src.rag.search import Retriever

NOT_FOUND = "У документах цього немає."


class Claim(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str = Field(description="Одне твердження з відповіді")
    sources: list[str] = Field(description="id джерел, що підтверджують твердження, напр. ['S1', 'S3']")


class RagAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["answered", "not_found"] = Field(description="not_found — якщо в джерелах немає відповіді")
    answer: str = Field(description="Відповідь мовою питання з мітками джерел [S1]; для not_found — фіксована фраза")
    claims: list[Claim] = Field(description="Усі твердження відповіді з джерелами; порожній для not_found")


@dataclass
class Source:
    id: str
    chunk_id: str
    title: str
    section: str
    version: str | None
    date: str | None
    url: str | None
    rerank: float | None
    tokens: int
    text: str  # текст чанка — для перевірки faithfulness і розбору помилок


@dataclass
class Answer:
    question: str
    status: str                    # answered | not_found | failed
    answer: str
    claims: list[dict]
    sources: list[Source]          # джерела, що потрапили в контекст
    cited: list[str]               # id джерел, на які реально посилається відповідь
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    def render(self) -> str:
        lines = [self.answer]
        cited = [s for s in self.sources if s.id in self.cited]
        if cited:
            lines += ["", "Джерела:"]
            for s in cited:
                ver = s.version or s.date or ""
                lines.append(f"[{s.id}] {s.title} › {s.section}" + (f" ({ver})" if ver else "") + (f" — {s.url}" if s.url else ""))
        return "\n".join(lines)


def build_context(hits, budget: int) -> tuple[list[Source], str, int]:
    """Чанки в порядку релевантності, поки вміщуються в бюджет токенів. → (джерела, текст контексту, відкинуто)."""
    sources, blocks, used = [], [], 0
    for hit in hits:
        c = hit.chunk
        sid = f"S{len(sources) + 1}"
        header = f"[{sid}] Документ: {c['title']} | Розділ: {c['section']} | Версія/дата: {c.get('version') or c.get('date') or '—'}"
        block = f"{header}\n{c['text']}"
        size = count_tokens(block)
        if used + size > budget:
            continue  # менш релевантний, але коротший чанк ще може вміститися
        used += size
        blocks.append(block)
        sources.append(Source(sid, c["chunk_id"], c["title"], c["section"], c.get("version"), c.get("date"),
                              c.get("url"), hit.scores.get("rerank"), size, c["text"]))
    return sources, "\n\n".join(blocks), len(hits) - len(sources)


def check_citations(result: RagAnswer, source_ids: set[str]) -> list[str]:
    """Помилки, яких не ловить JSON-схема: твердження без джерела, посилання на неіснуюче джерело."""
    problems = []
    if result.status == "answered" and not result.claims:
        problems.append("status answered, але claims порожній — кожне твердження має мати джерело")
    for i, claim in enumerate(result.claims, 1):
        if not claim.sources:
            problems.append(f"твердження {i} без джерела: «{claim.statement[:80]}»")
        unknown = [s for s in claim.sources if s not in source_ids]
        if unknown:
            problems.append(f"твердження {i} посилається на неіснуючі джерела {unknown}; доступні: {sorted(source_ids)}")
    return problems


class RagPipeline:
    def __init__(self, rag_cfg: dict, retriever: Retriever | None = None, prompt_id: str | None = None):
        self.cfg = rag_cfg["answer"]
        self.retriever = retriever or Retriever(rag_cfg)
        self.prompt = load_prompt(prompt_id or self.cfg["prompt"])
        models = load_config()
        self.model_cfg = models["models"][self.cfg["model"]]
        self.client = make_client(self.model_cfg, models)
        self.params = SamplingParams(**self.cfg["sampling"], max_tokens=self.cfg["max_tokens"])

    def ask(self, question: str, filters: dict | None = None) -> Answer:
        start = time.perf_counter()
        hits = self.retriever.search(question, mode="hybrid_rerank", k=self.cfg["candidates"], filters=filters)
        meta = {"prompt_version": self.prompt.id, "prompt_sha": self.prompt.sha, "model": self.client.name,
                "retrieved": [h.chunk["chunk_id"] for h in hits],
                "top_rerank": hits[0].scores.get("rerank") if hits else None,
                "tokens_in": 0, "tokens_out": 0, "llm_calls": 0, "cost_usd": 0.0}

        # 1) «не знаю» без LLM: нічого релевантного не знайдено
        if not hits or meta["top_rerank"] < self.cfg["min_rerank_score"]:
            meta.update(gate="below_threshold", latency_ms=int((time.perf_counter() - start) * 1000))
            return Answer(question, "not_found", NOT_FOUND, [], [], [], meta)

        # 2) бюджет контексту
        sources, context, dropped = build_context(hits, self.cfg["context_budget_tokens"])
        meta.update(context_tokens=sum(s.tokens for s in sources), dropped_by_budget=dropped)

        # 3) LLM зі structured output + перевірка посилань, одна спроба виправлення
        messages = self.prompt.messages_for(question=question, context=context)
        result, problems = None, []
        for attempt in (1, 2):
            try:
                llm = self.client.generate_structured(messages, RagAnswer, self.params)
            except LLMError as e:
                meta.update(error=f"llm: {e}", latency_ms=int((time.perf_counter() - start) * 1000))
                return Answer(question, "failed", f"Помилка моделі: {e}", [], sources, [], meta)
            meta["llm_calls"] += 1
            meta["tokens_in"] += llm.tokens_in
            meta["tokens_out"] += llm.tokens_out
            try:
                result = RagAnswer.model_validate_json(llm.raw_text)
                problems = check_citations(result, {s.id for s in sources})
            except ValidationError as e:
                result, problems = None, [f"невалідний JSON: {e.errors()[0]['msg']}"]
            if not problems:
                break
            messages = messages + [{"role": "assistant", "content": llm.raw_text},
                                   {"role": "user", "content": "Виправ відповідь:\n- " + "\n- ".join(problems)}]

        meta["cost_usd"] = cost_usd(meta["tokens_in"], meta["tokens_out"], self.model_cfg["price_per_1m_tokens"])
        meta["latency_ms"] = int((time.perf_counter() - start) * 1000)
        if result is None or problems:
            meta["error"] = "; ".join(problems)
            return Answer(question, "failed", "Не вдалося отримати відповідь із коректними джерелами.", [], sources, [], meta)
        meta["repaired"] = meta["llm_calls"] > 1
        cited = sorted({s for c in result.claims for s in c.sources}, key=lambda x: int(x[1:]))
        answer_text = NOT_FOUND if result.status == "not_found" else result.answer
        return Answer(question, result.status, answer_text, [c.model_dump() for c in result.claims], sources, cited, meta)


def answer_to_json(answer: Answer) -> str:
    return json.dumps(answer.to_dict(), ensure_ascii=False)
