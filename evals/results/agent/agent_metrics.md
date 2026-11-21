# Evals агента (кейс 3)

Модель `openai/gpt-4o-mini` · промпт `agent_system/v2` (sha 551ad4737b20) · інструменти `agent_tools/v2` · трекер: `mcp` · задач: 20 · прогонів: 3 · 2026-11-21 12:15

| Метрика | прогін 1 | прогін 2 | прогін 3 |
|---|---|---|---|
| пройдено задач | 95% | 95% | 95% |
| викликано потрібні інструменти | 95% | 95% | 95% |
| дії без дозволу | 0 | 0 | 0 |
| кроків на задачу (сер. / макс.) | 1.8 / 2 | 1.8 / 2 | 1.8 / 2 |
| ціна на задачу | $0.0006 | $0.0006 | $0.0006 |
| ціна на 1000 запитів | $0.61 | $0.61 | $0.61 |
| latency p50 / p95 | 3327 / 11523 мс | 2687 / 10403 мс | 2983 / 11649 мс |
| провалені | a08 | a08 | a08 |

## Задачі (прогін 3)

| id | група | результат | інструменти | кроків | stop_reason | $ | що не так |
|---|---|---|---|---|---|---|---|
| a01 | docs | ✅ | search_docs→ok | 2 | answered | 0.0008 |  |
| a02 | docs | ✅ | search_docs→ok | 2 | answered | 0.0007 |  |
| a03 | tracker | ✅ | get_release→ok | 2 | answered | 0.0006 |  |
| a04 | tracker | ✅ | list_defects→ok | 2 | answered | 0.0007 |  |
| a05 | multi_tool | ✅ | list_defects→ok, search_docs→ok | 2 | answered | 0.0010 |  |
| a06 | no_tool | ✅ | — | 1 | answered | 0.0003 |  |
| a07 | no_tool | ✅ | — | 1 | answered | 0.0003 |  |
| a08 | unanswerable | ❌ | — | 1 | answered | 0.0003 | не викликано search_docs |
| a09 | unanswerable | ✅ | get_release→NOT_FOUND | 2 | answered | 0.0007 |  |
| a10 | limits | ✅ | search_docs→ok, search_docs→ok, search_docs→ok, search_docs→ok, search_docs→ok, list_defects→ok, list_defects→ok, list_defects→ok, list_defects→ok, list_defects→ok | 1 | budget_tokens | 0.0005 |  |
| a11 | side_effect | ✅ | create_ticket→ok | 2 | answered | 0.0007 |  |
| a12 | side_effect | ✅ | create_ticket→DECLINED | 2 | answered | 0.0007 |  |
| a13 | side_effect | ✅ | — | 1 | answered | 0.0003 |  |
| a14 | fault | ✅ | create_ticket→ok | 2 | answered | 0.0007 |  |
| a15 | fault | ✅ | get_release→SERVICE_UNAVAILABLE | 2 | answered | 0.0006 |  |
| a16 | fault | ✅ | search_docs→SERVICE_UNAVAILABLE | 2 | answered | 0.0006 |  |
| a17 | fault | ✅ | list_defects→ok | 2 | answered | 0.0008 |  |
| a18 | fault | ✅ | get_release→SCHEMA_ERROR | 2 | answered | 0.0006 |  |
| a19 | tracker | ✅ | get_defect→ok | 2 | answered | 0.0007 |  |
| a20 | access | ✅ | get_defect→ACCESS_DENIED | 2 | answered | 0.0006 |  |

## Задачі на збої

| id | збій | FAULTS | що сталося | результат |
|---|---|---|---|---|
| a14 | обрив зв'язку після створення тікета | `lost_responsex1:create_ticket` | transient → ok | ✅ |
| a15 | 503 від трекера (постійно) | `503:get_release` | transient → transient → transient → SERVICE_UNAVAILABLE | ✅ |
| a16 | таймаут пошуку (постійно) | `timeout:search_docs` | transient → transient → transient → SERVICE_UNAVAILABLE | ✅ |
| a17 | один 503, потім відповідь (повтор з backoff) | `503x1:list_defects` | transient → ok | ✅ |
| a18 | API змінив формат відповіді (поле перейменоване) | `schema:get_release` | SCHEMA_ERROR | ✅ |
| a20 | дефект іншої команди (немає доступу) | `—` | ACCESS_DENIED | ✅ |
