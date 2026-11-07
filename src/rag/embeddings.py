"""Локальні embeddings (fastembed, ONNX на CPU) з кешем за хешем тексту.

Кеш (data/index/vectors_<модель>_<варіант>.npz) зберігає вектори для кожного тексту: при повторному ingestion
перераховуються лише нові або змінені чанки, а CI не витрачає ~3 хв на повний перерахунок.
"""

import hashlib
import re
from functools import lru_cache

import numpy as np
from fastembed import TextEmbedding

from src.config import ROOT


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


@lru_cache(maxsize=2)
def _model(name: str, cache_dir: str) -> TextEmbedding:
    return TextEmbedding(name, cache_dir=str(ROOT / cache_dir))


class Embedder:
    def __init__(self, cfg: dict, prompts: bool | None = None):
        self.name = cfg["model"]
        self.cache_dir = cfg["cache_dir"]
        self.prompts = cfg["prompts"] if prompts is None else prompts
        self.query_template = cfg["query_template"] if self.prompts else "{text}"
        self.passage_template = cfg["passage_template"] if self.prompts else "{text}"
        self.slug = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-") + ("_prompts" if self.prompts else "_plain")
        self.vectors_dir = ROOT / cfg["vectors_dir"]

    @property
    def model(self) -> TextEmbedding:
        return _model(self.name, self.cache_dir)

    def passage_text(self, chunk: dict) -> str:
        # з промптами назва документа йде в title, а в text — розділ + зміст; без промптів — embed_text як є
        if self.prompts:
            return self.passage_template.format(title=chunk["title"], text=f"{chunk['section']}\n\n{chunk['text']}")
        return chunk["embed_text"]

    def embed_passages(self, chunks: list[dict], tag: str) -> np.ndarray:
        """tag — набір чанків (structure / fixed): у кожного свій файл кешу."""
        cache_path = self.vectors_dir / f"vectors_{tag}_{self.slug}.npz"
        texts = [self.passage_text(c) for c in chunks]
        keys = [_sha(t) for t in texts]
        cache = {}
        if cache_path.exists():
            data = np.load(cache_path)
            cache = dict(zip(data["keys"].tolist(), data["vectors"]))
        missing = [(k, t) for k, t in zip(keys, texts) if k not in cache]
        if missing:
            print(f"  embeddings: рахую {len(missing)} нових текстів, з кешу {len(texts) - len(missing)}")
            for (k, _), v in zip(missing, self.model.embed([t for _, t in missing])):
                cache[k] = v
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            used = {k: cache[k] for k in keys}  # у кеші лишаються лише актуальні тексти
            np.savez_compressed(cache_path, keys=np.array(list(used)), vectors=np.array(list(used.values()), dtype=np.float32))
        vectors = np.array([cache[k] for k in keys], dtype=np.float32)
        return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

    def embed_query(self, question: str) -> np.ndarray:
        v = next(iter(self.model.embed([self.query_template.format(text=question)])))
        return (v / np.linalg.norm(v)).astype(np.float32)
