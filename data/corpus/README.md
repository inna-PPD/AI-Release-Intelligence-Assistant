# RAG-корпус (кейс 2)

42 документи у 4 форматах, лише публічні або синтетичні дані. Метадані кожного документа — [sources.json](sources.json).

| Джерело | Формат | К-сть | Що | Ліцензія |
|---|---|---|---|---|
| [Microsoft Learn](https://learn.microsoft.com/en-us/power-platform/) | HTML | 15 | pac CLI (`solution`, `package`, `pcf`), ALM (solutions, layers, environment strategy, source control, Build Tools, Pipelines), налаштування й оновлення CoE Starter Kit | [CC BY 4.0](https://github.com/MicrosoftDocs/power-platform/blob/main/LICENSE) |
| [GitHub Releases microsoft/coe-starter-kit](https://github.com/microsoft/coe-starter-kit/releases) | Markdown | 18 | release notes CoE Starter Kit, червень 2024 — лютий 2026 | MIT |
| Синтетичні (вигадана компанія Contoso) | DOCX | 6 | release notes 1.4.2–1.5.2, регресійний тест-план 1.5 | цей репозиторій |
| Синтетичні (вигадана компанія Contoso) | PDF | 3 | інструкції зі встановлення 1.4 (застаріла) і 1.5, runbook підтримки | цей репозиторій |

## Як відтворити

```bash
python scripts/download_corpus.py        # HTML + Markdown (сирі файли, з boilerplate)
python scripts/generate_contoso_docs.py  # DOCX + PDF (Windows: PDF друкується через Microsoft Edge)
python main.py ingest                    # → data/processed/
```

Сирі файли збережено в `raw/` без змін, щоб ingestion можна було перезапустити без мережі.

## Навмисні «пастки» для тестсету

- **Застарілі версії:** інструкція 1.4 (pac CLI ≥ 1.32, особисте підключення) і 1.5 (pac CLI ≥ 1.44, сервісний акаунт) суперечать одна одній; release notes CoE Kit за 18 місяців описують ту саму функціональність у різних станах.
- **Схожі документи:** release notes Contoso 1.5.1 (hotfix) і 1.5.2; дефект із 1.5.1 виправлено в 1.5.2.
- Синтетичні документи узгоджені з баг-репортами кейсу 1 (`data/synthetic/defects_synthetic.jsonl`).
