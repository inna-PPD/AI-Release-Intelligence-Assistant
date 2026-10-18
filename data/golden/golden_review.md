# Golden set — перевірка розмітки

Перевірено: **10 з 10**. Правила — [ANNOTATION_GUIDE.md](ANNOTATION_GUIDE.md).
Виправлення вносяться в `golden_set.json` (поле `expected`), після перевірки — `"reviewed": true`.

---

## syn-001 — ✅ перевірено

**Оригінальний текст:**

~~~~text
Title: Не зберігається заявка на закупівлю
Env: UAT
Release 1.4.2
Steps:
1. відкрити canvas app «Заявки на закупівлю»
2. заповнити всі поля, додати вкладення >5MB
3. Save
Expected: заявка створюється в cnt_request
Actual: спінер крутиться ~30 сек потім 'Something went wrong'
Severity: High
~~~~

| Поле | Еталон |
|---|---|
| `title` | Не зберігається заявка на закупівлю |
| `is_defect` | `true` |
| `components` | `canvas_app` · Заявки на закупівлю<br>`table` · cnt_request |
| `environments` | `uat` |
| `severity` | high |
| `release_version` | 1.4.2 |
| `steps_to_reproduce` | 1. відкрити canvas app «Заявки на закупівлю»<br>2. заповнити всі поля, додати вкладення >5MB<br>3. Save |
| `expected_result` | заявка створюється в cnt_request |
| `actual_result` | спінер крутиться ~30 сек потім 'Something went wrong' |
| `is_regression` | `null` |

---

## syn-005 — ✅ перевірено

**Оригінальний текст:**

~~~~text
при імпорті солюшена на тест вилітає помилка міссінг депенденсі на таблицю cnt_invoice. на деві все ок. реліз 1.5.0 блокує деплой!!! терміново
~~~~

| Поле | Еталон |
|---|---|
| `title` | Помилка missing dependency на cnt_invoice при імпорті солюшена на тест |
| `is_defect` | `true` |
| `components` | `solution` · `null`<br>`table` · cnt_invoice |
| `environments` | `test` |
| `severity` | critical |
| `release_version` | 1.5.0 |
| `steps_to_reproduce` | `[]` |
| `expected_result` | `null` |
| `actual_result` | при імпорті солюшена вилітає помилка міссінг депенденсі на таблицю cnt_invoice |
| `is_regression` | `null` |

> **Примітка:** «блокує деплой» + «терміново» → critical; dev працює — не додаємо

---

## syn-009 — ✅ перевірено

**Оригінальний текст:**

~~~~text
Sync LEO PPM -> Dataverse: задачі з ЛЕО не підтягуються в таблицю cnt_projecttask з 12.10. В run history флоу 'LEO Task Sync' помилка 429 Too Many Requests, після 3 retry фейлиться. Prod. Критично — PMи не бачать актуальний план, статус-репорт в пʼятницю.
~~~~

| Поле | Еталон |
|---|---|
| `title` | Задачі з LEO PPM не синхронізуються в Dataverse (429 Too Many Requests) |
| `is_defect` | `true` |
| `components` | `leo_ppm` · LEO PPM<br>`cloud_flow` · LEO Task Sync<br>`table` · cnt_projecttask |
| `environments` | `prod` |
| `severity` | critical |
| `release_version` | `null` |
| `steps_to_reproduce` | `[]` |
| `expected_result` | `null` |
| `actual_result` | задачі з ЛЕО не підтягуються в таблицю cnt_projecttask; в run history флоу помилка 429 Too Many Requests, після 3 retry фейлиться |
| `is_regression` | `true` |

> **Примітка:** «з 12.10 не підтягуються» → раніше працювало

---

## syn-010 — ✅ перевірено

**Оригінальний текст:**

~~~~text
[BUG] Duplicate records in cnt_invoice after Approval Flow v2 rerun
Release: 1.5.1 (hotfix)
Коли флоу перезапускається вручну з run history, він створює дубль інвойсу замість оновлення існуючого. Expected: upsert by cnt_invoicenumber. Actual: новий запис з тим самим номером. Також зачіпає cnt_request (статус двічі міняється). Env – test & uat. Це регресія, в 1.5.0 було ок.
~~~~

| Поле | Еталон |
|---|---|
| `title` | Duplicate records in cnt_invoice after Approval Flow v2 rerun |
| `is_defect` | `true` |
| `components` | `cloud_flow` · Approval Flow v2<br>`table` · cnt_invoice<br>`table` · cnt_request |
| `environments` | `test`, `uat` |
| `severity` | `null` |
| `release_version` | 1.5.1 |
| `steps_to_reproduce` | `[]` |
| `expected_result` | upsert by cnt_invoicenumber |
| `actual_result` | новий запис з тим самим номером |
| `is_regression` | `true` |

> **Примітка:** перезапуск з run history — умова, а не послідовність кроків

---

## syn-017 — ✅ перевірено

**Оригінальний текст:**

