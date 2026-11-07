"""Дві стратегії chunking: структурна (основна) і фіксована (для порівняння).

structure — ріжемо по розділах (заголовках). Блок (пункт списку, абзац, таблиця) ніколи не розривається;
    якщо розділ більший за max_tokens — пакуємо блоки до ліміту; завеликий блок ділимо по рядках таблиці
    (з повтором заголовка) або по реченнях. Сусідні дрібні розділи (< min_tokens) об'єднуються.
fixed — вікно фіксованої довжини з перекриттям поверх суцільного тексту, без огляду на структуру.
"""

import re
from functools import lru_cache

import tiktoken


@lru_cache(maxsize=1)
def _encoder():
    return tiktoken.get_encoding("o200k_base")


def count_tokens(text: str) -> int:
    return len(_encoder().encode(text))


def render_block(b: dict) -> str:
    if b["kind"] == "heading":
        return "#" * b["level"] + " " + b["text"]
    if b["kind"] == "list_item":
        return "- " + b["text"]
    return b["text"]


# ---------- structure-aware ----------

def split_sections(blocks: list[dict]) -> list[dict]:
    """Розділ = заголовок + блоки до наступного заголовка; path — ланцюжок заголовків (h1 > h2 > h3)."""
    sections, stack = [], []
    current = {"path": [], "blocks": []}
    for b in blocks:
        if b["kind"] == "heading":
            if current["blocks"]:
                sections.append(current)
            stack = [h for h in stack if h[0] < b["level"]] + [(b["level"], b["text"])]
            current = {"path": [t for _, t in stack], "blocks": [b]}
        else:
            current["blocks"].append(b)
    if current["blocks"]:
        sections.append(current)
    return sections


def _split_oversized(b: dict, max_tokens: int) -> list[dict]:
    """Завеликий блок: таблиця — по рядках з повтором шапки; інше — по реченнях / рядках."""
    if b["kind"] == "table":
        header, *rows = b["text"].split("\n")
        parts, current = [], []
        for row in rows:
            if current and count_tokens("\n".join([header, *current, row])) > max_tokens:
                parts.append(current)
                current = []
            current.append(row)
        parts.append(current)
        return [{**b, "text": "\n".join([header, *p]), "split": True} for p in parts if p]
    # речення; у release notes — ще й перед кожним URL (списки issue без розділових знаків)
    units = b["text"].split("\n") if b["kind"] == "code" else re.split(r"(?<=[.!?])\s+|\s+(?=https?://)", b["text"])
    parts, current = [], ""
    for unit in units:
        candidate = f"{current}\n{unit}" if b["kind"] == "code" and current else f"{current} {unit}".strip()
        if current and count_tokens(candidate) > max_tokens:
            parts.append(current)
            current = unit
        else:
            current = candidate
    parts.append(current)
    # запасний варіант: одиниця сама довша за ліміт — ріжемо по токенах
    enc, final = _encoder(), []
    for p in parts:
        ids = enc.encode(p)
        final += [enc.decode(ids[i:i + max_tokens]) for i in range(0, len(ids), max_tokens)] if len(ids) > max_tokens else [p]
    return [{**b, "text": p, "split": True} for p in final if p.strip()]


def topic(path: list[str]) -> str:
    """Тема = заголовки до рівня h2 (h1 > h2): напр. одна команда pac CLI або один розділ release notes."""
    return " > ".join(path[:2])


def structure_chunks(blocks: list[dict], max_tokens: int, min_tokens: int) -> list[dict]:
    """→ [{"section", "text", "split_block": чи містить шматок розрізаного блоку, "mixed_sections"}]"""
    # 1) дрібні сусідні підрозділи однієї теми (напр. параметри однієї команди) об'єднуємо,
    #    щоб не було чанків на 1 рядок; різні теми не змішуємо
    merged = []
    for sec in split_sections(blocks):
        size = count_tokens("\n".join(render_block(b) for b in sec["blocks"]))
        prev = merged[-1] if merged else None
        same_topic = prev and (prev["topic"] == topic(sec["path"])  # підрозділи однієї теми
                               or topic(sec["path"]).startswith(prev["topic"] + " > "))  # вступ h1 + перший h2
        prev_only_headings = prev and all(b["kind"] == "heading" for b in prev["blocks"])
        fits = prev and (prev["tokens"] + size <= max_tokens or prev_only_headings)  # «## Change Log» + «### Bugs»
        if prev and same_topic and prev["tokens"] < min_tokens and fits:
            prev["blocks"] += sec["blocks"]
            prev["titles"].append(" > ".join(sec["path"]))
            prev["tokens"] += size
        else:
            merged.append({"titles": [" > ".join(sec["path"])], "topic": topic(sec["path"]),
                           "blocks": list(sec["blocks"]), "tokens": size})

    # 2) пакуємо блоки розділу в чанки ≤ max_tokens, не розриваючи блоки
    chunks = []
    for sec in merged:
        # розділ = перший підрозділ; якщо об'єднано кілька — «… (+N)»
        section = (sec["titles"][0] or "(без розділу)") + (f" (+{len(sec['titles']) - 1})" if len(sec["titles"]) > 1 else "")
        mixed = False  # об'єднуються лише підрозділи однієї теми
        lines, split = [], False

        def emit():
            chunks.append({"section": section, "text": "\n".join(lines), "split_block": split, "mixed_sections": mixed})

        for b in sec["blocks"]:
            pieces = [b] if count_tokens(render_block(b)) <= max_tokens else _split_oversized(b, max_tokens)
            for piece in pieces:
                text = render_block(piece)
                only_headings = all(line.startswith("#") for line in lines)
                # заголовок не відриваємо від змісту: max_tokens — м'яка межа на довжину заголовка
                if lines and not only_headings and count_tokens("\n".join([*lines, text])) > max_tokens:
                    emit()
                    lines, split = [], False
                lines.append(text)
                split = split or piece.get("split", False)
        if lines:
            emit()
    return chunks


# ---------- fixed-size (baseline) ----------

def fixed_chunks(blocks: list[dict], size: int, overlap: int) -> list[dict]:
    """Суцільний текст → вікна по `size` токенів з перекриттям `overlap`. Розділ — той, де вікно починається."""
    enc = _encoder()
    tokens, owners, topics, boundaries = [], [], [], {0}
    for sec in split_sections(blocks):
        path = " > ".join(sec["path"]) or "(без розділу)"
        for b in sec["blocks"]:
            piece = enc.encode(render_block(b) + "\n")
            tokens += piece
            owners += [path] * len(piece)
            topics += [topic(sec["path"])] * len(piece)
            boundaries.add(len(tokens))  # тут закінчується блок
    chunks, step = [], size - overlap
    for start in range(0, max(len(tokens) - overlap, 1), step):
        end = min(start + size, len(tokens))
        chunks.append({
            "section": owners[start],
            "text": enc.decode(tokens[start:end]).strip(),
            "split_block": start not in boundaries or end not in boundaries,  # починається/закінчується посеред блоку
            "mixed_sections": len(set(topics[start:end])) > 1,  # зміст різних тем (h2) в одному чанку
        })
    return chunks
