# CHANGELOG — rag_judge / rag_faithfulness

## v1 — 2026-11-12
- `rag_judge/v1`: вердикт correct / partial / incorrect відносно еталонної відповіді; лише зміст, не стиль і не мова.
- `rag_faithfulness/v1`: для кожного твердження — чи підтверджують його процитовані джерела.
- Суддя — `anthropic/claude-haiku-5.5`, інша модель, ніж генератор `openai/gpt-4o-mini`. Калібрування на ручній розмітці — `evals/results/judge_calibration.md`.
