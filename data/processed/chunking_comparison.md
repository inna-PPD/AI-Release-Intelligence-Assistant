# Порівняння chunking-стратегій

structure: max 300 / min 60 токенів · fixed: 300 токенів, overlap 50 · токенізатор o200k_base

## Увесь корпус (після дедуплікації)

| Стратегія | Чанків | Токенів avg / min / max | Чанки з розрізаним блоком | Чанки з кількох розділів |
|---|---|---|---|---|
| structure | 404 | 141 / 9 / 316 | 9% | 0% |
| fixed | 252 | 280 / 51 / 301 | 97% | 52% |

«Розрізаний блок» — чанк починається або закінчується посеред абзацу, пункту списку чи рядка таблиці.
«Кілька розділів» — у чанку змішано зміст різних тем рівня h2 (напр. дві різні команди pac CLI). Structure об'єднує лише дрібні підрозділи однієї теми (параметри однієї команди).

## learn-cli-solution (html)

| | structure | fixed |
|---|---|---|
| чанків | 69 | 27 |
| токенів avg / max | 84 / 299 | 291 / 300 |
| розрізаний блок | 0% | 100% |
| кілька розділів | 0% | 70% |

Початок другого чанка:

- structure (`pac solution > Commands`): «## Commands
Command | Description
pac solution add-license | Add license and plan info to the solution.
pac solution add-reference | Adds a reference from the p…»
- fixed (`pac solution > Commands`): «project to the current state of the solution in your organization.
pac solution unpack | Extract solution components from solution.zip onto local filesystem (So…»

## coe-release-february2026 (md)

| | structure | fixed |
|---|---|---|
| чанків | 9 | 5 |
| токенів avg / max | 142 / 295 | 296 / 300 |
| розрізаний блок | 0% | 100% |
| кілька розділів | 0% | 60% |

Початок другого чанка:

- structure (`Upgrade Instructions`): «## Upgrade Instructions
- Upgrading from the latest version of the CoE Starter Kit: https://docs.microsoft.com/power-platform/guidance/coe/after-setup
- Trouble…»
- fixed (`Change Log > 🐛 CoE Starter Kit - BUGS (25)`): «CoE Starter Kit - BUG] Admin | Inactivity notifications - Email template by giving a hyperlink
- #9882-[CoE Starter Kit - BUG] Users who belong to a Microsoft 3…»

## contoso-regression-test-plan-1.5 (docx)

| | structure | fixed |
|---|---|---|
| чанків | 3 | 2 |
| токенів avg / max | 148 / 287 | 248 / 300 |
| розрізаний блок | 0% | 100% |
| кілька розділів | 0% | 100% |

Початок другого чанка:

- structure (`Contoso Procurement — Регресійний тест-план 1.5 > Тест-кейси`): «## Тест-кейси
ID | Компонент | Сценарій | Пріоритет
TC-101 | canvas app «Заявки на закупівлю» | Створення заявки з вкладенням 8 MB | High
TC-104 | cnt_request |…»
- fixed (`Contoso Procurement — Регресійний тест-план 1.5 > Тест-кейси`): «понад 100 000 грн | Medium
TC-120 | cnt_ApprovalValidation | Відхилення без коментаря показує повідомлення, а не помилку | High
TC-125 | LEO Task Sync | Синхрон…»

## contoso-install-guide-1.5 (pdf)

| | structure | fixed |
|---|---|---|
| чанків | 3 | 2 |
| токенів avg / max | 115 / 156 | 198 / 300 |
| розрізаний блок | 0% | 100% |
| кілька розділів | 0% | 100% |

Початок другого чанка:

- structure (`Contoso Procurement — Інструкція зі встановлення 1.5 > Порядок встановлення`): «## Порядок встановлення
- Імпортувати ContosoCore_Invoices_managed.zip (обов'язково першим, інакше — помилка missing dependency на cnt_invoice).
- Імпортувати C…»
- fixed (`Contoso Procurement — Інструкція зі встановлення 1.5 > Порядок встановлення`): «овнити environment variables cnt_LeoApiKey і cnt_LeoBaseUrl.
- Увімкнути flows «Approval Flow v2» і «LEO Task Sync».
## Перевірка після встановлення
Створити те…»

