# AI Release Intelligence Assistant

AI-система, яка аналізує релізну документацію й баг-репорти рішень на Microsoft Power Platform, структурує їх, шукає по них і формує рекомендації для оновлення й тестування.
Курсовий проєкт AI Engineering; повна специфікація — [docs/SPEC.md](docs/SPEC.md).

> Усі дані в репозиторії публічні (GitHub issues Microsoft, знеособлені) або синтетичні (вигадана компанія Contoso).

## Кейс 1 — Structured Extraction Service

Сирий баг-репорт (Teams, email, Azure DevOps, GitHub) → валідний JSON за схемою [`DefectReport`](src/schema.py).
Порівнюються провайдерська модель (OpenRouter) і локальна (Ollama).

**Результат** (повний звіт — [REPORT.md](REPORT.md)):

| Модель | Промпт | Field accuracy | Валідних | p95 | $ / 1000 док. |
|---|---|---|---|---|---|
| **gpt-4o-mini** (обрано) | v2 | **0.91** | 100% | 3.8 с | 0.66 |
| qwen2.5:7b (локально) | v2 | 0.73 | 100% | 19.4 с | 0 |

## Встановлення

Потрібно: Python 3.11+, ключ [OpenRouter](https://openrouter.ai/keys), [Ollama](https://ollama.com).

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # впишіть OPENROUTER_API_KEY
ollama pull qwen2.5:7b-instruct
```

## Запуск

```bash
python main.py run              # або: make run — обидві моделі × семплінг A, B, промпт v2
python main.py eval             # метрики по всіх results/*.jsonl → results/metrics.md, metrics.csv
```

Корисні варіанти:

```bash
python main.py run --models provider --sampling A --limit 3   # швидка перевірка
python main.py run --prompt extract_defect/v1                 # baseline-промпт
python main.py run --models local_json --sampling A           # без схеми: демонстрація валідації й repair
python -m pytest -q                                           # тести (без API)
```

Результати кожного прогону — `results/<дата>_<модель>_<промпт>_<семплінг>.jsonl`:
модель, версія і хеш промпту, параметри семплінгу, статус (`ok` / `repaired` / `failed`), токени, latency, вартість і сам JSON.

## Структура

```
config/models.yaml      моделі, ціни, семплінг, налаштування extraction
data/                   вхідні тексти (synthetic/, github/) і golden set (golden/)
prompts/extract_defect/ версії промптів (v1, v2) + CHANGELOG.md
src/schema.py           Pydantic-схема DefectReport
src/llm/                спільний інтерфейс LLMClient: OpenRouter, Ollama (retry, timeout)
src/extraction/         промпти й пайплайн: модель → валідація → repair → запис
src/evaluation/         field accuracy, % валідних, latency p50/p95, вартість
results/                виходи моделей + metrics.md / metrics.csv
REPORT.md               звіт-порівняння і вибір моделі для продакшну
scripts/                завантаження й перегляд даних
docs/SPEC.md            специфікація всього проєкту
```

## Дані

| Набір | К-сть | Джерело |
|---|---|---|
| `data/synthetic/defects_synthetic.jsonl` | 20 | згенеровано, див. [GENERATION.md](data/synthetic/GENERATION.md) |
| `data/github/defects_github.jsonl` | 20 | issues `microsoft/coe-starter-kit`, `microsoft/powerplatform-build-tools`, знеособлено скриптом [fetch_github_issues.py](scripts/fetch_github_issues.py) |
| `data/golden/golden_set.json` | 10 | еталонна розмітка, перевірена вручну; правила — [ANNOTATION_GUIDE.md](data/golden/ANNOTATION_GUIDE.md) |
