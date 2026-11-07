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

## Кейс 2 — RAG на власних даних + Evals

Документи → очищення → чанки з метаданими → hybrid search → відповідь з джерелами → evals у CI.
Корпус — 42 документи у 4 форматах (HTML, Markdown, DOCX, PDF): Microsoft Learn, release notes CoE Starter Kit, синтетичні документи Contoso. Деталі й ліцензії — [data/corpus/README.md](data/corpus/README.md).

### Ingestion (крок 1)

`python main.py ingest` → `data/processed/chunks.jsonl` + `manifest.json`:

1. **Витягування зі збереженням структури** ([src/ingest/extract.py](src/ingest/extract.py)): заголовки з рівнями, пункти списків, таблиці (рядки «клітинка | клітинка»), код. HTML — лише `main div.content` сторінки Learn; DOCX — стилі Heading / List і таблиці в порядку документа; PDF — заголовки за розміром шрифту, таблиці через `find_tables`, колонтитули — рядки, що повторюються на більшості сторінок.
2. **Очищення** ([src/ingest/clean.py](src/ingest/clean.py)): Unicode NFC, BOM / zero-width / soft hyphen, `\r\n`; Markdown-розмітка й HTML-теги в release notes; переноси рядків у PDF; boilerplate Learn («In this article», «Feedback», «Additional resources», дата оновлення) і навігаційні розділи «See also» / «Next step».
3. **Дедуплікація**: документи — SHA-256 очищеного тексту; чанки — хеш нормалізованого тексту (регістр, пробіли). Прибрано **62 дублікати чанків** — здебільшого однакові розділи «First Time Setup Instructions» / «Upgrade Instructions», що повторюються в кожному релізі CoE Kit і інакше забивали б top-k.
4. **Метадані чанка**: `source`, `url`, `title`, `section` (ланцюжок заголовків), `version`, `date`, `doc_hash`, `content_hash`, `format`, `product`, `license`.

### Chunking: чому за структурою, а не фіксованою довжиною

**Стратегія:** чанк = розділ документа (заголовок + його зміст); блок (пункт списку, абзац, рядок таблиці) не розривається. Розділ, довший за **300 токенів**, пакується блоками до ліміту; завелика таблиця ділиться по рядках із повтором шапки. Дрібні (< 60 токенів) сусідні підрозділи **однієї теми** (напр. параметри однієї команди `pac`) об'єднуються. Заголовок ніколи не відривається від змісту.

**Чому саме так для цих документів:**
- **Документи вже поділені на смислові одиниці**, і питання спрямовані саме на них: «що змінилось у CoE Kit у лютому 2026», «які параметри в `pac solution pack`», «який крок встановлення 1.5 іде першим». Release notes — список змін, довідка pac CLI — команда → параметри, інструкція — нумеровані кроки, тест-план — таблиця. Розділ = відповідь на одне питання і правильне джерело для цитати «документ + розділ».
- **300 токенів:** пункт release notes — 15–40 токенів, типовий розділ h2 — 100–300; ліміт вміщує розділ цілком, а великі списки змін (25–50 bug fixes у релізі) ділить на кілька чанків. Запас до ліміту embedding-моделі (512 токенів) лишається на контекстний заголовок і на те, що кирилиця дає більше токенів.
- **Overlap не потрібен:** межі чанків збігаються з межами блоків, тож речення не обриваються. Контекст сусідніх чанків замінює **contextual header** — у текст для embedding додається назва документа й розділ (`embed_text`). Без нього чанк «### Remarks» чи «## Порядок встановлення» неможливо прив'язати до команди чи версії, а версія релізу живе саме в назві документа.

**Порівняння з фіксованою довжиною** (300 токенів, overlap 50) — [data/processed/chunking_comparison.md](data/processed/chunking_comparison.md):

| | structure | fixed |
|---|---|---|
| чанків | 404 | 252 |
| токенів avg / max | 141 / 316 | 280 / 301 |
| чанки, що починаються / закінчуються **посеред блоку** | **9%** (лише завеликі таблиці й списки) | **97%** |
| чанки, що змішують **різні теми h2** | **0%** | **52%** |

На прикладах: фіксований чанк інструкції 1.5 починається з «…овнити environment variables cnt_LeoApiKey» (обрізане слово і крок без початку), а чанк довідки `pac solution` склеює кінець однієї команди з початком іншої — embedding такого чанка «розмитий», а цитата вказує на неправильний розділ. Вплив на якість пошуку (recall@k для обох стратегій) — у кроці 2.

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
python main.py ingest           # кейс 2: корпус → data/processed/chunks.jsonl + manifest.json
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
config/rag.yaml         кейс 2: параметри chunking, корпусу
data/                   вхідні тексти (synthetic/, github/) і golden set (golden/)
data/corpus/            кейс 2: сирі документи (raw/html, md, docx, pdf) + sources.json
data/processed/         кейс 2: chunks.jsonl, manifest.json, порівняння chunking
src/ingest/             кейс 2: витягування, очищення, chunking, ingestion-пайплайн
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
