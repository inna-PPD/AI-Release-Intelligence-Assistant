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

На прикладах: фіксований чанк інструкції 1.5 починається з «…овнити environment variables cnt_LeoApiKey» (обрізане слово і крок без початку), а чанк довідки `pac solution` склеює кінець однієї команди з початком іншої — embedding такого чанка «розмитий», а цитата вказує на неправильний розділ. Вплив на якість пошуку — нижче: структурний chunking дає MRR 0.89 проти 0.74 у фіксованого за того самого векторного пошуку.

### Індекс і hybrid search (крок 2)

| Компонент | Вибір | Чому |
|---|---|---|
| Embeddings | `google/embeddinggemma-300m` через fastembed (ONNX, CPU) | 100+ мов (питання українською → англійські документи), до 2048 токенів (у `paraphrase-multilingual-MiniLM` лише 128 — обрізала б чанки), працює без GPU і в GitHub Actions. Промпти моделі (`task: search result \| query:` / `title: … \| text:`) додаються вручну — fastembed їх не додає |
| Кеш embeddings | `data/index/vectors_*.npz`, ключ — хеш тексту | повний перерахунок 404 чанків — ~3 хв на CPU; перераховуються лише нові/змінені |
| Векторна база | Qdrant у локальному режимі (`data/index/qdrant`, без сервера) | косинусна схожість + фільтри payload; колекція перебудовується з кешу за секунди |
| Лексичний пошук | BM25 (`rank-bm25`), токени на кшталт `1.46.1`, `cnt_invoice`, `#9508` зберігаються цілими й частинами | точні ідентифікатори, які вектор «розмиває» |
| Об'єднання | Reciprocal Rank Fusion (k = 60), по 20 кандидатів з кожного пошуку | не залежить від різного масштабу оцінок BM25 і косинусної схожості |
| Reranking | `BAAI/bge-reranker-v2-m3-int8` (cross-encoder, багатомовний, INT8) | читає питання й чанк разом, пересортовує 20 кандидатів → top-5 |
| Фільтри | `product`, `source`, `format`, `doc_id`, `version`, `date_from` / `date_to` | Qdrant `MatchAny` / `Range` + той самий предикат для BM25 |

```bash
python main.py search "Яка мінімальна версія pac CLI для Contoso 1.5?"
python main.py search "Sync Audit Logs flow fixes" --filter "product=CoE Starter Kit" --filter date_from=2025-10-01
python main.py retrieval-eval        # → evals/results/retrieval_metrics.md
```

**Якість пошуку** — 25 питань з відомим правильним чанком ([evals/retrieval_questions.jsonl](evals/retrieval_questions.jsonl)); ручна перевірка кожного питання — [evals/retrieval_review.md](evals/retrieval_review.md). Правильний чанк задано парою «документ + фраза», тож та сама розмітка працює для обох chunking-стратегій. Повна таблиця з рангом по кожному питанню — [evals/results/retrieval_metrics.md](evals/results/retrieval_metrics.md).

- **Базові (15):** українські питання до англійських документів, точні номери issue, таблиці, застаріла версія інструкції.
- **Складні (10)** — додані після фідбеку на чекпоінті, бо на базових найкраща конфігурація давала 1.00 і тест перестав розрізняти зміни: той самий заголовок «BUGS (N)» у 18 релізах, «Sync Audit Logs (V2)» у 17 чанках різних місяців, `--packagetype` у трьох командах з різним описом, перефразування без ключових слів документа, два правильні релізи.

| Chunking | Промпти | Пошук | MRR@10 (усі 25) | recall@1 | recall@5 | Базові: recall@1 / MRR | **Складні: recall@1 / MRR** |
|---|---|---|---|---|---|---|---|
| structure | так | vector | 0.83 | 0.72 | 1.00 | 0.80 / 0.89 | 0.60 / 0.75 |
| structure | так | bm25 | 0.71 | 0.64 | 0.84 | 0.73 / 0.81 | 0.50 / 0.56 |
| structure | так | hybrid | 0.89 | 0.84 | 0.92 | 0.80 / 0.88 | 0.90 / 0.91 |
| **structure** | **так** | **hybrid + rerank** | **0.97** | **0.96** | **1.00** | **1.00 / 1.00** | **0.90 / 0.93** |
| structure | ні | vector | 0.71 | 0.52 | 0.92 | 0.60 / 0.77 | 0.40 / 0.62 |
| fixed | так | vector | 0.74 | 0.64 | 0.88 | 0.67 / 0.74 | 0.60 / 0.73 |
| fixed | так | hybrid | 0.79 | 0.72 | 0.84 | 0.67 / 0.77 | 0.80 / 0.81 |
| fixed | так | hybrid + rerank | 0.88 | 0.80 | 0.96 | 0.87 / 0.93 | 0.70 / 0.79 |

