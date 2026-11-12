import json

from src.extraction.prompts import load_prompt
from src.llm import LLMResult, SamplingParams
from src.rag.answer import NOT_FOUND, RagAnswer, RagPipeline, build_context, check_citations
from src.rag.search import Hit


def chunk(i, text="pac CLI версії 1.44 або новішої", **extra):
    return {"chunk_id": f"doc#{i:03d}", "doc_id": "doc", "title": "Інструкція 1.5", "section": f"Розділ {i}",
            "version": "1.5", "date": "2026-06-09", "url": None, "text": text, **extra}


def hit(i, rerank=3.0, text="pac CLI версії 1.44 або новішої"):
    return Hit(chunk(i, text), rerank, {"rerank": rerank})


def test_context_respects_token_budget_and_numbers_sources():
    hits = [hit(1), hit(2, text="дуже довгий текст " * 400), hit(3)]
    sources, context, dropped = build_context(hits, budget=200)
    assert [s.id for s in sources] == ["S1", "S2"] and dropped == 1  # довгий чанк не вмістився
    assert [s.chunk_id for s in sources] == ["doc#001", "doc#003"]
    assert "[S1] Документ: Інструкція 1.5 | Розділ: Розділ 1 | Версія/дата: 1.5" in context
    assert sum(s.tokens for s in sources) <= 200


def test_citation_checks():
    ok = RagAnswer(status="answered", answer="1.44 [S1]", claims=[{"statement": "1.44", "sources": ["S1"]}])
    assert check_citations(ok, {"S1", "S2"}) == []
    no_source = RagAnswer(status="answered", answer="x", claims=[{"statement": "x", "sources": []}])
    assert "без джерела" in check_citations(no_source, {"S1"})[0]
    unknown = RagAnswer(status="answered", answer="x", claims=[{"statement": "x", "sources": ["S9"]}])
    assert "неіснуючі" in check_citations(unknown, {"S1"})[0]
    empty = RagAnswer(status="answered", answer="x", claims=[])
    assert check_citations(empty, {"S1"})
    assert check_citations(RagAnswer(status="not_found", answer=NOT_FOUND, claims=[]), {"S1"}) == []


def test_prompt_placeholders_do_not_reprocess_inserted_text():
    p = load_prompt("rag_answer/v1")
    user = p.messages_for(question="Що означає {context}?", context="[S1] текст з {json: 1}")[1]["content"]
    assert "Що означає {context}?" in user and "[S1] текст з {json: 1}" in user


class FakeRetriever:
    def __init__(self, hits):
        self.hits = hits

    def search(self, *a, **kw):
        return self.hits


class FakeClient:
    name = "fake/model"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def generate_structured(self, messages, schema, params):
        self.calls += 1
        return LLMResult(json.dumps(self.replies.pop(0), ensure_ascii=False), 1000, 100, 50, self.name)


def pipeline(hits, replies, threshold=-1.0):
    p = object.__new__(RagPipeline)  # без завантаження моделей і конфігу
    p.cfg = {"candidates": 8, "context_budget_tokens": 2000, "min_rerank_score": threshold}
    p.retriever, p.client = FakeRetriever(hits), FakeClient(replies)
    p.prompt = load_prompt("rag_answer/v1")
    p.model_cfg = {"price_per_1m_tokens": {"input": 0.15, "output": 0.60}}
    p.params = SamplingParams()
    return p


def test_gate_answers_not_found_without_llm():
    p = pipeline([hit(1, rerank=-3.0)], replies=[])
    a = p.ask("Хто CEO?")
    assert a.status == "not_found" and a.answer == NOT_FOUND and p.client.calls == 0
    assert a.meta["gate"] == "below_threshold" and a.meta["cost_usd"] == 0.0


def test_answer_with_citations_and_repair():
    bad = {"status": "answered", "answer": "1.44 [S7]", "claims": [{"statement": "1.44", "sources": ["S7"]}]}
    good = {"status": "answered", "answer": "1.44 [S1]", "claims": [{"statement": "1.44", "sources": ["S1"]}]}
    p = pipeline([hit(1), hit(2)], replies=[bad, good])
    a = p.ask("Яка версія pac CLI?")
    assert a.status == "answered" and a.cited == ["S1"] and a.meta["repaired"] and p.client.calls == 2
    assert a.meta["tokens_in"] == 2000 and a.meta["cost_usd"] > 0
    assert "Джерела:\n[S1] Інструкція 1.5 › Розділ 1 (1.5)" in a.render()
