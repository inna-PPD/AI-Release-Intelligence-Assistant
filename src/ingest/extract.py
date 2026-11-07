"""Витягування тексту зі збереженням структури: документ → список блоків.

Блок — {"kind": "heading" | "paragraph" | "list_item" | "table" | "code", "level": int | None, "text": str}.
Заголовки зберігають рівень (1–4), таблиці — рядки «клітинка | клітинка», щоб chunking міг різати
документ по розділах і не розривати таблиці та списки.
"""

import re
from collections import Counter
from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

BLOCK_TAGS = ["h1", "h2", "h3", "h4", "p", "li", "table", "pre"]
# boilerplate Microsoft Learn усередині <main>: зміст сторінки, feedback, «Additional resources», дата оновлення
HTML_NOISE = ["nav", "script", "style", "button", "form", ".doc-outline", ".page-metadata-container",
              ".action-panel", "section.feedback-section", "#ms--additional-resources", ".display-none-print"]


def block(kind: str, text: str, level: int | None = None) -> dict:
    return {"kind": kind, "level": level, "text": text}


def _table_rows(rows: list[list[str]]) -> str:
    return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows if any(c.strip() for c in row))


# ---------- HTML (Microsoft Learn) ----------

def extract_html(path: Path) -> list[dict]:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    containers = [c for c in soup.select("main div.content") if not c.find_parent("nav")] or [soup.body]
    blocks = []
    for container in containers:
        for selector in HTML_NOISE:
            for el in container.select(selector):
                el.decompose()
        for el in container.find_all(BLOCK_TAGS):
            # вкладені блоки (p у li, li у таблиці) вже враховані в тексті батька
            if el.find_parent(["li", "table", "pre", "p"]) is not None:
                continue
            blocks.extend(_html_block(el))
    return blocks


def _html_block(el: Tag) -> list[dict]:
    if el.name in ("h1", "h2", "h3", "h4"):
        return [block("heading", el.get_text(" ", strip=True), int(el.name[1]))]
    if el.name == "table":
        rows = [[c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])] for tr in el.find_all("tr")]
        return [block("table", _table_rows(rows))]
    if el.name == "pre":
        return [block("code", el.get_text("\n", strip=True))]
    kind = "list_item" if el.name == "li" else "paragraph"
    return [block(kind, el.get_text(" ", strip=True))]


# ---------- Markdown (GitHub release notes) ----------

MD_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
MD_LIST = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")


def extract_markdown(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    blocks, paragraph, table, code = [], [], [], None

    def flush():
        nonlocal paragraph, table
        if paragraph:
            blocks.append(block("paragraph", " ".join(paragraph)))
            paragraph = []
        if table:
            rows = [r.strip().strip("|").split("|") for r in table if not re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", r)]
            blocks.append(block("table", _table_rows(rows)))
            table = []

    for line in lines:
        if line.strip().startswith("```"):
            if code is None:
                flush()
                code = []
            else:
                blocks.append(block("code", "\n".join(code)))
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if line.strip().startswith("|"):
            if paragraph:
                flush()
            table.append(line)
            continue
        if table:
            flush()
        if m := MD_HEADING.match(line):
            flush()
            blocks.append(block("heading", m[2].strip(" #"), min(len(m[1]), 4)))
        elif m := MD_LIST.match(line):
            flush()
            blocks.append(block("list_item", m[1]))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    flush()
    return blocks


# ---------- DOCX ----------

def extract_docx(path: Path) -> list[dict]:
    doc = Document(path)
    blocks = []
    for child in doc.element.body.iterchildren():  # абзаци й таблиці в порядку документа
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            style = p.style.name if p.style is not None else ""
            if style.startswith("Heading") and style[-1].isdigit():
                blocks.append(block("heading", p.text, int(style[-1])))
            elif style == "Title":
                blocks.append(block("heading", p.text, 1))
            elif style.startswith("List"):
                blocks.append(block("list_item", p.text))
            else:
                blocks.append(block("paragraph", p.text))
        elif tag == "tbl":
            table = Table(child, doc)
            blocks.append(block("table", _table_rows([[c.text for c in row.cells] for row in table.rows])))
    return blocks


# ---------- PDF ----------

PDF_BULLET = re.compile(r"^\s*(?:[•●▪◦\-–]|\d+[.)])\s*")


def extract_pdf(path: Path) -> list[dict]:
    """Заголовки визначаються за розміром шрифту відносно основного тексту; колонтитули — рядки,
    що повторюються на більшості сторінок, — відкидаються."""
    doc = pymupdf.open(path)
    lines = []  # (сторінка, розмір шрифту, текст, y)
    tables = {}  # сторінка → [(bbox, текст таблиці)]
    for page_no, page in enumerate(doc):
        found = page.find_tables().tables
        tables[page_no] = [(pymupdf.Rect(t.bbox), _table_rows([[c or "" for c in r] for r in t.extract()])) for t in found]
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                size = max(s["size"] for s in spans)
                table = next((t for t in tables[page_no] if pymupdf.Rect(line["bbox"]).intersects(t[0])), None)
                if table is not None:  # рядок усередині таблиці — таблиця піде окремим блоком
                    lines.append((page_no, -1.0, table[1], table[0].y0))
                    continue
                lines.append((page_no, round(size, 1), text, line["bbox"][1]))
    if not lines:
        return []

    page_count = len(doc)
    repeated = Counter(t for _, s, t, _ in lines if s > 0)
    noise = {t for t, n in repeated.items() if page_count > 1 and n >= max(2, page_count * 0.5)}
    body_size = Counter(s for _, s, _, _ in lines if s > 0).most_common(1)[0][0]
    heading_sizes = sorted({s for _, s, _, _ in lines if s >= body_size * 1.2}, reverse=True)

    blocks, paragraph, prev_y = [], [], None

    def flush():
        nonlocal paragraph
        if paragraph:
            # рядок, що закінчується дефісом, — перенос усередині слова/імені (svc-│contoso-flows): без пробілу
            text = "".join(line if line.endswith("-") else line + " " for line in paragraph).strip()
            kind = "list_item" if PDF_BULLET.match(paragraph[0]) else "paragraph"
            blocks.append(block(kind, PDF_BULLET.sub("", text, count=1) if kind == "list_item" else text))
            paragraph = []

    emitted_tables = set()
    for page_no, size, text, y in lines:
        if size < 0:  # таблиця: додаємо один раз
            if (page_no, y) not in emitted_tables:
                flush()
                blocks.append(block("table", text))
                emitted_tables.add((page_no, y))
            prev_y = None
            continue
        if text in noise:
            continue
        if size in heading_sizes:
            flush()
            level = heading_sizes.index(size) + 1
            prev = blocks[-1] if blocks else None
            if prev and prev["kind"] == "heading" and prev["level"] == level and prev.get("page") == page_no:
                prev["text"] += " " + text  # довгий заголовок, перенесений на наступний рядок
            else:
                blocks.append({**block("heading", text, level), "page": page_no})
        elif PDF_BULLET.match(text) or (prev_y is not None and y - prev_y > size * 1.8):
            flush()  # новий пункт списку або вертикальний розрив = новий абзац
            paragraph.append(text)
        else:
            paragraph.append(text)
        prev_y = y
    flush()
    return blocks


EXTRACTORS = {"html": extract_html, "md": extract_markdown, "docx": extract_docx, "pdf": extract_pdf}


def extract(path: Path, fmt: str) -> list[dict]:
    return EXTRACTORS[fmt](path)
