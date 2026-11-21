"""Набір задач агента з детермінованими перевірками (кейс 3).

Кожна задача: питання, (необов'язково) збої FAULTS, ліміти, рішення людини на підтвердження (approve)
і очікування `expect`. Перевірки — лише детерміновані: які інструменти викликано, що є / чого немає
у відповіді, процитовані документи, причина зупинки, кількість дій з побічним ефектом і тікетів, помилки в trace.

python main.py agent-eval [--only a01,a14] [--runs 3] → evals/results/agent/
"""

import json
import re
import statistics
import tempfile
from datetime import datetime
from pathlib import Path

from src.agent.factory import build_agent, load_agent_config
from src.config import ROOT
from src.tracker.service import TrackerService


def has(text: str, pattern: str) -> bool:
    """`a|b` — будь-яка з альтернатив, без урахування регістру."""
    low = text.lower()
    return any(alt.strip().lower() in low for alt in pattern.split("|"))


def check(task: dict, res, tickets: int) -> list[str]:
    """→ список проваленої перевірки (порожній — задачу пройдено)."""
    e, fails = task["expect"], []
    called = [c["name"] for c in res.tool_calls]
    for need in e.get("tools_required", []):
        if not any(alt in called for alt in need.split("|")):
            fails.append(f"не викликано {need}")
    for tool in e.get("tools_forbidden", []):
        if tool in called:
            fails.append(f"зайвий виклик {tool}")
    for pat in e.get("answer_all", []):
        if not has(res.answer, pat):
            fails.append(f"у відповіді немає «{pat}»")
    for pat in e.get("answer_none", []):
        if has(res.answer, pat):
            fails.append(f"у відповіді є заборонене «{pat}»")
    if "cites_doc" in e:
        cited = {s["doc_id"] for s in res.sources.values()}
        if not cited & set(e["cites_doc"]):
            fails.append(f"не процитовано жодного з {e['cites_doc']} (процитовано: {sorted(cited) or '—'})")
    if "stop_reason" in e and res.stop_reason not in e["stop_reason"]:
        fails.append(f"stop_reason {res.stop_reason}, очікувалось {e['stop_reason']}")
    if "max_steps" in e and res.steps > e["max_steps"]:
        fails.append(f"кроків {res.steps} > {e['max_steps']}")
    if "side_effects" in e and len(res.side_effects) != e["side_effects"]:
        fails.append(f"дій з побічним ефектом {len(res.side_effects)}, очікувалось {e['side_effects']}")
    if "tickets" in e and tickets != e["tickets"]:
        fails.append(f"тікетів у трекері {tickets}, очікувалось {e['tickets']}")
    if len(res.confirmations) < e.get("confirmations_min", 0):
        fails.append("не запитано підтвердження людини")
    trace_text = json.dumps(res.trace, ensure_ascii=False)
    for mark in e.get("trace_has", []):
        if mark not in trace_text:
            fails.append(f"у trace немає {mark}")
    return fails


def tools_ok(task: dict, res) -> bool:
    e = task["expect"]
    called = [c["name"] for c in res.tool_calls]
    return (all(any(a in called for a in need.split("|")) for need in e.get("tools_required", []))
            and not any(t in called for t in e.get("tools_forbidden", [])))


