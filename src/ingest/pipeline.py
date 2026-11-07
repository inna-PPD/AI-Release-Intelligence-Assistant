"""Ingestion: сирі документи → блоки → очищення → дедуплікація → чанки з метаданими.

Результат у data/processed/:
- chunks.jsonl        — основна (структурна) стратегія, вхід для індексації;
- chunks_fixed.jsonl  — фіксована стратегія, лише для порівняння;
- manifest.json       — що оброблено: документи, хеші, кількість чанків, відкинуті дублікати;
- chunking_comparison.md — порівняння стратегій.
"""

import hashlib
import json
import re
import statistics
from pathlib import Path

import yaml

from src.config import ROOT
from src.ingest.chunking import count_tokens, fixed_chunks, structure_chunks
from src.ingest.clean import clean_blocks
from src.ingest.extract import extract

CONFIG_PATH = ROOT / "config" / "rag.yaml"
META_FIELDS = ["doc_id", "title", "source", "format", "url", "product", "version", "date", "license"]


def load_rag_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def sha(text: str, n: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def dedup_key(text: str) -> str:
    """Ключ дублікатів: без різниці в регістрі й пробілах (цифри й версії зберігаються)."""
    return sha(re.sub(r"\s+", " ", text.lower()).strip())


def build_chunks(doc: dict, raw_chunks: list[dict], strategy: str, doc_hash: str) -> list[dict]:
    out = []
    for i, c in enumerate(raw_chunks):
        out.append({
            "chunk_id": f"{doc['doc_id']}#{i:03d}",
            **{k: doc[k] for k in META_FIELDS},
            "doc_hash": doc_hash,
            "section": c["section"],
            "chunk_index": i,
            "strategy": strategy,
            "n_tokens": count_tokens(c["text"]),
            "content_hash": dedup_key(c["text"]),
            "split_block": c["split_block"],
            "mixed_sections": c["mixed_sections"],
            "text": c["text"],
            # contextual chunk header: назва документа й розділ потрапляють в embedding
            "embed_text": f"{doc['title']}\n{c['section']}\n\n{c['text']}",
        })
    return out


def drop_duplicates(chunks: list[dict]) -> tuple[list[dict], list[dict]]:
    seen, kept, dropped = {}, [], []
    for c in chunks:
        if c["content_hash"] in seen:
            dropped.append({"chunk_id": c["chunk_id"], "duplicate_of": seen[c["content_hash"]]})
        else:
            seen[c["content_hash"]] = c["chunk_id"]
            kept.append(c)
    return kept, dropped


def stats(chunks: list[dict]) -> dict:
    sizes = [c["n_tokens"] for c in chunks]
    return {
        "chunks": len(chunks),
        "tokens_avg": round(statistics.mean(sizes)) if sizes else 0,
        "tokens_min": min(sizes, default=0),
        "tokens_max": max(sizes, default=0),
        "split_block_pct": round(100 * sum(c["split_block"] for c in chunks) / max(len(chunks), 1)),
        "mixed_sections_pct": round(100 * sum(c["mixed_sections"] for c in chunks) / max(len(chunks), 1)),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def comparison_report(cfg: dict, structure: list[dict], fixed: list[dict]) -> str:
    ch = cfg["chunking"]
    s_all, f_all = stats(structure), stats(fixed)
    lines = [
        "# Порівняння chunking-стратегій",
        "",
        f"structure: max {ch['max_tokens']} / min {ch['min_tokens']} токенів · "
        f"fixed: {ch['fixed']['size']} токенів, overlap {ch['fixed']['overlap']} · токенізатор o200k_base",
        "",
        "## Увесь корпус (після дедуплікації)",
        "",
        "| Стратегія | Чанків | Токенів avg / min / max | Чанки з розрізаним блоком | Чанки з кількох розділів |",
        "|---|---|---|---|---|",
    ]
    for name, s in (("structure", s_all), ("fixed", f_all)):
        lines.append(f"| {name} | {s['chunks']} | {s['tokens_avg']} / {s['tokens_min']} / {s['tokens_max']} "
                     f"| {s['split_block_pct']}% | {s['mixed_sections_pct']}% |")
    lines += ["", "«Розрізаний блок» — чанк починається або закінчується посеред абзацу, пункту списку чи рядка таблиці.",
              "«Кілька розділів» — у чанку змішано зміст різних тем рівня h2 (напр. дві різні команди pac CLI). "
              "Structure об'єднує лише дрібні підрозділи однієї теми (параметри однієї команди).", ""]

    for doc_id in ch["comparison_docs"]:
        s_doc = [c for c in structure if c["doc_id"] == doc_id]
        f_doc = [c for c in fixed if c["doc_id"] == doc_id]
        if not s_doc:
            continue
        a, b = stats(s_doc), stats(f_doc)
        lines += [
            f"## {doc_id} ({s_doc[0]['format']})", "",
            "| | structure | fixed |", "|---|---|---|",
            f"| чанків | {a['chunks']} | {b['chunks']} |",
            f"| токенів avg / max | {a['tokens_avg']} / {a['tokens_max']} | {b['tokens_avg']} / {b['tokens_max']} |",
            f"| розрізаний блок | {a['split_block_pct']}% | {b['split_block_pct']}% |",
            f"| кілька розділів | {a['mixed_sections_pct']}% | {b['mixed_sections_pct']}% |",
            "", "Початок другого чанка:", "",
            f"- structure (`{s_doc[min(1, len(s_doc) - 1)]['section']}`): «{s_doc[min(1, len(s_doc) - 1)]['text'][:160]}…»",
            f"- fixed (`{f_doc[min(1, len(f_doc) - 1)]['section']}`): «{f_doc[min(1, len(f_doc) - 1)]['text'][:160]}…»",
            "",
        ]
    return "\n".join(lines) + "\n"


def run_ingest() -> dict:
    cfg = load_rag_config()
    ch = cfg["chunking"]
    out_dir = ROOT / cfg["corpus"]["processed_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    sources = json.loads((ROOT / cfg["corpus"]["sources"]).read_text(encoding="utf-8"))

    documents, structure_all, fixed_all, seen_docs = [], [], [], {}
    for doc in sources:
        raw_path = ROOT / doc["path"]
        blocks, removed = clean_blocks(extract(raw_path, doc["format"]), doc["format"])
        full_text = "\n".join(b["text"] for b in blocks)
        doc_hash = sha(full_text)
        entry = {
            **{k: doc[k] for k in META_FIELDS}, "path": doc["path"],
            "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()[:16], "doc_hash": doc_hash,
            "blocks": len(blocks), "blocks_removed_as_noise": removed, "tokens": count_tokens(full_text),
        }
        if doc_hash in seen_docs:  # документ-дублікат (той самий зміст під іншою назвою/URL)
            documents.append({**entry, "status": "duplicate", "duplicate_of": seen_docs[doc_hash], "chunks": 0})
            continue
        seen_docs[doc_hash] = doc["doc_id"]
        s = build_chunks(doc, structure_chunks(blocks, ch["max_tokens"], ch["min_tokens"]), "structure", doc_hash)
        f = build_chunks(doc, fixed_chunks(blocks, ch["fixed"]["size"], ch["fixed"]["overlap"]), "fixed", doc_hash)
        structure_all += s
        fixed_all += f
        documents.append({**entry, "status": "ok", "chunks_before_dedup": len(s)})

    structure_kept, structure_dropped = drop_duplicates(structure_all)
    fixed_kept, _ = drop_duplicates(fixed_all)
    per_doc = {}
    for c in structure_kept:
        per_doc[c["doc_id"]] = per_doc.get(c["doc_id"], 0) + 1
    for d in documents:
        if d["status"] == "ok":
            d["chunks"] = per_doc.get(d["doc_id"], 0)

    write_jsonl(out_dir / "chunks.jsonl", structure_kept)
    write_jsonl(out_dir / "chunks_fixed.jsonl", fixed_kept)
    manifest = {
        "params": ch,
        "totals": {
            "documents": len(documents),
            "documents_by_format": {f: sum(d["format"] == f for d in documents) for f in sorted({d["format"] for d in documents})},
            "duplicate_documents": sum(d["status"] == "duplicate" for d in documents),
            "chunks": len(structure_kept),
            "duplicate_chunks_removed": len(structure_dropped),
        },
        "documents": documents,
        "duplicate_chunks": structure_dropped,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "chunking_comparison.md").write_text(comparison_report(cfg, structure_kept, fixed_kept), encoding="utf-8")
    return manifest
