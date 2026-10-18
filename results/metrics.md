## Зведена таблиця

| Модель | Промпт | Семплінг | Валідних | Failed | p50, мс | p95, мс | $ / 1000 док. | Field accuracy |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | extract_defect/v1 | A | 100% | 0 | 8046 | 15888 | 0.0000 | 0.59 |
| qwen2.5:7b-instruct | extract_defect/v1 | B | 100% | 0 | 7898 | 14794 | 0.0000 | 0.57 |
| openai/gpt-4o-mini | extract_defect/v1 | A | 100% | 0 | 2413 | 4221 | 0.5195 | 0.73 |
| openai/gpt-4o-mini | extract_defect/v1 | B | 100% | 0 | 2678 | 4821 | 0.5249 | 0.70 |
| openai/gpt-4o-mini | extract_defect/v2 | A | 100% | 0 | 2499 | 3836 | 0.6569 | 0.91 |
| qwen2.5:7b-instruct | extract_defect/v2 | A | 100% | 0 | 8299 | 19431 | 0.0000 | 0.73 |
| openai/gpt-4o-mini | extract_defect/v2 | B | 100% | 0 | 2347 | 3582 | 0.6572 | 0.89 |
| qwen2.5:7b-instruct | extract_defect/v2 | B | 100% | 0 | 8267 | 18070 | 0.0000 | 0.74 |

## Точність по полях (golden set)

| Поле | qwen2.5:7b-instruct · v1 · A | qwen2.5:7b-instruct · v1 · B | openai/gpt-4o-mini · v1 · A | openai/gpt-4o-mini · v1 · B | openai/gpt-4o-mini · v2 · A | qwen2.5:7b-instruct · v2 · A | openai/gpt-4o-mini · v2 · B | qwen2.5:7b-instruct · v2 · B |
|---|---|---|---|---|---|---|---|---|
| is_defect | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.90 |
| components.type | 0.10 | 0.10 | 0.30 | 0.30 | 0.80 | 0.60 | 0.80 | 0.60 |
| components.name | 0.52 | 0.30 | 0.62 | 0.62 | 0.88 | 0.72 | 0.85 | 0.76 |
| environments | 0.40 | 0.50 | 0.90 | 0.80 | 1.00 | 0.60 | 1.00 | 0.80 |
| severity | 0.80 | 0.80 | 0.70 | 0.70 | 1.00 | 0.70 | 1.00 | 0.70 |
| release_version | 0.70 | 0.90 | 0.90 | 0.80 | 0.90 | 0.70 | 0.90 | 0.80 |
| steps_to_reproduce | 0.50 | 0.49 | 0.65 | 0.54 | 0.99 | 0.78 | 0.97 | 0.78 |
| expected_result | 0.70 | 0.70 | 0.60 | 0.70 | 0.90 | 0.80 | 0.90 | 0.90 |
| actual_result | 0.50 | 0.30 | 0.70 | 0.60 | 0.70 | 0.60 | 0.60 | 0.40 |
| is_regression | 0.70 | 0.60 | 0.90 | 0.90 | 0.90 | 0.80 | 0.90 | 0.80 |
