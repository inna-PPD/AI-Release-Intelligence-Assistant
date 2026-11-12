"""Сторінка для ручної перевірки тестсету RAG: питання, еталонна відповідь, ключові факти, очікувані джерела.

Запуск: python scripts/testset_review.py → evals/testset_review.md (Ctrl+Shift+V)
Редагувати треба evals/testset.jsonl, а цей .md — перегенерувати.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTSET = ROOT / "evals" / "testset.jsonl"
OUT = ROOT / "evals" / "testset_review.md"
TRAPS = {"none": "—", "version": "застаріла версія", "similar": "схожий документ", "table": "таблиця",
         "cross_lingual": "питання UA → документ EN", "exact_id": "точний ідентифікатор", "synthesis": "кілька кроків/фактів"}


def main():
    items = [json.loads(line) for line in TESTSET.read_text(encoding="utf-8").splitlines() if line.strip()]
    reviewed = sum(i.get("reviewed", False) for i in items)
    answerable = sum(i["category"] == "answerable" for i in items)
    parts = ["# Тестсет RAG — перевірка", "",
             f"{len(items)} питань: {answerable} з відповіддю, {len(items) - answerable} без відповіді. Перевірено автором: **{reviewed} з {len(items)}**.",
             "Перевірте: чи правильна еталонна відповідь за документами, чи справді ключові факти обов'язкові, чи немає відповіді в корпусі для питань «без відповіді».",
             "", "| ID | Тип | Пастка | Питання | Еталон | Ключові факти | Джерела | ✓ |", "|---|---|---|---|---|---|---|---|"]
    for i in items:
        parts.append(f"| {i['id']} | {'з відповіддю' if i['category'] == 'answerable' else '**без відповіді**'} | {TRAPS.get(i['trap'], i['trap'])} "
                     f"| {i['question']} | {i['expected_answer']} | {', '.join(i['key_facts']) or '—'} "
                     f"| {', '.join(i['expected_sources']) or '—'} | {'✅' if i.get('reviewed') else '⏳'} |")
    notes = [f"- **{i['id']}:** {i['note']}" for i in items if i.get("note")]
    if notes:
        parts += ["", "## Примітки", "", *notes]
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Створено: {OUT.relative_to(ROOT)} ({reviewed}/{len(items)} перевірено)")


if __name__ == "__main__":
    main()