~~~~text
Привіт! Значить ситуація така: беру заявку яка вже погоджена, хочу її скопіювати (кнопка Clone), міняю постачальника і суму, зберігаю — а в копії лишається статус Approved і вона одразу йде в оплату, минаючи погодження!!! Це ж дірка в процесі. Перевіряла на уат, версія вроді 1.5.1 але не впевнена. На проді не пробувала і боюсь пробувати)) Очікую що копія створюється в статусі Draft.
~~~~

| Поле | Еталон |
|---|---|
| `title` | Клон погодженої заявки зберігає статус Approved і йде в оплату без погодження |
| `is_defect` | `true` |
| `components` | `[]` |
| `environments` | `uat` |
| `severity` | `null` |
| `release_version` | 1.5.1 |
| `steps_to_reproduce` | 1. беру заявку яка вже погоджена<br>2. скопіювати (кнопка Clone)<br>3. міняю постачальника і суму<br>4. зберігаю |
| `expected_result` | копія створюється в статусі Draft |
| `actual_result` | в копії лишається статус Approved і вона одразу йде в оплату, минаючи погодження |
| `is_regression` | `null` |

> **Примітка:** застосунок/таблиця не названі → components []; «!!!» без оцінки впливу → severity null

---

## syn-018 — ✅ перевірено

**Оригінальний текст:**

~~~~text
Known issue (1.5.2): Business rule 'Set default currency' on cnt_request doesn't fire when the form is opened via quick create. Users must select currency manually. Fix planned for 1.5.3. Low impact.
~~~~

| Поле | Еталон |
|---|---|
| `title` | Business rule 'Set default currency' doesn't fire on quick create |
| `is_defect` | `true` |
| `components` | `business_rule` · Set default currency<br>`table` · cnt_request |
| `environments` | `[]` |
| `severity` | low |
| `release_version` | 1.5.2 |
| `steps_to_reproduce` | `[]` |
| `expected_result` | `null` |
| `actual_result` | Business rule 'Set default currency' on cnt_request doesn't fire when the form is opened via quick create; users must select currency manually |
| `is_regression` | `null` |

> **Примітка:** known issue з release notes — це дефект; 1.5.3 — версія виправлення, не прояву

---

## syn-020 — ✅ перевірено

**Оригінальний текст:**

~~~~text
Не баг, але: було б добре щоб в Approval Flow приходило нагадування якщо заявка не погоджена 3 дні. Зараз висить тиждень і ніхто не знає. prod
~~~~

| Поле | Еталон |
|---|---|
| `title` | Нагадування в Approval Flow для непогоджених заявок |
| `is_defect` | `false` |
| `components` | `cloud_flow` · Approval Flow |
| `environments` | `prod` |
| `severity` | `null` |
| `release_version` | `null` |
| `steps_to_reproduce` | `[]` |
| `expected_result` | в Approval Flow приходить нагадування якщо заявка не погоджена 3 дні |
| `actual_result` | заявка висить тиждень і ніхто не знає |
| `is_regression` | `null` |

> **Примітка:** побажання, не дефект

---

## gh-005 — ✅ перевірено

**Оригінальний текст:**

~~~~text
8 Flows have failed with the same error message - "The user is not a member of the organization."

### Does this bug already exist in our backlog?

### Describe the issue

Current installed CoE starter Kit version: 4.5.0
Issue: The user is not a member of the organization.

We have identified that eight (8) Power Automate flows are consistently failing with the following error message:

"The user is not a member of the organization."

The affected flows and corresponding failing actions are listed below:
Admin | Sync Template v4

Desktop Flows – Action List_Envt_Desktop_Flows
Error: The user is not a member of the organization.
Model-Driven Apps – Action List_Envt_MDApps
Error: The user is not a member of the organization.
Canvas Apps – Action List_Envt_Apps
Error: The user is not a member of the organization.
Power Virtual Agents (PVA) – Action List_Envt_PVAs
Error: The user is not a member of the organization.
Business Process Flows – Action List_Envt_BPFs
Error: The user is not a member of the organization.

Cleanup Helper – Check Deleted v4

Solutions – Action List_Envt_Solutions
Error: The user is not a member of the organization.
Business Process Flows – Action List_Envt_BPFs
Error: The user is not a member of the organization.
Model-Driven Apps – Action List_Envt_MDAs
Error: The user is not a member of the organization.
Power Virtual Agents (PVA) – Action List_Envt_PVAs
Error: The user is not a member of the organization.

These failures are recurring and impacting the regular operation of our governance and cleanup automation processes.

We kindly request assistance in identifying the root cause of the membership-related error and providing guidance on resolving these failures. The flows are currently unable to run as expected.

[image]

### Expected Behavior

_No response_

### What solution are you experiencing the issue with?

Core

### What solution version are you using?

4.50.0

### What app or flow are you having the issue with?

Cleanup Helper – Check Deleted v4  ||  Admin | Sync Template v4

### What method are you using to get inventory and telemetry?