def run_task(task: dict) -> dict:
    approve = task.get("approve")
    asked: list[dict] = []

    def confirm(tool: str, args: dict) -> bool:
        asked.append({"tool": tool, "args": args})
        return approve is True   # None — підтвердження в задачі не очікувалось → відмова

    with tempfile.TemporaryDirectory() as tmp:
        tracker = TrackerService(team=load_agent_config()["agent"]["team"], tickets_path=Path(tmp) / "tickets.json")
        agent = build_agent(confirm=confirm, faults=task.get("faults"), limits=task.get("limits"), tracker=tracker)
        res = agent.run(task["question"])
        tickets = len(tracker.tickets())
    fails = check(task, res, tickets)
    unauthorized = sum(1 for _ in res.side_effects) if approve is not True else 0
    return {"id": task["id"], "group": task["group"], "fault_case": task.get("fault_case"), "faults": task.get("faults"),
            "passed": not fails, "fails": fails, "tools_ok": tools_ok(task, res), "unauthorized_actions": unauthorized,
            "tickets": tickets, "result": res.to_dict()}


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    lat = sorted(r["result"]["latency_ms"] for r in rows)
    cost = [r["result"]["cost_usd"] for r in rows]
    return {
        "tasks": n,
        "pass_rate": sum(r["passed"] for r in rows) / n,
        "tools_ok": sum(r["tools_ok"] for r in rows) / n,
        "unauthorized_actions": sum(r["unauthorized_actions"] for r in rows),
        "steps_mean": statistics.mean(r["result"]["steps"] for r in rows),
        "steps_max": max(r["result"]["steps"] for r in rows),
        "cost_per_task_usd": statistics.mean(cost),
        "cost_per_1000_usd": statistics.mean(cost) * 1000,
        "latency_p50_ms": lat[n // 2],
        "latency_p95_ms": lat[min(n - 1, int(round(0.95 * (n - 1))))],
        "failed_ids": [r["id"] for r in rows if not r["passed"]],
    }


def report(runs: list[list[dict]], meta: dict) -> str:
    sums = [summarize(r) for r in runs]
    lines = ["# Evals агента (кейс 3)", "",
             f"Модель `{meta['model']}` · промпт `{meta['prompt']}` (sha {meta['prompt_sha']}) · інструменти `{meta['tools']}`"
             f" · трекер: `{meta.get('tracker_backend', 'local')}` · задач: {sums[0]['tasks']} · прогонів: {len(runs)} · {datetime.now():%Y-%m-%d %H:%M}", "",
             "| Метрика | " + " | ".join(f"прогін {i + 1}" for i in range(len(runs))) + " |",
             "|---|" + "---|" * len(runs)]
    rowdefs = [("пройдено задач", lambda s: f"{s['pass_rate']:.0%}"),
               ("викликано потрібні інструменти", lambda s: f"{s['tools_ok']:.0%}"),
               ("дії без дозволу", lambda s: str(s["unauthorized_actions"])),
               ("кроків на задачу (сер. / макс.)", lambda s: f"{s['steps_mean']:.1f} / {s['steps_max']}"),
               ("ціна на задачу", lambda s: f"${s['cost_per_task_usd']:.4f}"),
               ("ціна на 1000 запитів", lambda s: f"${s['cost_per_1000_usd']:.2f}"),
               ("latency p50 / p95", lambda s: f"{s['latency_p50_ms']} / {s['latency_p95_ms']} мс"),
               ("провалені", lambda s: ", ".join(s["failed_ids"]) or "—")]
    lines += [f"| {name} | " + " | ".join(fn(s) for s in sums) + " |" for name, fn in rowdefs]

    last = runs[-1]
    lines += ["", f"## Задачі (прогін {len(runs)})", "",
              "| id | група | результат | інструменти | кроків | stop_reason | $ | що не так |", "|---|---|---|---|---|---|---|---|"]
    for r in last:
        res = r["result"]
        tools = ", ".join(f"{c['name']}→{c['outcome']}" for c in res["tool_calls"]) or "—"
        lines.append(f"| {r['id']} | {r['group']} | {'✅' if r['passed'] else '❌'} | {tools} | {res['steps']} | "
                     f"{res['stop_reason']} | {res['cost_usd']:.4f} | {'; '.join(r['fails']) or ''} |")

    lines += ["", "## Задачі на збої", "", "| id | збій | FAULTS | що сталося | результат |", "|---|---|---|---|---|"]
    for r in last:
        if not r["fault_case"]:
            continue
        res = r["result"]
        errs = [e.get("error") or ("ok" if e.get("ok") else "") for e in res["trace"] if e["type"] == "tool"]
        lines.append(f"| {r['id']} | {r['fault_case']} | `{r['faults'] or '—'}` | {' → '.join(x for x in errs if x)} | "
                     f"{'✅' if r['passed'] else '❌ ' + '; '.join(r['fails'])} |")
    return "\n".join(lines) + "\n"


def run_agent_eval(only: list[str] | None = None, runs: int = 1) -> int:
    cfg = load_agent_config()
    tasks = [json.loads(l) for l in (ROOT / cfg["evals"]["tasks"]).read_text(encoding="utf-8").splitlines() if l.strip()]
    if only:
        tasks = [t for t in tasks if t["id"] in only]
    out_dir = ROOT / cfg["evals"]["results_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    all_runs = []
    for n in range(1, runs + 1):
        rows = []
        for task in tasks:
            row = run_task(task)
            rows.append(row)
            res = row["result"]
            print(f"[{n}] {task['id']} {'✅' if row['passed'] else '❌'} {res['stop_reason']} · кроків {res['steps']} · "
                  f"{', '.join(c['name'] for c in res['tool_calls']) or 'без інструментів'}"
                  + (f" · {'; '.join(row['fails'])}" if row["fails"] else ""))
        all_runs.append(rows)
        suffix = ("_only" if only else "") + ("" if runs == 1 else f"_run{n}")
        with (out_dir / f"agent_results{suffix}.jsonl").open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    meta = all_runs[0][0]["result"]["meta"]
    md = report(all_runs, meta)
    metrics_path = out_dir / ("agent_metrics_only.md" if only else "agent_metrics.md")  # часткові прогони не затирають звіт
    metrics_path.write_text(md, encoding="utf-8")
    s = summarize(all_runs[-1])
    print(f"\nпройдено {s['pass_rate']:.0%} · інструменти {s['tools_ok']:.0%} · дії без дозволу {s['unauthorized_actions']}"
          f" · ${s['cost_per_1000_usd']:.2f} / 1000 запитів → {metrics_path.relative_to(ROOT)}")
    from src.agent.factory import close_shared
    close_shared()
    return 0
