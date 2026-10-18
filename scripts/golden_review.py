"""Сторінка для ручної перевірки golden set: оригінальний текст + еталонна розмітка поруч.

Запуск: python scripts/golden_review.py  → data/golden/golden_review.md (відкрити з Ctrl+Shift+V)
Редагувати треба golden_set.json, а цей .md — перегенерувати.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "data" / "golden" / "golden_set.json"
INPUTS = [ROOT / "data" / "synthetic" / "defects_synthetic.jsonl", ROOT / "data" / "github" / "defects_github.jsonl"]
OUT = ROOT / "data" / "golden" / "golden_review.md"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def show(value) -> str:
    if value is None:
        return "`null`"
    if value == []:
        return "`[]`"
    if isinstance(value, bool):
        return f"`{str(value).lower()}`"
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return "<br>".join(f"`{c['type']}` · {c['name'] if c['name'] else '`null`'}" for c in value)
    if isinstance(value, list) and len(value) > 1 and len(" ".join(value)) > 30:  # кроки — нумерованим списком
        return "<br>".join(f"{i}. {v}" for i, v in enumerate(value, 1))
    if isinstance(value, list):
        return ", ".join(f"`{v}`" for v in value)
    return str(value).replace("|", "\\|")


def main():
    texts = {d["id"]: d["text"] for path in INPUTS for d in read_jsonl(path)}
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    reviewed = sum(g.get("reviewed", False) for g in golden)
    parts = [
        "# Golden set — перевірка розмітки",
        "",
        f"Перевірено: **{reviewed} з {len(golden)}**. Правила — [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md).",
        "Виправлення вносяться в `golden_set.json` (поле `expected`), після перевірки — `\"reviewed\": true`.",
    ]
    for g in golden:
        status = "✅ перевірено" if g.get("reviewed") else "⏳ не перевірено"
        rows = "\n".join(f"| `{field}` | {show(value)} |" for field, value in g["expected"].items())
        parts += [
            "", "---", "", f"## {g['id']} — {status}", "",
            "**Оригінальний текст:**", "", "~~~~text", texts[g["id"]].strip(), "~~~~", "",  # ~~~~: у текстах бувають ```
            "| Поле | Еталон |", "|---|---|", rows,
        ]
        if g.get("notes"):
            parts += ["", f"> **Примітка:** {g['notes']}"]
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"Створено: {OUT.relative_to(ROOT)} ({reviewed}/{len(golden)} перевірено)")


if __name__ == "__main__":
    main()
