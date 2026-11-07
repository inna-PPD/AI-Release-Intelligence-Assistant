"""Очищення й нормалізація блоків після витягування.

- кодування: Unicode NFC, BOM, zero-width і soft hyphen, нерозривні пробіли, \\r\\n;
- Markdown-розмітка в тексті: посилання, картинки, жирний/курсив, HTML-теги з release notes;
- артефакти HTML: пробіл перед розділовими знаками після get_text(" ");
- boilerplate: службові рядки сторінок («In this article», «Feedback», «Last updated on ...»), порожні блоки.
"""

import re
import unicodedata

INVISIBLE = dict.fromkeys(map(ord, "﻿​‌‍⁠­"))
BOILERPLATE = re.compile(
    r"^(in this article|feedback|was this page helpful\??|additional resources|"
    r"last updated on .*|submit and view feedback for.*|table of contents|show \d+ more)$",
    re.I,
)
NAV_SECTION = re.compile(r"^(see also|next steps?|related (content|articles|information))$", re.I)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(INVISIBLE)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    return text


def strip_markdown(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                  # картинки
    text = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)", r"\1", text)  # [текст](url) → текст
    text = re.sub(r"<img[^>]*>|<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"</?[a-z][^>]*>", "", text, flags=re.I)               # інші inline-теги
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)                      # жирний
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", text)  # курсив *x*
    return text


def tidy(text: str, keep_newlines: bool) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" +([.,;:!?)])", r"\1", text)   # «unmanaged .» → «unmanaged.»
    text = re.sub(r"\( +", "(", text)
    if keep_newlines:
        text = "\n".join(line.strip() for line in text.split("\n"))
        return re.sub(r"\n{3,}", "\n\n", text).strip()
    return re.sub(r"\s*\n\s*", " ", text).strip()


def clean_blocks(blocks: list[dict], fmt: str) -> tuple[list[dict], int]:
    """Повертає (очищені блоки, кількість відкинутих)."""
    cleaned, skip_level = [], None
    for b in blocks:
        text = normalize_text(b["text"])
        if fmt == "md" and b["kind"] != "code":
            text = strip_markdown(text)
        text = tidy(text, keep_newlines=b["kind"] in ("table", "code"))
        if b["kind"] == "heading":
            if skip_level is not None and b["level"] <= skip_level:
                skip_level = None
            if NAV_SECTION.match(text):  # «See also», «Next step» — лише посилання на інші сторінки
                skip_level = b["level"]
        if skip_level is not None or not text or BOILERPLATE.match(text):
            continue
        cleaned.append({**b, "text": text})
    return cleaned, len(blocks) - len(cleaned)
