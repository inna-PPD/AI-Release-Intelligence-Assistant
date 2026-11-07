import json
from pathlib import Path

from src.config import ROOT
from src.ingest.chunking import count_tokens, fixed_chunks, split_sections, structure_chunks
from src.ingest.clean import clean_blocks
from src.ingest.extract import extract_markdown
from src.ingest.pipeline import drop_duplicates


def b(kind, text, level=None):
    return {"kind": kind, "level": level, "text": text}


def test_markdown_keeps_structure(tmp_path: Path):
    md = tmp_path / "r.md"
    md.write_bytes("## Change Log\r\n- fix **one** [link](https://x.y)\r\n\r\n| a | b |\r\n|---|---|\r\n| 1 | 2 |\r\n".encode())
    blocks = extract_markdown(md)
    assert [x["kind"] for x in blocks] == ["heading", "list_item", "table"]
    assert blocks[0]["level"] == 2 and blocks[2]["text"] == "a | b\n1 | 2"


def test_clean_removes_markup_noise_and_nav_sections():
    blocks = [
        b("heading", "Intro", 1), b("paragraph", "managed **solutions** are [deployed](http://u) ."),
        b("paragraph", "Was this page helpful?"), b("heading", "See also", 2), b("list_item", "Other page"),
        b("heading", "Next topic", 2), b("paragraph", "Text­ here​"),
    ]
    cleaned, removed = clean_blocks(blocks, "md")
    texts = [x["text"] for x in cleaned]
    assert "managed solutions are deployed." in texts
    assert "Other page" not in texts and "See also" not in texts and "Was this page helpful?" not in texts
    assert "Text here" in texts and removed == 3


def test_sections_carry_heading_path():
    sections = split_sections([b("heading", "Guide", 1), b("heading", "Install", 2), b("paragraph", "x"),
                               b("heading", "Check", 2), b("paragraph", "y")])
    assert [s["path"] for s in sections] == [["Guide"], ["Guide", "Install"], ["Guide", "Check"]]


def test_structure_chunks_respect_limit_and_keep_blocks_whole():
    items = [b("list_item", f"Item {i}: " + "word " * 30) for i in range(40)]
    chunks = structure_chunks([b("heading", "Notes", 1), *items], max_tokens=120, min_tokens=20)
    assert all(count_tokens(c["text"]) <= 120 for c in chunks)
    joined = "\n".join(c["text"] for c in chunks)
    assert all(("- " + i["text"]) in joined for i in items)  # жоден пункт не розрізано


def test_oversized_table_is_split_by_rows_with_header():
    rows = "\n".join(f"TC-{i} | компонент | сценарій перевірки номер {i}" for i in range(60))
    chunks = structure_chunks([b("heading", "Plan", 1), b("table", "ID | Компонент | Сценарій\n" + rows)], 100, 20)
    assert len(chunks) > 1
    assert all("ID | Компонент | Сценарій" in c["text"] for c in chunks)
    assert all(c["split_block"] for c in chunks)


def test_fixed_chunks_overlap():
    blocks = [b("paragraph", "token " * 500)]
    chunks = fixed_chunks(blocks, size=100, overlap=20)
    assert len(chunks) >= 5 and all(count_tokens(c["text"]) <= 101 for c in chunks)


def test_drop_duplicates_keeps_first():
    rows = [{"chunk_id": "a#0", "content_hash": "h1"}, {"chunk_id": "b#0", "content_hash": "h1"},
            {"chunk_id": "b#1", "content_hash": "h2"}]
    kept, dropped = drop_duplicates(rows)
    assert [r["chunk_id"] for r in kept] == ["a#0", "b#1"]
    assert dropped == [{"chunk_id": "b#0", "duplicate_of": "a#0"}]


def test_processed_chunks_have_metadata():
    path = ROOT / "data" / "processed" / "chunks.jsonl"
    chunks = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    required = {"chunk_id", "doc_id", "title", "source", "format", "section", "doc_hash", "text", "embed_text"}
    assert chunks and all(required <= c.keys() for c in chunks)
    assert len({c["content_hash"] for c in chunks}) == len(chunks)  # дублікатів немає
    assert {c["format"] for c in chunks} >= {"html", "md", "docx", "pdf"}