None

### Steps To Reproduce

_No response_

### Anything else?

_No response_
~~~~

| Поле | Еталон |
|---|---|
| `title` | 8 Flows have failed with the same error message - "The user is not a member of the organization." |
| `is_defect` | `true` |
| `components` | `cloud_flow` · Admin | Sync Template v4<br>`cloud_flow` · Cleanup Helper – Check Deleted v4 |
| `environments` | `[]` |
| `severity` | `null` |
| `release_version` | 4.50.0 |
| `steps_to_reproduce` | `[]` |
| `expected_result` | `null` |
| `actual_result` | flows are consistently failing with the error message "The user is not a member of the organization." |
| `is_regression` | `null` |

> **Примітка:** у тексті і 4.5.0, і 4.50.0 — беремо зі структурованого поля «What solution version are you using?»

---

## gh-012 — ✅ перевірено

**Оригінальний текст:**

~~~~text
pac catalog submit fails in v1.46.1 with Typeload exception "could not load file or assembly 'Microsoft.PowerPlatform.Dataverse.Client,"

Seems that the pac catalog submit command is broken in the latest pac cli version

I get a nasty type load exception. Tried it on an OOTB ADO build agent and on my local machine. Using the same command in v1.44.2 works like a charm. 

[image]
~~~~

| Поле | Еталон |
|---|---|
| `title` | pac catalog submit fails in v1.46.1 with TypeLoad exception |
| `is_defect` | `true` |
| `components` | `alm_tooling` · pac catalog submit |
| `environments` | `[]` |
| `severity` | `null` |
| `release_version` | 1.46.1 |
| `steps_to_reproduce` | `[]` |
| `expected_result` | `null` |
| `actual_result` | type load exception "could not load file or assembly 'Microsoft.PowerPlatform.Dataverse.Client" |
| `is_regression` | `true` |

> **Примітка:** «the same command in v1.44.2 works» → регресія; версія прояву 1.46.1

---

## gh-019 — ✅ перевірено

**Оригінальний текст:**

~~~~text
`pac solution pack` against YAML solution source incorrectly places Quick Create forms under `<forms type="quick" />`

**Describe the bug**
When running `pac solution pack` against a folder containing YAML generated by the Power Platform Git Integration that includes a table with a 'Quick Create' form, the resulting solution.zip file duplicates the Quick Create form definition under `<forms type='quick'>` as well as `<forms type='quickCreate'>`. 

This causes solution imports to fail when the quick create form contains an `<events />` definition.

**To Reproduce**
Steps to reproduce the behavior:
1. Create a solution, add a table and create a new Quick Create form 
2. Add an 'onLoad' event handler to the new Quick Create form
3. Use the Power Platform source control integration to commit the solution to git
4. Clone/download to git repository
5. Navigate to the solution root folder and run `pac solution pack --folder ./ --zipfile QuickCreateForm.zip --packageType managed` to generate an example.zip solution file
6. Attempt to import the example.zip managed solution file into another environment. An error will be shown stating _'Solution "QuickCreateForm" failed to import: Form XML of type quick with id <GUID> cannot contain element: events.'_
7. Manually unzip the QuickCreateForm.zip solution file and view the customizations.xml file. Observe that the `<forms type='quick'>` section contains a definition for the Quick Create form that includes `<events>`

**Expected behavior**
When packing YAML solution source, Quick Create form definitions should go under `<forms type='quickCreate'>` only.

**Screenshots**

customizations.xml showing the Quick Create form duplicated in `<forms type='quick' />` and `<forms type='quickCreate' />`

[image]

Error shown when importing solution:

[image]

**Desktop**
 - OS: Windows 11
- pac cli version 2.6.4

[image]
~~~~

| Поле | Еталон |
|---|---|
| `title` | pac solution pack places Quick Create forms under <forms type="quick" /> |
| `is_defect` | `true` |
| `components` | `alm_tooling` · pac solution pack |
| `environments` | `[]` |
| `severity` | `null` |
| `release_version` | 2.6.4 |
| `steps_to_reproduce` | 1. Create a solution, add a table and create a new Quick Create form<br>2. Add an 'onLoad' event handler to the new Quick Create form<br>3. Use the Power Platform source control integration to commit the solution to git<br>4. Clone/download to git repository<br>5. Navigate to the solution root folder and run `pac solution pack --folder ./ --zipfile QuickCreateForm.zip --packageType managed`<br>6. Attempt to import the example.zip managed solution file into another environment<br>7. Manually unzip the QuickCreateForm.zip solution file and view the customizations.xml file |
| `expected_result` | When packing YAML solution source, Quick Create form definitions should go under <forms type='quickCreate'> only |
| `actual_result` | the resulting solution.zip duplicates the Quick Create form definition under <forms type='quick'> as well as <forms type='quickCreate'>; solution imports fail when the quick create form contains an <events /> definition |
| `is_regression` | `null` |

> **Примітка:** версія pac cli з розділу Desktop
