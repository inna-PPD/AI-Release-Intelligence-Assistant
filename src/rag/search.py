"""Пошук по чанках: векторний (Qdrant), лексичний (BM25), hybrid (RRF) і reranking (cross-encoder).

Режими search():
- vector        — лише embeddings: добре розуміє зміст і переклад (питання українською → англійський текст);
- bm25          — лише слова: точні рядки на кшталт «#9508», «1.46.1», «cnt_invoice», які вектор «розмиває»;
- hybrid        — об'єднання обох списків через Reciprocal Rank Fusion;
- hybrid_rerank — hybrid-кандидати пересортовує cross-encoder, що читає питання і чанк разом.

Фільтри за метаданими (filters): product, source, format, doc_id, version — значення або список значень;
date_from / date_to — «YYYY-MM-DD». Векторний пошук фільтрує в Qdrant, BM25 — тим самим предикатом у Python.
"""

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models
from rank_bm25 import BM25Okapi

from src.config import ROOT
from src.rag.embeddings import Embedder

MODES = ("vector", "bm25", "hybrid", "hybrid_rerank")
MATCH_FIELDS = ("product", "source", "format", "doc_id", "version")
TOKEN = re.compile(r"\w+(?:[.\-]\w+)*")


def tokenize(text: str) -> list[str]:
    """«cnt_invoice», «1.46.1», «svc-contoso-flows» — цілим токеном і частинами, щоб «invoice» теж знаходив."""
    tokens = []
    for t in TOKEN.findall(text.lower()):
        tokens.append(t)
        parts = re.split(r"[._\-]", t)
        if len(parts) > 1:
            tokens += [p for p in parts if p]
    return tokens


def date_int(date: str | None) -> int | None:
    return int(date.replace("-", "")[:8]) if date else None


def matches(chunk: dict, filters: dict | None) -> bool:
    if not filters:
        return True
    for key in MATCH_FIELDS:
        if key in filters:
            allowed = filters[key] if isinstance(filters[key], list) else [filters[key]]
            if chunk.get(key) not in allowed:
                return False
    d = date_int(chunk.get("date"))
    if "date_from" in filters and (d is None or d < date_int(filters["date_from"])):
        return False
    if "date_to" in filters and (d is None or d > date_int(filters["date_to"])):
        return False
    return True


def qdrant_filter(filters: dict | None) -> models.Filter | None:
    if not filters:
        return None
    must = []
    for key in MATCH_FIELDS:
        if key in filters:
            allowed = filters[key] if isinstance(filters[key], list) else [filters[key]]
            must.append(models.FieldCondition(key=key, match=models.MatchAny(any=allowed)))
    if "date_from" in filters or "date_to" in filters:
        must.append(models.FieldCondition(key="date_int", range=models.Range(
            gte=date_int(filters.get("date_from")), lte=date_int(filters.get("date_to")))))
    return models.Filter(must=must)


def rrf(rankings: list[list[int]], k: int) -> list[tuple[int, float]]:
    """Reciprocal Rank Fusion: score = Σ 1 / (k + rank). Не залежить від масштабу BM25 і косинусної схожості."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, idx in enumerate(ranking, 1):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])


@lru_cache(maxsize=1)
def _reranker(name: str, cache_dir: str) -> TextCrossEncoder:
    return TextCrossEncoder(name, cache_dir=str(ROOT / cache_dir))


@dataclass
class Hit:
    chunk: dict
    score: float
    scores: dict = field(default_factory=dict)  # vector / bm25 / rrf / rerank — для аналізу помилок


class Retriever:
    def __init__(self, cfg: dict, strategy: str = "structure", prompts: bool | None = None):
        self.cfg = cfg
        name = "chunks.jsonl" if strategy == "structure" else f"chunks_{strategy}.jsonl"
        path = ROOT / cfg["corpus"]["processed_dir"] / name
        self.chunks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        self.embedder = Embedder(cfg["embeddings"], prompts)
        vectors = self.embedder.embed_passages(self.chunks, tag=strategy)

        # векторна база: Qdrant у локальному режимі (без сервера); колекція перебудовується з кешу embeddings
        self.collection = f"{strategy}_{self.embedder.slug}"
        self.qdrant = QdrantClient(path=str(ROOT / cfg["index"]["qdrant_path"] / self.collection))
        if self.qdrant.collection_exists(self.collection):
            self.qdrant.delete_collection(self.collection)
        self.qdrant.create_collection(self.collection, vectors_config=models.VectorParams(
            size=vectors.shape[1], distance=models.Distance.COSINE))
        self.qdrant.upload_points(self.collection, [
            models.PointStruct(id=i, vector=v.tolist(), payload={
                **{k: c.get(k) for k in (*MATCH_FIELDS, "chunk_id", "title", "section", "date")},
                "date_int": date_int(c.get("date"))})
            for i, (c, v) in enumerate(zip(self.chunks, vectors))])

        self.bm25 = BM25Okapi([tokenize(c["embed_text"]) for c in self.chunks])

    # ---- окремі пошуки: повертають [(індекс чанка, оцінка)] ----

    def vector_search(self, question: str, k: int, filters: dict | None = None) -> list[tuple[int, float]]:
        res = self.qdrant.query_points(self.collection, query=self.embedder.embed_query(question).tolist(),
                                       query_filter=qdrant_filter(filters), limit=k)
        return [(p.id, p.score) for p in res.points]

    def bm25_search(self, question: str, k: int, filters: dict | None = None) -> list[tuple[int, float]]:
        scores = self.bm25.get_scores(tokenize(question))
        order = [i for i in np.argsort(-scores) if scores[i] > 0 and matches(self.chunks[i], filters)]
        return [(int(i), float(scores[i])) for i in order[:k]]

    # ---- основний вхід ----

    def search(self, question: str, mode: str = "hybrid_rerank", k: int | None = None,
               filters: dict | None = None) -> list[Hit]:
        s = self.cfg["search"]
        k = k or s["top_k"]
        n = max(s["candidates"], k)
        if mode == "vector":
            return [Hit(self.chunks[i], sc, {"vector": sc}) for i, sc in self.vector_search(question, k, filters)]
        if mode == "bm25":
            return [Hit(self.chunks[i], sc, {"bm25": sc}) for i, sc in self.bm25_search(question, k, filters)]

        vec, lex = self.vector_search(question, n, filters), self.bm25_search(question, n, filters)
        vec_s, lex_s = dict(vec), dict(lex)
        fused = rrf([[i for i, _ in vec], [i for i, _ in lex]], s["rrf_k"])
        hits = [Hit(self.chunks[i], sc, {"vector": vec_s.get(i), "bm25": lex_s.get(i), "rrf": sc}) for i, sc in fused]
        if mode == "hybrid":
            return hits[:k]
        if mode != "hybrid_rerank":
            raise ValueError(f"невідомий режим {mode}; доступні: {MODES}")

        candidates = hits[:n]
        reranker = _reranker(s["reranker"], self.cfg["embeddings"]["cache_dir"])
        rerank_scores = list(reranker.rerank(question, [h.chunk["embed_text"] for h in candidates]))
        for h, sc in zip(candidates, rerank_scores):
            h.scores["rerank"] = float(sc)
            h.score = float(sc)
        return sorted(candidates, key=lambda h: -h.score)[:k]

    def close(self):
        self.qdrant.close()
