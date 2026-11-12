# evals/ — оцінка RAG (кейс 2)

| Що | Де |
|---|---|
| Тестсет відповідей (23 питання: еталон, ключові факти, очікувані джерела; 6 без відповіді) | [testset.jsonl](testset.jsonl), перегляд — [testset_review.md](testset_review.md) |
| Питання для оцінки пошуку (25: базові + складні, правильний чанк = документ + фраза) | [retrieval_questions.jsonl](retrieval_questions.jsonl), перегляд — [retrieval_review.md](retrieval_review.md) |
| **Scoring-функції** | код у [src/rag/evals.py](../src/rag/evals.py): детерміновані `deterministic_scores` (refusal, source_hit, key_facts, no_forbidden, citations_ok), LLM-суддя `Judge.judge` (правильність) і `Judge.faithful` (faithfulness), `check_thresholds`, `calibrate`; recall@k / MRR — [src/rag/retrieval_eval.py](../src/rag/retrieval_eval.py) |
| Промпти судді | [prompts/rag_judge/v1.md](../prompts/rag_judge/v1.md), [prompts/rag_faithfulness/v1.md](../prompts/rag_faithfulness/v1.md) |
| Ручна розмітка для калібрування судді | [calibration/hand_grades.json](calibration/hand_grades.json) |
| Результати прогону | [results/rag_metrics.md](results/rag_metrics.md), [results/rag_answers.jsonl](results/rag_answers.jsonl), [results/retrieval_metrics.md](results/retrieval_metrics.md), [results/judge_calibration.md](results/judge_calibration.md) |
| Результати промпту v1 (для порівняння) | [results/rag_metrics_v1.md](results/rag_metrics_v1.md) |
| Розкид метрик між прогонами | [results/variance/](results/variance/) |

Запуск: `python main.py case2` — усе разом, або окремо `retrieval-eval`, `rag-eval [--ci]`, `calibrate`.
