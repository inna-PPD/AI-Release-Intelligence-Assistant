"""Завантажує баг-репорти з публічних GitHub-репозиторіїв Power Platform
і знеособлює їх (імена, @згадки, email, URL, GUID, шляхи з іменами користувачів).

Запуск:
    python scripts/fetch_github_issues.py            # 10 issues з кожного репо
    python scripts/fetch_github_issues.py --per-repo 8

Без токена GitHub дозволяє 60 запитів на годину — цього достатньо.
Якщо задано змінну GITHUB_TOKEN, вона використовується автоматично.

Результат: data/github/defects_github.jsonl
УВАГА: автоматичне знеособлення не ідеальне — перегляньте тексти вручну.
"""

import argparse
import json
import os
import random
import re
import urllib.request
from collections import Counter
from pathlib import Path

REPOS = ["microsoft/coe-starter-kit", "microsoft/powerplatform-build-tools"]
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "github" / "defects_github.jsonl"
MAX_CHARS = 3000
MIN_BODY_CHARS = 80
SEED = 42

# (назва, регулярний вираз, заміна) — порядок важливий: спершу HTML і URL, потім решта
SCRUB_RULES = [
    ("html_comment", re.compile(r"<!--.*?-->", re.S), ""),
    ("image", re.compile(r"<img[^>]*>|!\[[^\]]*\]\([^)]*\)", re.I), "[image]"),
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "<EMAIL>"),
    ("url", re.compile(r"https?://\S+"), "<URL>"),
    ("dynamics_host", re.compile(r"\b[\w-]+\.(crm\d*\.dynamics\.com|sharepoint\.com|powerappsportals\.com)\b", re.I), "<ORG_URL>"),
    ("guid", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<GUID>"),
    ("user_path", re.compile(r"(?i)([A-Z]:\\Users\\)[^\\\s]+"), r"\1<USER>"),
    ("home_path", re.compile(r"(/(?:home|Users)/)[^/\s]+"), r"\1<USER>"),
    # (?!/) — не чіпати npm-пакети на кшталт @microsoft/power-apps
    ("mention", re.compile(r"(?<![\w<])@[A-Za-z0-9][A-Za-z0-9-]{0,38}\b(?!/)"), "@<USER>"),
    # «Thanks,\nJohn Smith» — рядок з іменем після підпису
    ("signature", re.compile(r"(?im)^((?:thanks|thank you|regards|best regards|kind regards|cheers|br)[,!.]?\s*\n)\s*[A-Z][\w'.-]+(?:\s+[A-Z][\w'.-]+)?\s*$"), r"\1<NAME>"),
    # шаблонні чекбокси на кшталт «- [x] I have checked and confirm this is a new bug.»
    ("checkbox", re.compile(r"(?m)^\s*- \[[ xX]\] .*$\n?"), ""),
]


def fetch_json(url: str):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "ai-course-dataset"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def scrub(text: str, author: str, stats: Counter) -> str:
    # логін автора може траплятися в тексті без @
    if author:
        text, n = re.subn(re.escape(author), "<USER>", text, flags=re.I)
        stats["author_login"] += n
    for name, pattern, replacement in SCRUB_RULES:
        text, n = pattern.subn(replacement, text)
        stats[name] += n
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rstrip() + "\n[...]"
    return text


def fetch_bug_issues(repo: str, count: int, rng: random.Random) -> list[dict]:
    url = f"https://api.github.com/repos/{repo}/issues?labels=bug&state=all&per_page=100"
    issues = [
        i for i in fetch_json(url)
        if "pull_request" not in i and len((i.get("body") or "").strip()) >= MIN_BODY_CHARS
    ]
    return rng.sample(issues, min(count, len(issues)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--per-repo", type=int, default=10, help="скільки issues брати з кожного репозиторію")
    args = parser.parse_args()

    rng = random.Random(SEED)
    stats = Counter()
    records = []
    for repo in REPOS:
        for issue in fetch_bug_issues(repo, args.per_repo, rng):
            author = (issue.get("user") or {}).get("login", "")
            text = f"{issue['title']}\n\n{issue['body']}"
            records.append({
                "id": f"gh-{len(records) + 1:03d}",
                "source": "github",
                "channel": "github_issue",
                "origin": f"{repo}#{issue['number']}",
                "text": scrub(text, author, stats),
            })
        print(f"{repo}: взято {sum(r['origin'].startswith(repo) for r in records)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nЗбережено {len(records)} записів у {OUT_PATH}")
    print("Замін при знеособленні:", dict(stats) or "немає")
    print("Перегляньте тексти вручну перед комітом!")


if __name__ == "__main__":
    main()
