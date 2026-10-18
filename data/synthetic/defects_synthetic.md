# defects_synthetic.jsonl

20 записів. Згенеровано з `defects_synthetic.jsonl`, не редагуйте вручну.

---

## syn-001

`source: synthetic` · `channel: devops`

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

---

## syn-002

`source: synthetic` · `channel: teams`

дівчата, флоу погодження знову впав на проді 😭 ніхто не отримує листи з ранку

---

## syn-003

`source: synthetic` · `channel: email`

Добрий день! Звертаюсь щодо проблеми, яка виникла після оновлення минулого тижня. Коли я відкриваю картку проєкту в Project Hub і переходжу на вкладку Gantt, задачі відображаються з неправильними датами — усі зсунуті на один день назад. До оновлення такого не було. Перевіряла в Chrome і Edge, однаково. Це заважає планувати спринт, прошу подивитись якомога швидше. Дякую, Ірина, PMO

---

## syn-004

`source: synthetic` · `channel: devops`

Plugin cnt_ApprovalValidation throws NullReferenceException on update of cnt_approval when Status = Rejected and Comment is empty. Found in TEST during regression for 1.5.0. Worked fine in 1.4.x. Stack: System.NullReferenceException: Object reference not set to an instance of an object. at Contoso.Plugins.ApprovalValidation.Execute(IServiceProvider sp). Prio: medium, workaround = fill comment.

---

## syn-005

`source: synthetic` · `channel: teams`

при імпорті солюшена на тест вилітає помилка міссінг депенденсі на таблицю cnt_invoice. на деві все ок. реліз 1.5.0 блокує деплой!!! терміново

---

## syn-006

`source: synthetic` · `channel: devops`

Користувачі з роллю Project Manager не бачать кнопку «Затвердити бюджет» на формі проєкту (model-driven, Project Hub). Адміни бачать. Середовище PROD, після релізу 1.4.3 вчора.
Очікувано: PM має бачити кнопку.
Кроки: залогінитись під PM -> відкрити будь-який проєкт у статусі Draft -> кнопки нема.

---

## syn-007

`source: synthetic` · `channel: teams`

щось не так з звітами. цифри не сходяться. подивіться пліз

---

## syn-008

`source: synthetic` · `channel: devops`

PCF контрол для вибору дат (cnt.DateRangePicker) на мобілці не відкривається календар. iOS 18, Power Apps mobile. На десктопі норм. Env: UAT. low priority мабуть, бо мобілкою мало хто користується

---

## syn-009

`source: synthetic` · `channel: email`

Sync LEO PPM -> Dataverse: задачі з ЛЕО не підтягуються в таблицю cnt_projecttask з 12.10. В run history флоу 'LEO Task Sync' помилка 429 Too Many Requests, після 3 retry фейлиться. Prod. Критично — PMи не бачать актуальний план, статус-репорт в пʼятницю.

---

## syn-010

`source: synthetic` · `channel: devops`

[BUG] Duplicate records in cnt_invoice after Approval Flow v2 rerun
Release: 1.5.1 (hotfix)
Коли флоу перезапускається вручну з run history, він створює дубль інвойсу замість оновлення існуючого. Expected: upsert by cnt_invoicenumber. Actual: новий запис з тим самим номером. Також зачіпає cnt_request (статус двічі міняється). Env – test & uat. Це регресія, в 1.5.0 було ок.

---

## syn-011

`source: synthetic` · `channel: email`

Доброго дня. Не можу додати рахунок у системі заявок, пише що в мене немає прав. Вчора могла. Що робити? Олена, фінвідділ

---

## syn-012

`source: synthetic` · `channel: test_run`

TC-118 FAIL. canvas Заявки, екран Approve, кнопка Reject неактивна якщо сума > 100000. rel 1.5.0 / TEST. sev med

---

## syn-013

`source: synthetic` · `channel: teams`

Pipeline deploy to UAT failed on step 'Import solution ContosoCore_1_5_2_managed'. Error: The solution file is invalid. The compressed file must contain the following files at its root: solution.xml, customizations.xml. Схоже, артефакт зібрався криво. Не блокер для тестів поки, але реліз у четвер.

---

## syn-014

`source: synthetic` · `channel: teams`

Апдейт по флоу погодження: впав через те що connection reference cnt_sharedoffice365 в PROD був привʼязаний до акаунта звільненого співробітника. Перепривʼязали — працює. Але треба розібратись чому після релізу 1.4.3 ref вказує не на сервісний акаунт. sev: high (було), зараз low

---

## syn-015

`source: synthetic` · `channel: email`

У Ганті (LEO) при перетягуванні задачі мишкою залежні задачі не зсуваються. Хоча звʼязок FS є. Пробувала на 3 проєктах. Не знаю чи це баг чи так задумано 🤷‍♀️

---

## syn-016

`source: synthetic` · `channel: devops`

Форма проєкту в Project Hub вантажиться 15-20 сек на PROD (на TEST 3 сек). Почалось після того як додали subgrid з cnt_projecttask і cnt_risk. Користувачі скаржаться. Monitor показує купу запитів RetrieveMultiple

---

## syn-017

`source: synthetic` · `channel: email`

Привіт! Значить ситуація така: беру заявку яка вже погоджена, хочу її скопіювати (кнопка Clone), міняю постачальника і суму, зберігаю — а в копії лишається статус Approved і вона одразу йде в оплату, минаючи погодження!!! Це ж дірка в процесі. Перевіряла на уат, версія вроді 1.5.1 але не впевнена. На проді не пробувала і боюсь пробувати)) Очікую що копія створюється в статусі Draft.

---

## syn-018

`source: synthetic` · `channel: release_notes`

Known issue (1.5.2): Business rule 'Set default currency' on cnt_request doesn't fire when the form is opened via quick create. Users must select currency manually. Fix planned for 1.5.3. Low impact.

---

## syn-019

`source: synthetic` · `channel: teams`

{"error":{"code":"0x80040237","message":"A record with matching key values already exists: cnt_projectcode"}}
це при створенні проєкту з шаблону LEO, dev

---

## syn-020

`source: synthetic` · `channel: teams`

Не баг, але: було б добре щоб в Approval Flow приходило нагадування якщо заявка не погоджена 3 дні. Зараз висить тиждень і ніхто не знає. prod
