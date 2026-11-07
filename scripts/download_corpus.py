"""Завантажує публічну частину RAG-корпусу (кейс 2).

- HTML: сторінки Microsoft Learn про pac CLI, ALM і CoE Starter Kit (CC BY 4.0)
- Markdown: release notes CoE Starter Kit з GitHub Releases (MIT)

Сирі файли зберігаються як є (з HTML-boilerplate, \\r\\n тощо) — очищення робить ingestion.
Метадані кожного документа → data/corpus/sources.json (його доповнює generate_contoso_docs.py).

Запуск: python scripts/download_corpus.py
"""

import json
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "corpus" / "raw"
SOURCES = ROOT / "data" / "corpus" / "sources.json"

LEARN_BASE = "https://learn.microsoft.com/en-us/power-platform/"
LEARN_PAGES = {
    # doc_id: (шлях, продукт)
    "learn-cli-introduction": ("developer/cli/introduction", "pac CLI"),
    "learn-cli-solution": ("developer/cli/reference/solution", "pac CLI"),
    "learn-cli-package": ("developer/cli/reference/package", "pac CLI"),
    "learn-cli-pcf": ("developer/cli/reference/pcf", "pac CLI"),
    "learn-alm-basics": ("alm/basics-alm", "ALM"),
    "learn-alm-solution-concepts": ("alm/solution-concepts-alm", "ALM"),
    "learn-alm-solution-layers": ("alm/solution-layers-alm", "ALM"),
    "learn-alm-update-solutions": ("alm/update-solutions-alm", "ALM"),
    "learn-alm-environment-strategy": ("alm/environment-strategy-alm", "ALM"),
    "learn-alm-source-control": ("alm/use-source-control-solution-files", "ALM"),
    "learn-alm-build-tools": ("alm/devops-build-tools", "Power Platform Build Tools"),
    "learn-alm-pipelines": ("alm/pipelines", "Power Platform Pipelines"),
    "learn-coe-setup": ("guidance/coe/setup", "CoE Starter Kit"),
    "learn-coe-after-setup": ("guidance/coe/after-setup", "CoE Starter Kit"),
    "learn-coe-faq": ("guidance/coe/faq", "CoE Starter Kit"),
}

COE_REPO = "microsoft/coe-starter-kit"
COE_SINCE = "2024-06-01"  # релізи CoE Kit від цієї дати (≈ 17 штук)


def fetch_learn(client: httpx.Client) -> list[dict]:
    docs = []
    for doc_id, (path, product) in LEARN_PAGES.items():
        url = LEARN_BASE + path
        html = client.get(url).raise_for_status().text
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1).split(" - ")[0].strip()
        date = re.search(r'name="ms.date" content="([^"]+)"', html)
        out = RAW / "html" / f"{doc_id}.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        docs.append({
            "doc_id": doc_id, "title": title, "format": "html", "path": out.relative_to(ROOT).as_posix(),
            "source": "microsoft_learn", "url": url, "product": product,
            "date": date.group(1)[:10] if date else None, "version": None, "license": "CC BY 4.0",
        })
        print(f"html  {doc_id}: {title}")
    return docs


def coe_version(tag: str) -> str:
    """CoEStarterKit-February2026 → 'February 2026'; HF-релізи зберігають суфікс."""
    name = tag.removeprefix("CoEStarterKit-")
    return re.sub(r"([A-Za-z]+)(\d{2,4})", lambda m: f"{m[1].capitalize()} {m[2] if len(m[2]) == 4 else '20' + m[2]}", name)


def fetch_coe_releases(client: httpx.Client) -> list[dict]:
    releases = client.get(f"https://api.github.com/repos/{COE_REPO}/releases?per_page=100").raise_for_status().json()
    docs = []
    for rel in releases:
        tag, published = rel["tag_name"], rel["published_at"][:10]
        if published < COE_SINCE or not tag.startswith("CoEStarterKit-") or "Preview" in tag or len(rel["body"] or "") < 1000:
            continue
        doc_id = "coe-release-" + re.sub(r"[^a-z0-9]+", "-", tag.removeprefix("CoEStarterKit-").lower()).strip("-")
        out = RAW / "md" / f"{doc_id}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(rel["body"].encode("utf-8"))  # як є, з \r\n
        version = coe_version(tag)
        docs.append({
            "doc_id": doc_id, "title": f"CoE Starter Kit release notes — {version}", "format": "md",
            "path": out.relative_to(ROOT).as_posix(), "source": "github_release", "url": rel["html_url"],
            "product": "CoE Starter Kit", "date": published, "version": version, "license": "MIT",
        })
        print(f"md    {doc_id}: {version} ({published})")
    return docs


def main():
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "ai-course-corpus"}) as client:
        public = fetch_learn(client) + fetch_coe_releases(client)
    existing = json.loads(SOURCES.read_text(encoding="utf-8")) if SOURCES.exists() else []
    synthetic = [d for d in existing if d["source"] == "synthetic"]
    SOURCES.write_text(json.dumps(public + synthetic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nПублічних документів: {len(public)} → {SOURCES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