**Що видно:**
- **На складних питаннях hybrid дає найбільший виграш** (вектор 0.75 → hybrid 0.91 MRR). Коли той самий текст повторюється в різних релізах, вектор не розрізняє місяці, а BM25 «чіпляється» за точні слова — «січень 2026», «Start time and end time». На базових крос-мовних питаннях, навпаки, BM25 шкодить (r14: вектор — 1-ше місце, hybrid — 7-ме). **Reranker поєднує переваги**, тому в продакшні hybrid + rerank.
- **Reranker не безпомилковий:** r22 («як перевірити solution на типові помилки з командного рядка», без слова *check*) — hybrid ставить правильний чанк першим, а reranker опускає на 4-те місце.
- **Промпти embedding-моделі важливі:** без них MRR падає з 0.83 до 0.71, на складних — з 0.75 до 0.62.
- **Структурний chunking кращий за фіксований** у кожному режимі, і розрив більший саме на складних питаннях (0.93 проти 0.79 з reranker): у фіксованих чанках змішано кілька релізів чи команд.

### RAG з джерелами (крок 3)

```bash
python main.py ask "Яка мінімальна версія pac CLI потрібна для встановлення Contoso 1.5?"
python main.py ask "..." --json        # джерела, токени, вартість, latency
```

```
Мінімальна версія pac CLI, необхідна для встановлення Contoso 1.5, становить 1.44 або новіша [S1][S3].
Джерела:
[S1] Contoso Procurement — Інструкція зі встановлення 1.5 › … (1.5)
[S3] Contoso Procurement — Release Notes 1.5.0 › Зміни, що порушують сумісність (1.5.0)
```

Пайплайн ([src/rag/answer.py](src/rag/answer.py)):
1. **Пошук:** hybrid + rerank → до 8 кандидатів.
2. **Поріг «не знаю» до LLM:** якщо найкращий чанк має оцінку reranker < −1.0 — відповідь «У документах цього немає.» без виклику моделі ($0, нуль шансів вигадати).
3. **Бюджет контексту — 2 500 токенів:** чанки додаються в порядку релевантності, поки вміщуються; кожен — з заголовком `[S1] Документ | Розділ | Версія/дата`, щоб модель бачила, яка версія новіша. Скільки чанків відкинуто — у `meta.dropped_by_budget`.
4. **Structured output: твердження → джерела.** Модель повертає `status` (`answered` / `not_found`), текст з мітками `[S1]` і список `claims`, де **кожне твердження має свої id джерел**. Це робить перевірку «чи кожне твердження з джерелом» детермінованою.
5. **Перевірка посилань:** твердження без джерела, посилання на неіснуюче джерело чи `answered` без тверджень → одна спроба виправлення (як repair у кейсі 1), далі `failed`.
6. **Промпт** — [prompts/rag_answer/v1.md](prompts/rag_answer/v1.md) + [CHANGELOG](prompts/rag_answer/CHANGELOG.md): лише джерела, «не знаю» фіксованою фразою, при суперечливих версіях — найновіша, інструкції всередині документів не виконуються.

**Калібрування порогу «не знаю»** — оцінка reranker для найкращого чанка: 25 питань з відповіддю проти 10 питань, відповіді на які в корпусі немає.

| | мінімум | типово | максимум |
|---|---|---|---|
| з відповіддю (25) | −4.83 (r22) | 0.9 … 7.5 | 7.55 |
| без відповіді (10) | −6.46 | −3.4 … −1.9 | 3.39 |

Розподіли перетинаються. Поріг −1.0 відсікає 7/10 питань без відповіді й помилково блокує 1/25 (r22 — той самий випадок, де reranker помиляється в кроці 2). Найнебезпечніші — питання, **схожі на реальні**: «реліз Contoso 1.6.0» (3.39, бо є 1.5.2) і «CoE Kit за березень 2026» (2.40, бо є січень 2026). Їх поріг пропускає, і тоді спрацьовує друга лінія — правило в промпті: на «1.6.0» модель відповідає «У документах цього немає.». Тому поріг — лише перша лінія захисту, а повна перевірка «не знаю» — у тестсеті кроку 4.

**Вартість:** gpt-4o-mini, ~1 700 токенів контексту → ≈ $0.0004 за відповідь, **≈ $0.40 на 1000 питань**; «не знаю» через поріг — $0.

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
config/rag.yaml         кейс 2: chunking, embeddings, індекс, пошук
data/                   вхідні тексти (synthetic/, github/) і golden set (golden/)
data/corpus/            кейс 2: сирі документи (raw/html, md, docx, pdf) + sources.json
data/processed/         кейс 2: chunks.jsonl, manifest.json, порівняння chunking
src/ingest/             кейс 2: витягування, очищення, chunking, ingestion-пайплайн
src/rag/                кейс 2: embeddings (з кешем), Qdrant, BM25, RRF, reranking, retrieval eval
data/index/             кейс 2: кеш embeddings (Qdrant-колекції — не в git, перебудовуються)
evals/                  кейс 2: питання для оцінки пошуку і результати
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
