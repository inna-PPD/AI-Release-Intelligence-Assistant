"""Трекер релізів і дефектів Contoso: логіка доступу до даних.

Цим модулем користуються і локальні інструменти агента, і MCP-сервер (крок 2), тому обмеження доступу
стоять тут, а не в описах для моделі:
- читання лише з data/tracker (фіксовані файли, жодних довільних шляхів чи запитів);
- дефекти інших команд закриті (AccessDenied);
- запис — лише створення тікета, з ключем ідемпотентності.
"""

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from src.config import ROOT

DATA_DIR = ROOT / "data" / "tracker"
TICKETS_PATH = ROOT / "runtime" / "tickets.json"
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
DEFECT_ID_RE = re.compile(r"^DEF-\d{1,5}$")


class TrackerError(Exception):
    code = "ERROR"


class NotFound(TrackerError):
    code = "NOT_FOUND"


class AccessDenied(TrackerError):
    code = "ACCESS_DENIED"


def idempotency_key(title: str, version: str) -> str:
    """Той самий заголовок + версія → той самий ключ, незалежно від регістру й пробілів."""
    norm = " ".join(title.lower().split()) + "|" + version.strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


class TrackerService:
    def __init__(self, team: str = "procurement", data_dir: Path = DATA_DIR, tickets_path: Path = TICKETS_PATH):
        self.team = team
        self.releases = json.loads((data_dir / "releases.json").read_text(encoding="utf-8"))
        self.defects = json.loads((data_dir / "defects.json").read_text(encoding="utf-8"))
        self.tickets_path = tickets_path
        self._lock = threading.Lock()

    # --- читання ---
    def get_release(self, version: str) -> dict:
        if not VERSION_RE.match(version):
            raise ValueError(f"версія має бути у форматі X.Y.Z, отримано {version!r}")
        for r in self.releases:
            if r["version"] == version:
                return {k: r[k] for k in ("version", "status", "release_date", "solution", "deployed_to")}
        raise NotFound(f"реліз {version} у трекері не знайдено; відомі версії: {', '.join(r['version'] for r in self.releases)}")

    def list_defects(self, version: str | None = None, severity: str | None = None, status: str | None = None) -> dict:
        rows = [d for d in self.defects if d["team"] == self.team
                and (version is None or d["version"] == version)
                and (severity is None or d["severity"] == severity)
                and (status is None or d["status"] == status)]
        return {"team": self.team, "count": len(rows), "defects": [self._public(d) for d in rows]}

    def get_defect(self, defect_id: str) -> dict:
        if not DEFECT_ID_RE.match(defect_id):
            raise ValueError(f"id дефекту має бути у форматі DEF-123, отримано {defect_id!r}")
        for d in self.defects:
            if d["id"] == defect_id:
                if d["team"] != self.team:
                    raise AccessDenied(f"{defect_id} належить команді {d['team']}; у команди {self.team} немає доступу")
                return self._public(d)
        raise NotFound(f"дефект {defect_id} не знайдено")

    @staticmethod
    def _public(d: dict) -> dict:
        return {k: d[k] for k in ("id", "title", "version", "severity", "status", "component", "environment", "fixed_in")}

    # --- запис (побічний ефект) ---
    def create_ticket(self, title: str, version: str, severity: str, description: str) -> dict:
        key = idempotency_key(title, version)
        with self._lock:
            tickets = self._load_tickets()
            for t in tickets:
                if t["idempotency_key"] == key:
                    return {"ticket_id": t["ticket_id"], "status": "already_exists", "idempotency_key": key}
            ticket = {"ticket_id": f"TCK-{len(tickets) + 1:04d}", "title": title, "version": version,
                      "severity": severity, "description": description, "team": self.team,
                      "idempotency_key": key, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            tickets.append(ticket)
            self.tickets_path.parent.mkdir(parents=True, exist_ok=True)
            self.tickets_path.write_text(json.dumps(tickets, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ticket_id": ticket["ticket_id"], "status": "created", "idempotency_key": key}

    def _load_tickets(self) -> list[dict]:
        if not self.tickets_path.exists():
            return []
        return json.loads(self.tickets_path.read_text(encoding="utf-8"))

    def tickets(self) -> list[dict]:
        return self._load_tickets()
