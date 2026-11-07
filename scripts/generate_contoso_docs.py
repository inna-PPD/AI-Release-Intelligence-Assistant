"""Генерує синтетичну частину RAG-корпусу: документи вигаданої компанії Contoso (DOCX і PDF).

Світ той самий, що й у кейсі 1 (таблиці cnt_*, Approval Flow v2, LEO Task Sync, релізи 1.4.x–1.5.x).
Навмисні «пастки» для тестсету:
- дві версії інструкції зі встановлення (1.4 — застаріла, 1.5 — актуальна) з різними вимогами;
- схожі release notes сусідніх версій (1.5.1 hotfix vs 1.5.2).

DOCX — python-docx (справжні стилі Heading / List / Table); PDF — HTML → Microsoft Edge headless.
Запуск (Windows, потрібен Edge): python scripts/generate_contoso_docs.py
"""

import html
import json
import subprocess
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "corpus" / "raw"
SOURCES = ROOT / "data" / "corpus" / "sources.json"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# Блоки: ("h1"|"h2"|"h3"|"p", текст) · ("ul"|"ol", [пункти]) · ("table", [[заголовки], [рядок], ...])
DOCS = {
    "contoso-release-notes-1.4.2": {
        "format": "docx", "version": "1.4.2", "date": "2026-03-17",
        "title": "Contoso Procurement — Release Notes 1.4.2",
        "blocks": [
            ("h1", "Contoso Procurement — Release Notes 1.4.2"),
            ("p", "Дата релізу: 17.03.2026. Середовища: DEV → TEST → UAT → PROD. Solution: ContosoCore_1_4_2_managed."),
            ("h2", "Нові можливості"),
            ("ul", [
                "Canvas app «Заявки на закупівлю»: додано вкладення до заявки (до 10 MB на файл).",
                "Таблиця cnt_request: нове поле cnt_costcenter (центр витрат), обов'язкове для заявок понад 50 000 грн.",
                "Approval Flow v2: погоджувач отримує лист із прямим посиланням на заявку.",
            ]),
            ("h2", "Виправлення"),
            ("ul", [
                "Виправлено дублювання номера заявки при одночасному збереженні двома користувачами.",
                "Project Hub: форма проєкту більше не показує порожній subgrid ризиків для нових проєктів.",
            ]),
            ("h2", "Відомі проблеми"),
            ("ul", [
                "Вкладення понад 5 MB у UAT можуть зберігатися до 30 секунд; виправлення заплановано в 1.4.3.",
            ]),
        ],
    },
    "contoso-release-notes-1.4.3": {
        "format": "docx", "version": "1.4.3", "date": "2026-04-21",
        "title": "Contoso Procurement — Release Notes 1.4.3",
        "blocks": [
            ("h1", "Contoso Procurement — Release Notes 1.4.3"),
            ("p", "Дата релізу: 21.04.2026. Solution: ContosoCore_1_4_3_managed. Реліз встановлюється поверх 1.4.2 без міграції даних."),
            ("h2", "Нові можливості"),
            ("ul", [
                "Model-driven app «Project Hub»: кнопка «Затвердити бюджет» на формі проєкту для ролі Project Manager.",
                "Нова security role «Procurement Auditor» з доступом лише на читання до cnt_request і cnt_invoice.",
            ]),
            ("h2", "Виправлення"),
            ("ul", [
                "Збереження заявок із вкладеннями понад 5 MB прискорено до 3–5 секунд (проблема з 1.4.2).",
                "Approval Flow v2 тепер використовує connection reference cnt_sharedoffice365 замість особистого підключення розробника.",
            ]),
            ("h2", "Відомі проблеми"),
            ("ul", [
                "Після оновлення connection reference cnt_sharedoffice365 потрібно вручну прив'язати до сервісного акаунта в кожному середовищі.",
            ]),
        ],
    },
    "contoso-release-notes-1.5.0": {
        "format": "docx", "version": "1.5.0", "date": "2026-06-09",
        "title": "Contoso Procurement — Release Notes 1.5.0",
        "blocks": [
            ("h1", "Contoso Procurement — Release Notes 1.5.0"),
            ("p", "Дата релізу: 09.06.2026. Мажорний реліз: інтеграція з LEO PPM і нова таблиця інвойсів. Solution: ContosoCore_1_5_0_managed."),
            ("h2", "Нові можливості"),
            ("ul", [
                "Нова таблиця cnt_invoice (інвойси) зі зв'язком на cnt_request; ключ — cnt_invoicenumber.",
                "Flow «LEO Task Sync»: щогодинна синхронізація задач з LEO PPM у таблицю cnt_projecttask.",
                "Plugin cnt_ApprovalValidation: відхилення погодження без коментаря блокується.",
                "PCF-контрол cnt.DateRangePicker для вибору періоду на формах проєкту.",
            ]),
            ("h2", "Зміни, що порушують сумісність"),
            ("ul", [
                "Поле cnt_request.cnt_amount_old видалено; звіти мають використовувати cnt_amount.",
                "Мінімальна версія pac CLI для деплою — 1.44.",
            ]),
            ("h2", "Відомі проблеми"),
            ("ul", [
                "Імпорт solution у TEST може завершитися помилкою missing dependency на cnt_invoice, якщо ContosoCore_Invoices не імпортовано першим.",
            ]),
        ],
    },
    "contoso-release-notes-1.5.1": {
        "format": "docx", "version": "1.5.1", "date": "2026-07-02",
        "title": "Contoso Procurement — Release Notes 1.5.1 (hotfix)",
        "blocks": [
            ("h1", "Contoso Procurement — Release Notes 1.5.1 (hotfix)"),
            ("p", "Дата релізу: 02.07.2026. Hotfix-реліз. Solution: ContosoCore_1_5_1_managed."),
            ("h2", "Виправлення"),
            ("ul", [
                "Plugin cnt_ApprovalValidation: усунено NullReferenceException при відхиленні погодження з порожнім коментарем (регресія 1.5.0).",
                "Flow «LEO Task Sync»: додано повтор з експоненційною паузою при помилці 429 Too Many Requests.",
                "Approval Flow v2: повторний запуск з run history більше не створює дубль інвойсу — запис оновлюється за cnt_invoicenumber.",
            ]),
            ("h2", "Відомі проблеми"),
            ("ul", [
                "Клонування погодженої заявки (кнопка Clone) зберігає статус Approved; виправлення заплановано в 1.5.2.",
            ]),
        ],
    },
    "contoso-release-notes-1.5.2": {
        "format": "docx", "version": "1.5.2", "date": "2026-08-25",
        "title": "Contoso Procurement — Release Notes 1.5.2",
        "blocks": [
            ("h1", "Contoso Procurement — Release Notes 1.5.2"),
            ("p", "Дата релізу: 25.08.2026. Solution: ContosoCore_1_5_2_managed."),
            ("h2", "Нові можливості"),
            ("ul", [
                "Approval Flow v2: нагадування погоджувачу, якщо заявка не погоджена протягом 3 робочих днів.",
                "Project Hub: subgrid ризиків завантажується за запитом (вкладка «Ризики»), що пришвидшує відкриття форми проєкту.",
            ]),
            ("h2", "Виправлення"),
            ("ul", [
                "Клон погодженої заявки тепер створюється в статусі Draft (проблема з 1.5.1).",
                "Роль Project Manager знову бачить кнопку «Затвердити бюджет» (регресія 1.4.3 на PROD).",
            ]),
            ("h2", "Відомі проблеми"),
            ("ul", [
                "Business rule «Set default currency» на cnt_request не спрацьовує у формі quick create; валюту треба обрати вручну. Виправлення заплановано в 1.5.3.",
            ]),
        ],
    },
    "contoso-regression-test-plan-1.5": {
        "format": "docx", "version": "1.5", "date": "2026-08-18",
        "title": "Contoso Procurement — Регресійний тест-план 1.5",
        "blocks": [
            ("h1", "Contoso Procurement — Регресійний тест-план 1.5"),
            ("p", "Тест-план застосовується перед кожним релізом гілки 1.5.x у середовищі UAT. Відповідальна — QA Lead. Критерій виходу: усі тест-кейси пріоритету High пройдено, відкритих дефектів Critical немає."),
            ("h2", "Тест-кейси"),
            ("table", [
                ["ID", "Компонент", "Сценарій", "Пріоритет"],
                ["TC-101", "canvas app «Заявки на закупівлю»", "Створення заявки з вкладенням 8 MB", "High"],
                ["TC-104", "cnt_request", "Заявка понад 50 000 грн без центру витрат не зберігається", "High"],
                ["TC-110", "Approval Flow v2", "Погодження заявки: лист погоджувачу з посиланням", "High"],
                ["TC-112", "Approval Flow v2", "Повторний запуск з run history не створює дубль інвойсу", "High"],
                ["TC-118", "canvas app «Заявки на закупівлю»", "Кнопка Reject активна для заявок понад 100 000 грн", "Medium"],
                ["TC-120", "cnt_ApprovalValidation", "Відхилення без коментаря показує повідомлення, а не помилку", "High"],
                ["TC-125", "LEO Task Sync", "Синхронізація 500 задач без помилки 429", "Medium"],
                ["TC-130", "Project Hub", "Кнопка «Затвердити бюджет» видима для ролі Project Manager", "High"],
                ["TC-134", "Project Hub", "Форма проєкту відкривається менш ніж за 5 секунд на PROD-подібних даних", "Medium"],
            ]),
            ("h2", "Порядок виконання"),
            ("ol", [
                "Розгорнути реліз у UAT через pipeline «Contoso-Release».",
                "Виконати тест-кейси High, потім Medium.",
                "Зафіксувати результати в Azure DevOps Test Plans.",
                "Передати звіт Release Manager для рішення go / no-go.",
            ]),
        ],
    },
    "contoso-install-guide-1.4": {
        "format": "pdf", "version": "1.4", "date": "2026-03-10",
        "title": "Contoso Procurement — Інструкція зі встановлення 1.4 (застаріла)",
        "blocks": [
            ("h1", "Contoso Procurement — Інструкція зі встановлення 1.4"),
            ("p", "Статус документа: застарілий з 09.06.2026. Для версій 1.5.x використовуйте інструкцію 1.5."),
            ("h2", "Передумови"),
            ("ul", [
                "pac CLI версії 1.32 або новішої.",
                "Роль System Administrator у цільовому середовищі.",
                "Особисте підключення Office 365 Outlook для Approval Flow v2.",
            ]),
            ("h2", "Порядок встановлення"),
            ("ol", [
                "Імпортувати ContosoCore_1_4_x_managed.zip командою pac solution import.",
                "Увімкнути Approval Flow v2 під обліковим записом адміністратора.",
                "Призначити ролі користувачам вручну.",
            ]),
            ("h2", "Перевірка після встановлення"),
            ("p", "Створити тестову заявку в canvas app «Заявки на закупівлю» і переконатися, що погоджувач отримав лист."),
        ],
    },
    "contoso-install-guide-1.5": {
        "format": "pdf", "version": "1.5", "date": "2026-06-09",
        "title": "Contoso Procurement — Інструкція зі встановлення 1.5",
        "blocks": [
            ("h1", "Contoso Procurement — Інструкція зі встановлення 1.5"),
            ("p", "Актуальна інструкція для версій 1.5.0 і новіших. Замінює інструкцію 1.4."),
            ("h2", "Передумови"),
            ("ul", [
                "pac CLI версії 1.44 або новішої (нижчі версії не підтримують пакування ContosoCore_Invoices).",
                "Роль System Administrator у цільовому середовищі.",
                "Сервісний акаунт svc-contoso-flows з ліцензією Power Automate Premium — особисті підключення заборонені.",
                "Доступ до API LEO PPM (ключ зберігається в environment variable cnt_LeoApiKey).",
            ]),
            ("h2", "Порядок встановлення"),
            ("ol", [
                "Імпортувати ContosoCore_Invoices_managed.zip (обов'язково першим, інакше — помилка missing dependency на cnt_invoice).",
                "Імпортувати ContosoCore_1_5_x_managed.zip командою pac solution import --activate-plugins.",
                "Прив'язати connection reference cnt_sharedoffice365 до сервісного акаунта svc-contoso-flows.",
                "Заповнити environment variables cnt_LeoApiKey і cnt_LeoBaseUrl.",
                "Увімкнути flows «Approval Flow v2» і «LEO Task Sync».",
            ]),
            ("h2", "Перевірка після встановлення"),
            ("ul", [
                "Створити тестову заявку і переконатися, що погоджувач отримав лист від svc-contoso-flows.",
                "Запустити «LEO Task Sync» вручну і перевірити появу записів у cnt_projecttask.",
            ]),
        ],
    },
    "contoso-support-runbook": {
        "format": "pdf", "version": "1.5", "date": "2026-09-01",
        "title": "Contoso Procurement — Runbook підтримки",
        "blocks": [
            ("h1", "Contoso Procurement — Runbook підтримки"),
            ("p", "Документ для першої лінії підтримки. Описує типові інциденти та дії. Актуальний для версій 1.5.x."),
            ("h2", "Approval Flow v2 не надсилає листи"),
            ("ol", [
                "Перевірити run history flow на помилки підключення.",
                "Переконатися, що connection reference cnt_sharedoffice365 прив'язано до svc-contoso-flows, а не до особистого акаунта.",
                "Якщо акаунт заблоковано — ескалювати до команди Power Platform (SLA 4 години).",
            ]),
            ("h2", "LEO Task Sync падає з помилкою 429"),
            ("ol", [
                "Переконатися, що встановлено версію 1.5.1 або новішу (з повтором при 429).",
                "Перевірити ліміт API у LEO PPM: 1 000 запитів на годину на тенант.",
                "Якщо помилка повторюється більше 3 годин — створити інцидент Severity High.",
            ]),
            ("h2", "Класифікація серйозності інцидентів"),
            ("table", [
                ["Severity", "Критерій", "Час реакції"],
                ["Critical", "Зупинено погодження або оплату на PROD", "30 хвилин"],
                ["High", "Функція недоступна, є обхідний шлях", "4 години"],
                ["Medium", "Часткова деградація, не блокує роботу", "2 робочі дні"],
                ["Low", "Косметичні проблеми", "Наступний реліз"],
            ]),
        ],
    },
}


