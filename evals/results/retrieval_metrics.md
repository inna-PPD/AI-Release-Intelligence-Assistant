# Якість пошуку (retrieval)

25 питань з відомим правильним чанком — `evals/retrieval_questions.jsonl`. Hit = у top-k є чанк потрібного документа, що містить ключову фразу.

| Chunking | Промпти embeddings | Пошук | recall@1 | recall@3 | recall@5 | recall@10 | MRR@10 |
|---|---|---|---|---|---|---|---|
| structure | так | vector | 0.72 | 1.00 | 1.00 | 1.00 | 0.83 |
| structure | так | bm25 | 0.64 | 0.76 | 0.84 | 0.84 | 0.71 |
| structure | так | hybrid | 0.84 | 0.92 | 0.92 | 1.00 | 0.89 |
| structure | так | hybrid_rerank | 0.96 | 0.96 | 1.00 | 1.00 | 0.97 |
| structure | ні | vector | 0.52 | 0.88 | 0.92 | 1.00 | 0.71 |
| fixed | так | vector | 0.64 | 0.84 | 0.88 | 0.88 | 0.74 |
| fixed | так | hybrid | 0.72 | 0.84 | 0.84 | 0.96 | 0.79 |
| fixed | так | hybrid_rerank | 0.80 | 0.96 | 0.96 | 1.00 | 0.88 |

## Базові vs складні питання

Складні: схожі розділи в різних релізах, той самий параметр у різних командах, перефразування без ключових слів, кілька правильних чанків.

| Chunking | Промпти | Пошук | base (15): recall@1 / recall@5 / MRR | hard (10): recall@1 / recall@5 / MRR |
|---|---|---|---|---|
| structure | так | vector | 0.80 / 1.00 / 0.89 | 0.60 / 1.00 / 0.75 |
| structure | так | bm25 | 0.73 / 0.93 / 0.81 | 0.50 / 0.70 / 0.56 |
| structure | так | hybrid | 0.80 / 0.93 / 0.88 | 0.90 / 0.90 / 0.91 |
| structure | так | hybrid_rerank | 1.00 / 1.00 / 1.00 | 0.90 / 1.00 / 0.93 |
| structure | ні | vector | 0.60 / 0.93 / 0.77 | 0.40 / 0.90 / 0.62 |
| fixed | так | vector | 0.67 / 0.87 / 0.74 | 0.60 / 0.90 / 0.73 |
| fixed | так | hybrid | 0.67 / 0.87 / 0.77 | 0.80 / 0.80 / 0.81 |
| fixed | так | hybrid_rerank | 0.87 / 1.00 / 0.93 | 0.70 / 0.90 / 0.79 |

## Ранг першого правильного чанка по питаннях (— = не знайдено в top-10)

| Питання | Тип | struct·vector | struct·bm25 | struct·hybrid | struct·hybrid_rerank | struct·vector·plain | fixed·vector | fixed·hybrid | fixed·hybrid_rerank |
|---|---|---|---|---|---|---|---|---|---|
| r01 Яка мінімальна версія pac CLI потрібна для встановлення Cont | base · version_trap | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| r02 Який пакет треба імпортувати першим при встановленні версії  | base · same_language | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| r03 Що виправили в hotfix 1.5.1 для синхронізації з LEO при поми | base · similar_docs | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 |
| r04 За який час треба відреагувати на інцидент Critical? | base · table | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r05 Який тест-кейс перевіряє лист погоджувачу в Approval Flow v2 | base · table | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r06 How do I package solution components from a local folder int | base · same_language | 1 | 1 | 1 | 1 | 1 | — | 3 | 1 |
| r07 Чи можна імпортувати managed solution у середовище, де є йог | base · cross_lingual | 1 | 4 | 1 | 1 | 2 | 1 | 1 | 1 |
| r08 Which CoE Starter Kit release fixed issue #9508 about the En | base · exact_id | 3 | 1 | 1 | 1 | 10 | — | 8 | 2 |
| r09 Які environment variables треба заповнити під час встановлен | base · same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r10 У якому статусі тепер створюється клон погодженої заявки? | base · similar_docs | 2 | 1 | 2 | 1 | 2 | 3 | 2 | 1 |
| r11 Which connectors must the data policy allow for the CoE Star | base · same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r12 Яка команда pac відправляє PCF-компонент у середовище Datave | base · cross_lingual | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r13 Який ліміт запитів до API LEO PPM на годину? | base · same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r14 Як часто виходять нові версії CoE Starter Kit? | base · cross_lingual | 1 | — | 7 | 1 | 1 | 4 | 10 | 1 |
| r15 Які середовища, крім production, Microsoft радить мати для A | base · cross_lingual | 1 | 3 | 1 | 1 | 2 | 2 | 2 | 2 |
| r16 Скільки багів виправили в релізі CoE Starter Kit за січень 2 | hard · similar_docs | 3 | — | 7 | 1 | 4 | — | — | 3 |
| r17 In which CoE Starter Kit release was the Sync Audit Logs (V2 | hard · similar_docs | 3 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| r18 Що робить параметр --packagetype саме в команді pac solution | hard · similar_docs | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| r19 Які дані зникнуть, якщо видалити managed solution із середов | hard · paraphrase | 1 | 4 | 1 | 1 | 2 | 1 | 1 | 1 |
| r20 Який тест перевіряє, що картка проєкту в Project Hub не відк | hard · paraphrase | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r21 У якій версії Contoso з'явилась роль лише для перегляду заяв | hard · paraphrase | 1 | 3 | 1 | 1 | 1 | 1 | 1 | 1 |
| r22 Як перевірити solution на типові помилки з командного рядка  | hard · paraphrase | 3 | — | 1 | 4 | 3 | 2 | 1 | 9 |
| r23 Що треба зробити перед встановленням оновлення CoE Starter K | hard · similar_docs | 2 | — | 1 | 1 | 7 | 3 | 7 | 2 |
| r24 Що потрібно зробити з connection reference cnt_sharedoffice3 | hard · version_trap | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r25 У якому релізі CoE виправили проблему, коли flow Inactivity  | hard · multi_relevant | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
