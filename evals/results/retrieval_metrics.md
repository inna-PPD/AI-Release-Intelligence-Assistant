# Якість пошуку (retrieval)

15 питань з відомим правильним чанком — `evals/retrieval_questions.jsonl`. Hit = у top-k є чанк потрібного документа, що містить ключову фразу.

| Chunking | Промпти embeddings | Пошук | recall@1 | recall@3 | recall@5 | recall@10 | MRR@10 |
|---|---|---|---|---|---|---|---|
| structure | так | vector | 0.80 | 1.00 | 1.00 | 1.00 | 0.89 |
| structure | так | bm25 | 0.73 | 0.87 | 0.93 | 0.93 | 0.81 |
| structure | так | hybrid | 0.80 | 0.93 | 0.93 | 1.00 | 0.88 |
| structure | так | hybrid_rerank | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| structure | ні | vector | 0.60 | 0.93 | 0.93 | 1.00 | 0.77 |
| fixed | так | vector | 0.67 | 0.80 | 0.87 | 0.87 | 0.74 |
| fixed | так | hybrid | 0.67 | 0.87 | 0.87 | 1.00 | 0.77 |
| fixed | так | hybrid_rerank | 0.87 | 1.00 | 1.00 | 1.00 | 0.93 |

## Ранг першого правильного чанка по питаннях (— = не знайдено в top-10)

| Питання | Тип | struct·vector | struct·bm25 | struct·hybrid | struct·hybrid_rerank | struct·vector·plain | fixed·vector | fixed·hybrid | fixed·hybrid_rerank |
|---|---|---|---|---|---|---|---|---|---|
| r01 Яка мінімальна версія pac CLI потрібна для встановлення Cont | version_trap | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1 |
| r02 Який пакет треба імпортувати першим при встановленні версії  | same_language | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 |
| r03 Що виправили в hotfix 1.5.1 для синхронізації з LEO при поми | similar_docs | 2 | 1 | 2 | 1 | 2 | 1 | 1 | 1 |
| r04 За який час треба відреагувати на інцидент Critical? | table | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r05 Який тест-кейс перевіряє лист погоджувачу в Approval Flow v2 | table | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r06 How do I package solution components from a local folder int | same_language | 1 | 1 | 1 | 1 | 1 | — | 3 | 1 |
| r07 Чи можна імпортувати managed solution у середовище, де є йог | cross_lingual | 1 | 4 | 1 | 1 | 2 | 1 | 1 | 1 |
| r08 Which CoE Starter Kit release fixed issue #9508 about the En | exact_id | 3 | 1 | 1 | 1 | 10 | — | 8 | 2 |
| r09 Які environment variables треба заповнити під час встановлен | same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r10 У якому статусі тепер створюється клон погодженої заявки? | similar_docs | 2 | 1 | 2 | 1 | 2 | 3 | 2 | 1 |
| r11 Which connectors must the data policy allow for the CoE Star | same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r12 Яка команда pac відправляє PCF-компонент у середовище Datave | cross_lingual | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r13 Який ліміт запитів до API LEO PPM на годину? | same_language | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| r14 Як часто виходять нові версії CoE Starter Kit? | cross_lingual | 1 | — | 7 | 1 | 1 | 4 | 10 | 1 |
| r15 Які середовища, крім production, Microsoft радить мати для A | cross_lingual | 1 | 3 | 1 | 1 | 2 | 2 | 2 | 2 |
