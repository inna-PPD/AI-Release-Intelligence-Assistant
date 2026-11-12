# Питання для оцінки пошуку — перевірка

Перевірено автором: **25 з 25**.
Для кожного питання: чи це реалістичне питання користувача і чи справді показаний чанк на нього відповідає.
Виправлення — у `evals/retrieval_questions.jsonl`, потім `python scripts/retrieval_review.py`.

---

## r01 · базове · є застаріла версія документа · ✅

**Питання:** Яка мінімальна версія pac CLI потрібна для встановлення Contoso Procurement 1.5?

**Очікується:** документ `contoso-install-guide-1.5`, чанк містить «1.44 або новішої» — знайдено чанків: 1

`contoso-install-guide-1.5#000` · Contoso Procurement — Інструкція зі встановлення 1.5 › Contoso Procurement — Інструкція зі встановлення 1.5 (+1)

~~~~text
# Contoso Procurement — Інструкція зі встановлення 1.5
Актуальна інструкція для версій 1.5.0 і новіших. Замінює інструкцію 1.4.
## Передумови
- pac CLI версії 1.44 або новішої (нижчі версії не підтримують пакування ContosoCore_Invoices).
- Роль System Administrator у цільовому середовищі.
- Сервісний акаунт svc-contoso-flows з ліцензією Power Automate Premium — особисті підключення заборонені.
- Доступ до API LEO PPM (ключ зберігається в environment variable cnt_LeoApiKey).
~~~~

> **Примітка:** інструкція 1.4 (застаріла) каже 1.32 — пастка

---

## r02 · базове · мова питання = мова документа · ✅

**Питання:** Який пакет треба імпортувати першим при встановленні версії 1.5?

**Очікується:** документ `contoso-install-guide-1.5`, чанк містить «обов'язково першим» — знайдено чанків: 1

`contoso-install-guide-1.5#001` · Contoso Procurement — Інструкція зі встановлення 1.5 › Contoso Procurement — Інструкція зі встановлення 1.5 > Порядок встановлення

