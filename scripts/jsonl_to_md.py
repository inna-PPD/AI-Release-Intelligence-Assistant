"""Робить з JSONL читабельний Markdown для перегляду (Ctrl+Shift+V у VS Code).

JSONL лишається основним форматом для коду; .md — лише для очей, його можна перегенерувати.

Запуск:
    python scripts/jsonl_to_md.py data/github/defects_github.jsonl
    python scripts/jsonl_to_md.py data/synthetic/defects_synthetic.jsonl
"""

import json
import re
import sys
from pathlib import Path


def to_markdown_body(text: str) -> str:
    # заголовки всередині тексту робимо жирними, щоб не ламали структуру документа
    text = re.sub(r"(?m)^#{1,6}\s*(.+)$", r"**\1**", text)
    # обрізаний текст може мати незакритий блок коду — закриваємо
    if text.count("```") % 2:
        text += "\n```"
    return text


def convert(path: Path) -> Path:
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    parts = [f"# {path.name}\n\n{len(records)} записів. Згенеровано з `{path.name}`, не редагуйте вручну.\n"]
    for r in records:
        meta = " · ".join(f"`{k}: {v}`" for k, v in r.items() if k not in ("id", "text"))
        parts.append(f"---\n\n## {r['id']}\n\n{meta}\n\n{to_markdown_body(r['text'])}\n")
    out = path.with_suffix(".md")
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for arg in sys.argv[1:]:
        print("Створено:", convert(Path(arg)))