def write_docx(blocks: list, path: Path) -> None:
    doc = Document()
    for kind, content in blocks:
        if kind in ("h1", "h2", "h3"):
            doc.add_heading(content, level=int(kind[1]))
        elif kind == "p":
            doc.add_paragraph(content)
        elif kind in ("ul", "ol"):
            style = "List Bullet" if kind == "ul" else "List Number"
            for item in content:
                doc.add_paragraph(item, style=style)
        elif kind == "table":
            table = doc.add_table(rows=len(content), cols=len(content[0]))
            table.style = "Table Grid"
            for r, row in enumerate(content):
                for c, value in enumerate(row):
                    table.cell(r, c).text = value
    doc.save(path)


def write_pdf(blocks: list, title: str, path: Path) -> None:
    parts = [f"<!doctype html><html lang='uk'><head><meta charset='utf-8'><title>{html.escape(title)}</title>",
             "<style>body{font-family:Arial,sans-serif;font-size:11pt;margin:20mm}h1{font-size:18pt}h2{font-size:14pt;margin-top:18px}"
             "table{border-collapse:collapse}td,th{border:1px solid #999;padding:4px 8px}</style></head><body>"]
    for kind, content in blocks:
        if kind in ("h1", "h2", "h3", "p"):
            parts.append(f"<{kind}>{html.escape(content)}</{kind}>")
        elif kind in ("ul", "ol"):
            parts.append(f"<{kind}>" + "".join(f"<li>{html.escape(i)}</li>" for i in content) + f"</{kind}>")
        elif kind == "table":
            head = "".join(f"<th>{html.escape(c)}</th>" for c in content[0])
            rows = "".join("<tr>" + "".join(f"<td>{html.escape(c)}</td>" for c in row) + "</tr>" for row in content[1:])
            parts.append(f"<table><tr>{head}</tr>{rows}</table>")
    parts.append("</body></html>")
    tmp = path.with_suffix(".tmp.html")
    tmp.write_text("".join(parts), encoding="utf-8")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={path}", tmp.resolve().as_uri()], check=True, capture_output=True)
    tmp.unlink()


def main():
    synthetic = []
    for doc_id, spec in DOCS.items():
        fmt = spec["format"]
        path = RAW / fmt / f"{doc_id}.{fmt}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "docx":
            write_docx(spec["blocks"], path)
        else:
            write_pdf(spec["blocks"], spec["title"], path)
        synthetic.append({
            "doc_id": doc_id, "title": spec["title"], "format": fmt, "path": path.relative_to(ROOT).as_posix(),
            "source": "synthetic", "url": None, "product": "Contoso Procurement",
            "date": spec["date"], "version": spec["version"], "license": "synthetic (this repo)",
        })
        print(f"{fmt:5} {doc_id}")
    existing = json.loads(SOURCES.read_text(encoding="utf-8")) if SOURCES.exists() else []
    public = [d for d in existing if d["source"] != "synthetic"]
    SOURCES.write_text(json.dumps(public + synthetic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nСинтетичних документів: {len(synthetic)}; усього в sources.json: {len(public) + len(synthetic)}")


if __name__ == "__main__":
    main()