~~~~text
## Порядок встановлення
- Імпортувати ContosoCore_Invoices_managed.zip (обов'язково першим, інакше — помилка missing dependency на cnt_invoice).
- Імпортувати ContosoCore_1_5_x_managed.zip командою pac solution import --activate-plugins.
- Прив'язати connection reference cnt_sharedoffice365 до сервісного акаунта svc-contoso-flows.
- Заповнити environment variables cnt_LeoApiKey і cnt_LeoBaseUrl.
- Увімкнути flows «Approval Flow v2» і «LEO Task Sync».
~~~~

---

## r03 · базове · є схожий документ-пастка · ✅

**Питання:** Що виправили в hotfix 1.5.1 для синхронізації з LEO при помилці 429?

**Очікується:** документ `contoso-release-notes-1.5.1`, чанк містить «експоненційною паузою» — знайдено чанків: 1

`contoso-release-notes-1.5.1#000` · Contoso Procurement — Release Notes 1.5.1 (hotfix) › Contoso Procurement — Release Notes 1.5.1 (hotfix) (+1)

~~~~text
# Contoso Procurement — Release Notes 1.5.1 (hotfix)
Дата релізу: 02.07.2026. Hotfix-реліз. Solution: ContosoCore_1_5_1_managed.
## Виправлення
- Plugin cnt_ApprovalValidation: усунено NullReferenceException при відхиленні погодження з порожнім коментарем (регресія 1.5.0).
- Flow «LEO Task Sync»: додано повтор з експоненційною паузою при помилці 429 Too Many Requests.
- Approval Flow v2: повторний запуск з run history більше не створює дубль інвойсу — запис оновлюється за cnt_invoicenumber.
~~~~

> **Примітка:** runbook теж згадує 429 — схожий документ

---

## r04 · базове · відповідь у таблиці · ✅

**Питання:** За який час треба відреагувати на інцидент Critical?

**Очікується:** документ `contoso-support-runbook`, чанк містить «30 хвилин» — знайдено чанків: 1

`contoso-support-runbook#002` · Contoso Procurement — Runbook підтримки › Contoso Procurement — Runbook підтримки > Класифікація серйозності інцидентів

~~~~text
## Класифікація серйозності інцидентів
Severity | Критерій | Час реакції
Critical | Зупинено погодження або оплату на PROD | 30 хвилин
High | Функція недоступна є обхідний шлях
, | 4 години
Medium | Часткова деградація не блокує роботу
, | 2 робочі дні
Low | Косметичні проблеми | Наступний реліз
~~~~

---

## r05 · базове · відповідь у таблиці · ✅

**Питання:** Який тест-кейс перевіряє лист погоджувачу в Approval Flow v2?

**Очікується:** документ `contoso-regression-test-plan-1.5`, чанк містить «TC-110» — знайдено чанків: 1

`contoso-regression-test-plan-1.5#001` · Contoso Procurement — Регресійний тест-план 1.5 › Contoso Procurement — Регресійний тест-план 1.5 > Тест-кейси

~~~~text
## Тест-кейси
ID | Компонент | Сценарій | Пріоритет
TC-101 | canvas app «Заявки на закупівлю» | Створення заявки з вкладенням 8 MB | High
TC-104 | cnt_request | Заявка понад 50 000 грн без центру витрат не зберігається | High
TC-110 | Approval Flow v2 | Погодження заявки: лист погоджувачу з посиланням | High
TC-112 | Approval Flow v2 | Повторний запуск з run history не створює дубль інвойсу | High
TC-118 | canvas app «Заявки на закупівлю» | Кнопка Reject активна для заявок понад 100 000 грн | Medium
TC-120 | cnt_ApprovalValidation | Відхилення без коментаря показує повідомлення, а не помилку | High
TC-125 | LEO Task Sync | Синхронізація 500 задач без помилки 429 | Medium
TC-130 | Project Hub | Кнопка «Затвердити бюджет» видима для ролі Project Manager | High
TC-134 | Project Hub | Форма проєкту відкривається менш ніж за 5 секунд на PROD-подібних даних | Medium
~~~~

---

## r06 · базове · мова питання = мова документа · ✅

**Питання:** How do I package solution components from a local folder into a solution.zip with pac?

**Очікується:** документ `learn-cli-solution`, чанк містить «Package solution components on local filesystem into solution.zip» — знайдено чанків: 2

`learn-cli-solution#001` · Microsoft Power Platform CLI solution command group › pac solution > Commands

~~~~text
## Commands
Command | Description
pac solution add-license | Add license and plan info to the solution.
pac solution add-reference | Adds a reference from the project in the current directory to the project at 'path'
pac solution add-solution-component | Add one or more solution components to the target unmanaged solution in Dataverse.
pac solution check | Upload a Dataverse solution project to run against the Power Apps Checker service.
pac solution clone | Create a solution project based on an existing solution in your organization.
pac solution create-settings | Create a settings file from solution zip or solution folder.
pac solution delete | Delete a solution from Dataverse in the current environment.
pac solution export | Export a solution from Dataverse.
pac solution import | Import the solution into Dataverse.
pac solution init | Initializes a directory with a new Dataverse solution project
pac solution list | List all Solutions from the current Dataverse organization
pac solution online-version | Gets or sets version for solution loaded in Dataverse.
pac solution pack | Package solution components on local filesystem into solution.zip (SolutionPackager).
pac solution publish | Publishes all customizations
pac solution sync | Sync the current Dataverse solution project to the current state of the solution in your organization.
pac solution unpack | Extract solution components from solution.zip onto local filesystem (SolutionPackager).
pac solution upgrade | Apply solution upgrade
pac solution version | Update build or revision version for the solution.
~~~~

`learn-cli-solution#043` · Microsoft Power Platform CLI solution command group › pac solution > pac solution pack (+3)

~~~~text
## pac solution pack
Package solution components on local filesystem into solution.zip (SolutionPackager).
### Example
pac solution pack --zipfile C:\SampleSolution.zip --folder.\SampleSolutionUnpacked\.
### Required Parameters for solution pack
#### --zipfile -z
The full path to the solution ZIP file
~~~~

> **Примітка:** pack і unpack мають схожі параметри

---

## r07 · базове · питання українською, документ англійською · ✅

**Питання:** Чи можна імпортувати managed solution у середовище, де є його вихідний unmanaged solution?

**Очікується:** документ `learn-alm-solution-concepts`, чанк містить «can't import a managed solution into the same environment» — знайдено чанків: 1

`learn-alm-solution-concepts#002` · Solution concepts with Power Platform › Solution concepts > Managed and unmanaged solutions

~~~~text
- Managed solutions are deployed. Managed solutions are deployed to any environment that isn't a development environment for that solution. These environments include test, user acceptance testing (UAT), system integration testing (SIT), and production environments. Managed solutions can be serviced independently from other managed solutions in an environment. As an ALM best practice, managed solutions should be generated by exporting an unmanaged solution as managed and considered a build artifact. Additionally: You can't edit components directly within a managed solution. To edit managed components, first add them to an unmanaged solution. When you edit a managed component, you create a dependency between your unmanaged customizations and the managed solution. When a dependency exists, the managed solution can't be uninstalled until you remove the dependency. Some managed components can’t be edited. To verify whether a component can be edited, view the Managed properties. You can't export a managed solution. But you can export an unmanaged solution as managed. When a managed solution is deleted (uninstalled), all the customizations and extensions included with it are removed.
Important
- You can't import a managed solution into the same environment that contains the originating unmanaged solution. To test a managed solution, you need a separate environment to import it into.
- When you delete a managed solution, the following data is lost: data stored in custom tables that are part of the managed solution and data stored in custom columns that are part of the managed solution on other tables that aren't part of the managed solution.
~~~~

---

## r08 · базове · точний ідентифікатор (номер issue) · ✅

**Питання:** Which CoE Starter Kit release fixed issue #9508 about the Environments with no Apps or Flows report?

**Очікується:** документ `coe-release-february2026`, чанк містить «#9508» — знайдено чанків: 1

`coe-release-february2026#003` · CoE Starter Kit release notes — February 2026 › Change Log (+1)

~~~~text
## Change Log
### 🐛 CoE Starter Kit - BUGS (25)
- #9508-[CoE Starter Kit - BUG] Wrong Report "Environments with no Apps or Flows"
- #9537-[CoE Starter Kit - Bug/Question] Inactivity notification process Configuration - cannot share Apps with admin or maker group
- #9539-[CoE Starter Kit - BUG] Admin | Inactivity notifications - Email template by giving a hyperlink
- #9882-[CoE Starter Kit - BUG] Users who belong to a Microsoft 365 group linked to a Microsoft Teams environment are classified as System Admins
- #10463-[CoE Starter Kit - BUG] Developer Compliance Center is inconsistent when setting the Risk Assessment State between Apps, Bots, and Flows
- #10606-[CoE Starter Kit - BUG] [CoE Starter Kit - BUG] FullInventory env var locked and Admin | Sync Template v4 (Flows) not updating flow names in large tenant
- #10629-[CoE Starter Kit - BUG] All Cloud deleted from an Environment
- #10633-[CoE Starter Kit - BUG] Link to latest version is not updated
- #10641-[CoE Starter Kit - BUG] ISSUE TITLE
- #10644-[CoE Starter Kit - BUG] Admin | Audit Logs | Office 365 Management API Subscription Flow Fails
~~~~

---

## r09 · базове · мова питання = мова документа · ✅

**Питання:** Які environment variables треба заповнити під час встановлення Contoso 1.5?

**Очікується:** документ `contoso-install-guide-1.5`, чанк містить «cnt_LeoApiKey» — знайдено чанків: 2

`contoso-install-guide-1.5#000` · Contoso Procurement — Інструкція зі встановлення 1.5 › Contoso Procurement — Інструкція зі встановлення 1.5 (+1)

~~~~text
# Contoso Procurement — Інструкція зі встановлення 1.5
Актуальна інструкція для версій 1.5.0 і новіших. Замінює інструкцію 1.4.
## Передумови
- pac CLI версії 1.44 або новішої (нижчі версії не підтримують пакування ContosoCore_Invoices).
- Роль System Administrator у цільовому середовищі.
- Сервісний акаунт svc-contoso-flows з ліцензією Power Automate Premium — особисті підключення заборонені.
- Доступ до API LEO PPM (ключ зберігається в environment variable cnt_LeoApiKey).
~~~~

`contoso-install-guide-1.5#001` · Contoso Procurement — Інструкція зі встановлення 1.5 › Contoso Procurement — Інструкція зі встановлення 1.5 > Порядок встановлення

~~~~text
## Порядок встановлення
- Імпортувати ContosoCore_Invoices_managed.zip (обов'язково першим, інакше — помилка missing dependency на cnt_invoice).
- Імпортувати ContosoCore_1_5_x_managed.zip командою pac solution import --activate-plugins.
- Прив'язати connection reference cnt_sharedoffice365 до сервісного акаунта svc-contoso-flows.
- Заповнити environment variables cnt_LeoApiKey і cnt_LeoBaseUrl.
- Увімкнути flows «Approval Flow v2» і «LEO Task Sync».
~~~~

---

## r10 · базове · є схожий документ-пастка · ✅

**Питання:** У якому статусі тепер створюється клон погодженої заявки?

**Очікується:** документ `contoso-release-notes-1.5.2`, чанк містить «статусі Draft» — знайдено чанків: 1

`contoso-release-notes-1.5.2#001` · Contoso Procurement — Release Notes 1.5.2 › Contoso Procurement — Release Notes 1.5.2 > Виправлення

~~~~text
## Виправлення
- Клон погодженої заявки тепер створюється в статусі Draft (проблема з 1.5.1).
- Роль Project Manager знову бачить кнопку «Затвердити бюджет» (регресія 1.4.3 на PROD).
~~~~

> **Примітка:** release notes 1.5.1 описують стару поведінку (Approved)

---

## r11 · базове · мова питання = мова документа · ✅

**Питання:** Which connectors must the data policy allow for the CoE Starter Kit environment?

**Очікується:** документ `learn-coe-setup`, чанк містить «Validate data policies» — знайдено чанків: 1

`learn-coe-setup#008` · Set up the CoE Starter Kit: Prerequisites and instructions › Set up the CoE Starter Kit: Prerequisites and instructions > Create your environments > Validate data policies

~~~~text
### Validate data policies
The data policy applied to your CoE Starter Kit environment must allow the following connectors to be used together in the business group:
- Approvals
- Azure Resource Manager
- HTTP
- HTTP with Microsoft Entra ID (preauthorized)
- Microsoft Dataverse
- Microsoft Dataverse (legacy)
- Microsoft Teams
- Office 365 Groups
- Office 365 Outlook
- Office 365 Users
- Power Apps for Admins
- Power Apps for Makers
- Power Automate for Admins
- Power Automate Management
- Power Platform for Admins
- Power Platform for Admins V2
- Power Query Dataflows
- RSS
Note
The CoE Starter Kit collects information about who owns a resource, such as an app or a flow.
- If the resource is owned by an interactive user, the Office 365 Users connector is used to collect the owner details.
- If the resource is owned by a service principal (app user), the HTTP with Microsoft Entra ID (preauthorized) connector makes a call to Microsoft Graph to retrieve the app user name to correctly mark ownership of resources to avoid them being marked as orphaned (without an owner).
~~~~

---

## r12 · базове · питання українською, документ англійською · ✅

**Питання:** Яка команда pac відправляє PCF-компонент у середовище Dataverse?

**Очікується:** документ `learn-cli-pcf`, чанк містить «pac pcf push» — знайдено чанків: 2

`learn-cli-pcf#000` · Microsoft Power Platform CLI pcf command group › pac pcf (+1)

~~~~text
# pac pcf
Commands for working with Power Apps component framework projects.
Create and build a code component explains how to use these commands.
## Commands
Command | Description
pac pcf init | Initializes a directory with a new Power Apps component framework project
pac pcf push | Import the Power Apps component framework project into the current Dataverse organization
pac pcf version | Patch version for controls
~~~~

`learn-cli-pcf#005` · Microsoft Power Platform CLI pcf command group › pac pcf > pac pcf push (+3)

~~~~text
## pac pcf push
Import the Power Apps component framework project into the current Dataverse organization
### Example
pac pcf push --publisher-prefix dev
### Optional Parameters for pcf push
#### --environment -env
Specifies the target Dataverse. The value may be a Guid or absolute https URL. When not specified, the active organization selected for the current auth profile will be used.
~~~~

---

## r13 · базове · мова питання = мова документа · ✅

**Питання:** Який ліміт запитів до API LEO PPM на годину?

**Очікується:** документ `contoso-support-runbook`, чанк містить «1 000 запитів» — знайдено чанків: 1

`contoso-support-runbook#001` · Contoso Procurement — Runbook підтримки › Contoso Procurement — Runbook підтримки > LEO Task Sync падає з помилкою 429

~~~~text
## LEO Task Sync падає з помилкою 429
- Переконатися, що встановлено версію 1.5.1 або новішу (з повтором при 429).
- Перевірити ліміт API у LEO PPM: 1 000 запитів на годину на тенант.
- Якщо помилка повторюється більше 3 годин — створити інцидент Severity High.
~~~~

---

## r14 · базове · питання українською, документ англійською · ✅

**Питання:** Як часто виходять нові версії CoE Starter Kit?

**Очікується:** документ `learn-coe-after-setup`, чанк містить «How often new versions» — знайдено чанків: 1

`learn-coe-after-setup#001` · Update the Center of Excellence (CoE) Starter Kit › Update the Center of Excellence (CoE) Starter Kit > How often new versions are released

~~~~text
## How often new versions are released
A new version of the CoE Starter Kit is released monthly, usually in the first full week of each month. This release cadence is important to know so that you can review, organize, plan, and test the latest version.
Updates (bug fixes, enhancements, new features, and deprecations) are announced through GitHub release notes.
~~~~

---

## r15 · базове · питання українською, документ англійською · ✅

**Питання:** Які середовища, крім production, Microsoft радить мати для ALM?

**Очікується:** документ `learn-alm-environment-strategy`, чанк містить «test, UAT, SIT» — знайдено чанків: 1

`learn-alm-environment-strategy#002` · ALM environment strategy considerations › Environment strategy for ALM > Other environments

~~~~text
## Other environments
You should also answer the question, "Which types of non-development environments do I need?"
For example, in addition to your production environment, you might need separate test, UAT, SIT, and pre-production environments. Notice that, at a minimum, any healthy ALM practice should include using a test environment prior to deploying anything to the production environment. This ensures that you have a place to test your app, but also ensures that the deployment itself can be tested.
More information: Establishing an environment strategy for Microsoft Power Platform
~~~~

---

## r16 · складне · є схожий документ-пастка · ✅

**Питання:** Скільки багів виправили в релізі CoE Starter Kit за січень 2026?

**Очікується:** документ `coe-release-january2026`, чанк містить «BUGS (38)» — знайдено чанків: 1

`coe-release-january2026#003` · CoE Starter Kit release notes — January 2026 › Change Log (+1)

~~~~text
## Change Log
### 🐛 CoE Starter Kit - BUGS (38)
- #8576-[CoE Starter Kit - BUG] Sys Admin PIM workaround not working with GCC
- #8913-[CoE Starter Kit - BUG] CustomControlDefaultConfig error - can't import Core Components solution
- #9740-[CoE Starter Kit - BUG] Clean Up App URL in email notification not working
- #9763-[CoE Starter Kit - BUG] Agents missing in admin_PVA table
- #10002-Flow Admin | Sync Template v4 (Driver) never finishes in GCC High Tenant
- #10005-[CoE Starter Kit - BUG] Production Apps are marked as Deleted in Cloud Flow Inventory in Power Platform Admin View App
- #10044-[CoE Starter Kit - BUG] Admin | Sync Template v3 (Environment Properties) Flow Missing after Core Components 4.50.1
- #10282-[CoE Starter Kit - BUG] ISSUE TITLE
- #10300-[CoE Starter Kit - BUG] ISSUE TITLE: Error on "Configure welcome emails" in Setup wizard
- #10395-[CoE Starter Kit - BUG] Issues with Flow Permission Center
- #10405-[CoE Starter Kit - BUG] SYNC HELPER - Get Security Role Users - 'admin_EnvironmentSecurityRolePermission' With Id '' Does Not Exist
~~~~

> **Примітка:** заголовок «BUGS (N)» є в кожному з 18 релізів — треба вибрати правильний місяць

---

## r17 · складне · є схожий документ-пастка · ✅

**Питання:** In which CoE Starter Kit release was the Sync Audit Logs (V2) bug 'Start time and end time must both be specified' fixed?

**Очікується:** документ `coe-release-december2025`, чанк містить «Start time and end time must both be specified» — знайдено чанків: 1

`coe-release-december2025#003` · CoE Starter Kit release notes — December 2025 › Change Log (+1)

~~~~text
## Change Log
### 🐛 CoE Starter Kit - BUGS (57)
- #9058-[CoE Starter Kit - BUG] Data Policy Impact Analysis - inconsistent reporting of non-business connector group
- #9622-[CoE Starter Kit - BUG] Parse Inventory Action for 5 Flows fails with error - Invalid Type. Expected String but got Null.
- #9683-[CoE Starter Kit - BUG] Failed to Upgrade CoE (Core Components) with "the same key has already been added" Error
- #9911-[CoE Starter Kit - BUG] Admin | Audit Logs | Sync Audit Logs (V2) - Start time and end time must both be specified
- #9953-[CoE Starter Kit - BUG] Advisory ticket. We would like to transfer account owning the CoE Starter Kit to new Service Account. Need advice and guidance on steps involved in the process for a clean transition.
- #9972-[CoE Starter Kit - BUG] Admin | Sync Template v3 (Flow Action Details) - Cannot Enable Flow
- #9974-[CoE Starter Kit - BUG] Bots, solutions, powerpages... tables are not populated by condition in Sync Template flows
- #9978-[CoE Starter Kit - BUG] SharePoint form apps
- #9979-Issue with COE Power BI Report Marking Active Flows and Apps as Deleted
~~~~

> **Примітка:** Sync Audit Logs (V2) згадується в 17 чанках різних релізів

---

## r18 · складне · є схожий документ-пастка · ✅

**Питання:** Що робить параметр --packagetype саме в команді pac solution clone?

**Очікується:** документ `learn-cli-solution`, чанк містить «Specifies the extraction type for the solution» — знайдено чанків: 1

`learn-cli-solution#021` · Microsoft Power Platform CLI solution command group › pac solution > pac solution clone > Optional Parameters for solution clone > --outputDirectory -o (+2)

~~~~text
#### --outputDirectory -o
Output directory
#### --packagetype -p
Specifies the extraction type for the solution. Can be: 'Unmanaged', 'Managed' or 'Both'. The default value is: 'Both'.
#### --targetversion -v
Deprecated: This parameter is ignored.
~~~~

> **Примітка:** --packagetype є також у pack і sync з іншим описом

---

## r19 · складне · перефразоване питання без ключових слів документа · ✅

**Питання:** Які дані зникнуть, якщо видалити managed solution із середовища?

**Очікується:** документ `learn-alm-solution-concepts`, чанк містить «following data is lost» — знайдено чанків: 1

`learn-alm-solution-concepts#002` · Solution concepts with Power Platform › Solution concepts > Managed and unmanaged solutions

~~~~text
- Managed solutions are deployed. Managed solutions are deployed to any environment that isn't a development environment for that solution. These environments include test, user acceptance testing (UAT), system integration testing (SIT), and production environments. Managed solutions can be serviced independently from other managed solutions in an environment. As an ALM best practice, managed solutions should be generated by exporting an unmanaged solution as managed and considered a build artifact. Additionally: You can't edit components directly within a managed solution. To edit managed components, first add them to an unmanaged solution. When you edit a managed component, you create a dependency between your unmanaged customizations and the managed solution. When a dependency exists, the managed solution can't be uninstalled until you remove the dependency. Some managed components can’t be edited. To verify whether a component can be edited, view the Managed properties. You can't export a managed solution. But you can export an unmanaged solution as managed. When a managed solution is deleted (uninstalled), all the customizations and extensions included with it are removed.
Important
- You can't import a managed solution into the same environment that contains the originating unmanaged solution. To test a managed solution, you need a separate environment to import it into.
- When you delete a managed solution, the following data is lost: data stored in custom tables that are part of the managed solution and data stored in custom columns that are part of the managed solution on other tables that aren't part of the managed solution.
~~~~

---

## r20 · складне · перефразоване питання без ключових слів документа · ✅

**Питання:** Який тест перевіряє, що картка проєкту в Project Hub не відкривається надто довго?

**Очікується:** документ `contoso-regression-test-plan-1.5`, чанк містить «TC-134» — знайдено чанків: 1

`contoso-regression-test-plan-1.5#001` · Contoso Procurement — Регресійний тест-план 1.5 › Contoso Procurement — Регресійний тест-план 1.5 > Тест-кейси

~~~~text
## Тест-кейси
ID | Компонент | Сценарій | Пріоритет
TC-101 | canvas app «Заявки на закупівлю» | Створення заявки з вкладенням 8 MB | High
TC-104 | cnt_request | Заявка понад 50 000 грн без центру витрат не зберігається | High
TC-110 | Approval Flow v2 | Погодження заявки: лист погоджувачу з посиланням | High
TC-112 | Approval Flow v2 | Повторний запуск з run history не створює дубль інвойсу | High
TC-118 | canvas app «Заявки на закупівлю» | Кнопка Reject активна для заявок понад 100 000 грн | Medium
TC-120 | cnt_ApprovalValidation | Відхилення без коментаря показує повідомлення, а не помилку | High
TC-125 | LEO Task Sync | Синхронізація 500 задач без помилки 429 | Medium
TC-130 | Project Hub | Кнопка «Затвердити бюджет» видима для ролі Project Manager | High
TC-134 | Project Hub | Форма проєкту відкривається менш ніж за 5 секунд на PROD-подібних даних | Medium
~~~~

> **Примітка:** у документі — «менш ніж за 5 секунд»; TC-130 теж про Project Hub

---

## r21 · складне · перефразоване питання без ключових слів документа · ✅

**Питання:** У якій версії Contoso з'явилась роль лише для перегляду заявок та інвойсів?

**Очікується:** документ `contoso-release-notes-1.4.3`, чанк містить «Procurement Auditor» — знайдено чанків: 1

`contoso-release-notes-1.4.3#001` · Contoso Procurement — Release Notes 1.4.3 › Contoso Procurement — Release Notes 1.4.3 > Нові можливості

~~~~text
## Нові можливості
- Model-driven app «Project Hub»: кнопка «Затвердити бюджет» на формі проєкту для ролі Project Manager.
- Нова security role «Procurement Auditor» з доступом лише на читання до cnt_request і cnt_invoice.
~~~~

> **Примітка:** у питанні немає назви ролі

---

## r22 · складне · перефразоване питання без ключових слів документа · ✅

**Питання:** Як перевірити solution на типові помилки з командного рядка перед деплоєм?

**Очікується:** документ `learn-cli-solution`, чанк містить «run against the Power Apps Checker service» — знайдено чанків: 2

`learn-cli-solution#001` · Microsoft Power Platform CLI solution command group › pac solution > Commands

~~~~text
## Commands
Command | Description
pac solution add-license | Add license and plan info to the solution.
pac solution add-reference | Adds a reference from the project in the current directory to the project at 'path'
pac solution add-solution-component | Add one or more solution components to the target unmanaged solution in Dataverse.
pac solution check | Upload a Dataverse solution project to run against the Power Apps Checker service.
pac solution clone | Create a solution project based on an existing solution in your organization.
pac solution create-settings | Create a settings file from solution zip or solution folder.
pac solution delete | Delete a solution from Dataverse in the current environment.
pac solution export | Export a solution from Dataverse.
pac solution import | Import the solution into Dataverse.
pac solution init | Initializes a directory with a new Dataverse solution project
pac solution list | List all Solutions from the current Dataverse organization
pac solution online-version | Gets or sets version for solution loaded in Dataverse.
pac solution pack | Package solution components on local filesystem into solution.zip (SolutionPackager).
pac solution publish | Publishes all customizations
pac solution sync | Sync the current Dataverse solution project to the current state of the solution in your organization.
pac solution unpack | Extract solution components from solution.zip onto local filesystem (SolutionPackager).
pac solution upgrade | Apply solution upgrade
pac solution version | Update build or revision version for the solution.
~~~~

`learn-cli-solution#010` · Microsoft Power Platform CLI solution command group › pac solution > pac solution check (+3)

~~~~text
## pac solution check
Upload a Dataverse solution project to run against the Power Apps Checker service.
### Example
pac solution check --path c:\Users\Documents\Solution.zip --outputDirectory c:\samplepackage --geo UnitedStates
### Optional Parameters for solution check
#### --clearCache -cc
Clears the solution checker enforcement cache, for your tenant, of all records that pertain to past results for your solutions.
This parameter requires no value. It's a switch.
~~~~

> **Примітка:** у питанні немає слів check / Checker

---

## r23 · складне · є схожий документ-пастка · ✅

**Питання:** Що треба зробити перед встановленням оновлення CoE Starter Kit, якщо ви змінювали його flows?

**Очікується:** документ `learn-coe-after-setup`, чанк містить «Remove unmanaged layers from inventory flows» — знайдено чанків: 1

`learn-coe-after-setup#005` · Update the Center of Excellence (CoE) Starter Kit › Update the Center of Excellence (CoE) Starter Kit > Install updates > Remove unmanaged layers from inventory flows

~~~~text
### Remove unmanaged layers from inventory flows
Before installing the upgrade, check that the solution is in a healthy state to receive the new updates.
Making any changes to flows or apps in the solution creates an unmanaged layer. Components with unmanaged layers don't receive updates until you remove that unmanaged layer. Learn more in Solution layers.
All flows with Admin | Sync Template v in the name are responsible for collecting your tenant's inventory and building the foundation that the CoE Starter Kit relies on. Don't customize these flows. If you have additional requirements on what inventory to collect, raise a feature ask or create your own flow. Learn more in Extend and customize CoE Starter Kit components.
Before installing the upgrade, remove unmanaged layers from the inventory flows.
Note
You might unknowingly create an unmanaged layer by selecting Edit to look at flow actions or by modifying the run-only properties of the flow.
You can check for unmanaged layers on the inventory flows by using the CoE Admin Command Center app.
- Open the CoE Admin Command Center app from your CoE environment.
- Select CoE flows from the navigation menu.
- Check if any of the flows show the layer icon, indicating they have unmanaged layers.
- Select the layer icon to go to the solution layer page of the flow and remove the unmanaged layer.
~~~~

> **Примітка:** FAQ і release notes листопада 2025 теж згадують unmanaged layers

---

## r24 · складне · є застаріла версія документа · ✅

**Питання:** Що потрібно зробити з connection reference cnt_sharedoffice365 після оновлення до 1.4.3?

**Очікується:** документ `contoso-release-notes-1.4.3`, чанк містить «вручну прив'язати» — знайдено чанків: 1

`contoso-release-notes-1.4.3#003` · Contoso Procurement — Release Notes 1.4.3 › Contoso Procurement — Release Notes 1.4.3 > Відомі проблеми

~~~~text
## Відомі проблеми
- Після оновлення connection reference cnt_sharedoffice365 потрібно вручну прив'язати до сервісного акаунта в кожному середовищі.
~~~~

> **Примітка:** інструкція 1.5 і runbook теж згадують cnt_sharedoffice365

---

## r25 · складне · правильних чанків кілька · ✅

**Питання:** У якому релізі CoE виправили проблему, коли flow Inactivity notifications v2 (Clean Up and Delete) не вмикався?

**Очікується:** документ `coe-release-september2025`, чанк містить «won't turn on» — знайдено чанків: 1

`coe-release-september2025#007` · CoE Starter Kit release notes — September 2025 › Change Log (+1)

~~~~text
- #10127-[CoE Starter Kit - BUG] AI metadata not populating in Admin View
- #10130-[CoE Starter Kit - BUG] DLP Impact Analysis Tool shows incorrect cached results across multiple tenants
- #10131-[CoE Starter Kit - BUG] ISSUE TITLE
- #10132-[CoE Starter Kit - BUG] - Permissions, turn off and delete flow dialogs empty
- #10133-[CoE Starter Kit - BUG] Cannot get Audit (Usage) Flows to work - NEED HELP
- #10136-[CoE Starter Kit - BUG] Request Orphaned Objects Reassigned Child Always Returns Success to Parent
- #10137-[CoE Starter Kit - BUG] ISSUE TITLE - Flow Last Run On Field is unavailable in the Power Bi DashBoards of CoE Solution
- #10146-[CoE Starter Kit - BUG] ISSUE TITLE - App Last Launched On is empty and Flow Last Run On is empty
- #10147-[CoE Starter Kit v4.5 - BUG] - the "Admin | Sync Template v4 (Driver)" solution flow is not completing Inventory for CareFirst BCBS
- #10148-[CoE Starter Kit - BUG] Admin | Inactivity notifications v2 (Clean Up and Delete) won't turn on
~~~~
**Очікується:** документ `coe-release-august2025`, чанк містить «won't turn on» — знайдено чанків: 1

`coe-release-august2025#004` · CoE Starter Kit release notes — August 2025 › Change Log (+1)

~~~~text
- #10055-CoE Started Tool kit - Power Automate Flow "Admin | Audit Logs | Sync Audit Logs (V2)" if failing
- #10056-[CoE Starter Kit - BUG] Inactivity notifications 2 Clean up and Delete flow won't turn on
- #10060-[CoE Starter Kit - BUG] Unable to assign new Owner to a Flow that is part of a solution
- #10066-[CoE Starter Kit - BUG] Developer Environments activity
- #10075-[CoE Starter Kit - BUG] Connector name is missing in the 'Connectors' section of Environment Creation Requests
- #10079-[CoE Starter Kit - BUG] Passwords Containing Plaintext still set to YES
- #10082-[CoE Starter Kit - BUG] Flow Last Run On Date not populating
- #10083-[CoE Starter Kit - BUG] Admin | Sync Blog Posts is missing
- #10086-[CoE Starter Kit - BUG] SYNC HELPER - Get Security Role Users keeps failing
- #10087-Unable to Deploy Powerpage based solution using ALM
- #10089-[CoE Starter Kit - BUG] errors with wizard no automate displayed
- #10094-[CoE Starter Kit - BUG] ISSUE TITLE
- #10095-[CoE Starter Kit - BUG] Last Launched Date Wrong Time Zone
~~~~

> **Примітка:** два правильні релізи; ще 5 чанків згадують Inactivity notifications
