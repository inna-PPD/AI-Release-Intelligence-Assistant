"""Завантаження версіонованих промптів з prompts/<name>/<version>.md.

Формат файлу: YAML front matter (version, date, ...) + розділи `## system` і `## user`.
У `## user` плейсхолдер {text} замінюється текстом документа.
"""

import hashlib
import re
from dataclasses import dataclass

import yaml

from src.config import ROOT

PROMPTS_DIR = ROOT / "prompts"
SECTION_RE = re.compile(r"^## (system|user)\s*$", re.M)


@dataclass
class Prompt:
    id: str          # напр. "extract_defect/v1" — потрапляє в кожен запис results/
    system: str
    user_template: str
    sha: str         # хеш файлу: якщо файл версії змінили без нової версії, це видно в results/

    def messages(self, text: str) -> list[dict]:
        # replace, а не format: у баг-репортах трапляються фігурні дужки (JSON, стектрейси)
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user_template.replace("{text}", text)},
        ]


def load_prompt(prompt_id: str) -> Prompt:
    path = PROMPTS_DIR / f"{prompt_id}.md"
    raw = path.read_text(encoding="utf-8")
    _, front, body = raw.split("---", 2)
    meta = yaml.safe_load(front)
    parts = SECTION_RE.split(body)
    sections = dict(zip(parts[1::2], (p.strip() for p in parts[2::2])))
    if f"v{str(meta['version']).lstrip('v')}" != prompt_id.rsplit("/", 1)[-1]:
        raise ValueError(f"{path}: version у front matter не збігається з назвою файлу")
    sha = hashlib.sha256(raw.replace("\r\n", "\n").encode("utf-8")).hexdigest()[:12]
    return Prompt(id=prompt_id, system=sections["system"], user_template=sections["user"], sha=sha)
