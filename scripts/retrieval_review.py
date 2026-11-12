"""Сторінка для ручної перевірки питань оцінки пошуку: питання → очікуваний документ і фраза → сам чанк.

Запуск: python scripts/retrieval_review.py → evals/retrieval_review.md (відкрити з Ctrl+Shift+V)
Редагувати треба evals/retrieval_questions.jsonl, а цей .md — перегенерувати.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "evals" / "retrieval_questions.jsonl"
CHUNKS = ROOT / "data" / "processed" / "chunks.jsonl"
OUT = ROOT / "evals" / "retrieval_review.md"

TYPES = {
    "same_language": "мова питання = мова документа",
    "cross_lingual": "питання українською, документ англійською",
    "exact_id": "точний ідентифікатор (номер issue)",
    "table": "відповідь у таблиці",
    "similar_docs": "є схожий документ-пастка",
    "version_trap": "є застаріла версія документа",
    "paraphrase": "перефразоване питання без ключових слів документа",
    "multi_relevant": "правильних чанків кілька",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main():
    chunks = read_jsonl(CHUNKS)
    questions = read_jsonl(QUESTIONS)
    reviewed = sum(q.get("reviewed", False) for q in questions)
    parts = [
        "# Питання для оцінки пошуку — перевірка",
        "",
        f"Перевірено автором: **{reviewed} з {len(questions)}**.",
        f"Для кожного питання: чи це реалістичне питання користувача і чи справді показаний чанк на нього відповідає.",
        "Виправлення — у `evals/retrieval_questions.jsonl`, потім `python scripts/retrieval_review.py`.",
    ]
    for q in questions:
        status = "✅" if q.get("reviewed") else "⏳ не перевірено"
        level = "складне" if q.get("set") == "hard" else "базове"
        parts += ["", "---", "", f"## {q['id']} · {level} · {TYPES.get(q['type'], q['type'])} · {status}", "",
                  f"**Питання:** {q['question']}", ""]
        for rel in q["relevant"]:
            found = [c for c in chunks if c["doc_id"] == rel["doc_id"] and rel["contains"].lower() in c["text"].lower()]
            parts.append(f"**Очікується:** документ `{rel['doc_id']}`, чанк містить «{rel['contains']}» — знайдено чанків: {len(found)}")
            for c in found:
                parts += ["", f"`{c['chunk_id']}` · {c['title']} › {c['section']}", "", "~~~~text", c["text"].strip(), "~~~~"]
        if q.get("note"):
            parts += ["", f"> **Примітка:** {q['note']}"]
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Створено: {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
