"""Інструменти агента: схеми аргументів і відповідей (Pydantic) + реалізація.

Тексти для моделі (коли викликати, коли ні) — у prompts/agent_tools/<версія>.yaml; тут лише типи,
обмеження і код. Кожен інструмент робить одну річ.

Позначки, які перевіряє цикл агента (у коді, не в промпті):
- safe_to_retry: читання без побічних ефектів — можна повторювати при timeout / 429 / 503;
- side_effect: змінює щось поза розмовою → виконується лише після підтвердження людиною;
- grounded_args: значення має бути в словах користувача (агент не вгадує версію для тікета).
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.config import ROOT
from src.tracker.service import TrackerService

TOOLS_DIR = ROOT / "prompts" / "agent_tools"
Severity = Literal["critical", "high", "medium", "low"]
VERSION = r"^\d+\.\d+\.\d+$"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- аргументи ---
class SearchDocsArgs(Strict):
    query: str = Field(min_length=3, max_length=300)
    product: Literal["Contoso Procurement", "CoE Starter Kit", "pac CLI", "ALM", "Power Platform Pipelines",
                     "Power Platform Build Tools"] | None = None
    version: str | None = Field(default=None, pattern=r"^\d+\.\d+(\.\d+)?$")


class GetReleaseArgs(Strict):
    version: str = Field(pattern=VERSION)


class ListDefectsArgs(Strict):
    version: str | None = Field(default=None, pattern=VERSION)
    severity: Severity | None = None
    status: Literal["open", "resolved"] | None = None


class GetDefectArgs(Strict):
    defect_id: str = Field(pattern=r"^DEF-\d{1,5}$")


class CreateTicketArgs(Strict):
    title: str = Field(min_length=5, max_length=120)
    version: str = Field(pattern=VERSION)
    severity: Severity
    description: str = Field(min_length=5, max_length=2000)


# --- відповіді (перевіряються, щоб зміна формату API не дійшла до моделі тихим None) ---
class SearchResult(Strict):
    source_id: str
    doc_id: str
    title: str
    section: str
    version: str | None
    date: str | None
    text: str


class SearchDocsOut(Strict):
    results: list[SearchResult]


class ReleaseOut(Strict):
    version: str
    status: Literal["released", "in_testing", "planned"]
    release_date: str | None
    solution: str | None
    deployed_to: list[str]


class DefectOut(Strict):
    id: str
    title: str
    version: str
    severity: Severity
    status: Literal["open", "resolved"]
    component: str
    environment: str
    fixed_in: str | None


class DefectListOut(Strict):
    team: str
    count: int
    defects: list[DefectOut]


class TicketOut(Strict):
    ticket_id: str
    status: Literal["created", "already_exists"]
    idempotency_key: str


# --- контекст виконання ---
@dataclass
class SourceRegistry:
    """Наскрізна нумерація джерел S1, S2… за весь запит, щоб цитати з різних пошуків не плутались."""
    by_chunk: dict[str, str] = field(default_factory=dict)
    sources: dict[str, dict] = field(default_factory=dict)

    def register(self, chunk: dict) -> str:
        cid = chunk["chunk_id"]
        if cid not in self.by_chunk:
            sid = f"S{len(self.by_chunk) + 1}"
            self.by_chunk[cid] = sid
            self.sources[sid] = {"doc_id": chunk["doc_id"], "title": chunk["title"], "section": chunk["section"],
                                 "version": chunk.get("version"), "date": chunk.get("date"), "url": chunk.get("url")}
        return self.by_chunk[cid]


@dataclass
class ToolContext:
    tracker: TrackerService
    retriever: Any = None             # src.rag.search.Retriever; None — пошук вимкнено (юніт-тести)
    min_rerank_score: float = -1.0
    top_k: int = 5
    registry: SourceRegistry = field(default_factory=SourceRegistry)


# --- реалізація ---
def search_docs(a: SearchDocsArgs, ctx: ToolContext) -> dict:
    filters = {k: v for k, v in (("product", a.product), ("version", a.version)) if v}
    hits = ctx.retriever.search(a.query, mode="hybrid_rerank", k=ctx.top_k, filters=filters or None)
    results = []
    for h in hits:
        if h.scores.get("rerank", 0) < ctx.min_rerank_score:
            continue  # той самий поріг «не знаю», що й у RAG кейсу 2
        c = h.chunk
        results.append({"source_id": ctx.registry.register(c), "doc_id": c["doc_id"], "title": c["title"],
                        "section": c["section"], "version": c.get("version"), "date": c.get("date"), "text": c["text"]})
    return {"results": results}


def get_release(a: GetReleaseArgs, ctx: ToolContext) -> dict:
    return ctx.tracker.get_release(a.version)


def list_defects(a: ListDefectsArgs, ctx: ToolContext) -> dict:
    return ctx.tracker.list_defects(a.version, a.severity, a.status)


def get_defect(a: GetDefectArgs, ctx: ToolContext) -> dict:
    return ctx.tracker.get_defect(a.defect_id)


def create_ticket(a: CreateTicketArgs, ctx: ToolContext) -> dict:
    return ctx.tracker.create_ticket(a.title, a.version, a.severity, a.description)


@dataclass
class ToolSpec:
    name: str
    args_model: type[BaseModel]
    output_model: type[BaseModel]
    fn: Callable[[BaseModel, ToolContext], dict]
    safe_to_retry: bool = True
    side_effect: bool = False
    grounded_args: tuple[str, ...] = ()
    description: str = ""
    arg_descriptions: dict[str, str] = field(default_factory=dict)

    def openai_schema(self) -> dict:
        schema = self.args_model.model_json_schema()
        schema.pop("title", None)
        for name, prop in schema.get("properties", {}).items():
            prop.pop("title", None)
            prop.pop("default", None)
            if name in self.arg_descriptions:
                prop["description"] = self.arg_descriptions[name]
        return {"type": "function", "function": {"name": self.name, "description": self.description, "parameters": schema}}


REGISTRY = [
    ToolSpec("search_docs", SearchDocsArgs, SearchDocsOut, search_docs),
    ToolSpec("get_release", GetReleaseArgs, ReleaseOut, get_release),
    ToolSpec("list_defects", ListDefectsArgs, DefectListOut, list_defects),
    ToolSpec("get_defect", GetDefectArgs, DefectOut, get_defect),
    # Повтор безпечний, бо трекер дедуплікує за ключем ідемпотентності (заголовок + версія): обрив зв'язку
    # після створення → повтор поверне already_exists, а не дубль. Без ключа тут було б safe_to_retry=False.
    ToolSpec("create_ticket", CreateTicketArgs, TicketOut, create_ticket,
             safe_to_retry=True, side_effect=True, grounded_args=("version",)),
]


def load_tools(version: str = "v1", names: list[str] | None = None) -> tuple[dict[str, ToolSpec], str]:
    """Специфікації з описами з prompts/agent_tools/<version>.yaml. → (інструменти за назвою, id версії описів)."""
    doc = yaml.safe_load((TOOLS_DIR / f"{version}.yaml").read_text(encoding="utf-8"))
    if doc["version"] != version:
        raise ValueError(f"agent_tools/{version}.yaml: version у файлі — {doc['version']}")
    specs = {}
    for spec in REGISTRY:
        if names is not None and spec.name not in names:
            continue
        text = doc["tools"][spec.name]
        missing = set(spec.args_model.model_fields) - set(text["args"])
        if missing:
            raise ValueError(f"agent_tools/{version}.yaml: {spec.name} без опису аргументів {sorted(missing)}")
        specs[spec.name] = ToolSpec(**{**spec.__dict__, "description": text["description"].strip(),
                                       "arg_descriptions": text["args"]})
    return specs, f"agent_tools/{version}"
