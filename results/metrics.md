## Зведена таблиця

| Модель | Промпт | Семплінг | Валідних | Failed | p50, мс | p95, мс | $ / 1000 док. | Field accuracy |
|---|---|---|---|---|---|---|---|---|
| qwen2.5:7b-instruct | extract_defect/v1 | A | 100% | 0 | 8046 | 15888 | 0.0000 | 0.59 |
| qwen2.5:7b-instruct | extract_defect/v1 | B | 100% | 0 | 7898 | 14794 | 0.0000 | 0.57 |
| openai/gpt-4o-mini | extract_defect/v1 | A | 100% | 0 | 2413 | 4221 | 0.5195 | 0.73 |
| openai/gpt-4o-mini | extract_defect/v1 | B | 100% | 0 | 2678 | 4821 | 0.5249 | 0.70 |

## Точність по полях (golden set)

| Поле | qwen2.5:7b-instruct · v1 · A | qwen2.5:7b-instruct · v1 · B | openai/gpt-4o-mini · v1 · A | openai/gpt-4o-mini · v1 · B |
|---|---|---|---|---|
| is_defect | 1.00 | 1.00 | 1.00 | 1.00 |
| components.type | 0.10 | 0.10 | 0.30 | 0.30 |
| components.name | 0.52 | 0.30 | 0.62 | 0.62 |
| environments | 0.40 | 0.50 | 0.90 | 0.80 |
| severity | 0.80 | 0.80 | 0.70 | 0.70 |
| release_version | 0.70 | 0.90 | 0.90 | 0.80 |
| steps_to_reproduce | 0.50 | 0.49 | 0.65 | 0.54 |
| expected_result | 0.70 | 0.70 | 0.60 | 0.70 |
| actual_result | 0.50 | 0.30 | 0.70 | 0.60 |
| is_regression | 0.70 | 0.60 | 0.90 | 0.90 |
