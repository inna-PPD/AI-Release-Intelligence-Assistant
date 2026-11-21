"""Збирання агента з конфігів: config/agent.yaml + config/models.yaml + config/rag.yaml."""

from dataclasses import fields

import yaml

from src.agent.loop import Agent, Confirm, Limits
from src.agent.tools import ToolContext, load_tools
from src.config import ROOT, load_config
from src.extraction.prompts import load_prompt
from src.llm import SamplingParams, make_client
from src.tracker.service import TrackerService

_RETRIEVER = None  # моделі embeddings і reranker вантажаться один раз на процес


def load_agent_config() -> dict:
    return yaml.safe_load((ROOT / "config" / "agent.yaml").read_text(encoding="utf-8"))


def shared_retriever():
    global _RETRIEVER
    if _RETRIEVER is None:
        from src.rag.search import Retriever
        _RETRIEVER = Retriever(yaml.safe_load((ROOT / "config" / "rag.yaml").read_text(encoding="utf-8")))
        _RETRIEVER.search("warm up", mode="hybrid_rerank", k=1)  # перший виклик повільний — не в таймауті інструмента
    return _RETRIEVER


def close_shared() -> None:
    global _RETRIEVER
    if _RETRIEVER is not None:
        _RETRIEVER.close()
        _RETRIEVER = None


def build_agent(confirm: Confirm | None = None, faults: str | None = None, limits: dict | None = None,
                tracker: TrackerService | None = None, llm=None) -> Agent:
    cfg = load_agent_config()
    a = cfg["agent"]
    models = load_config()
    model_cfg = models["models"][a["model"]]
    rag = yaml.safe_load((ROOT / "config" / "rag.yaml").read_text(encoding="utf-8"))
    tools, tools_id = load_tools(a["tools"])
    ctx = ToolContext(tracker=tracker or TrackerService(team=a["team"]), retriever=shared_retriever(),
                      min_rerank_score=rag["answer"]["min_rerank_score"], top_k=rag["search"]["top_k"])
    known = {f.name for f in fields(Limits)}
    lim = Limits(**{k: v for k, v in {**cfg["limits"], **(limits or {})}.items() if k in known})
    prompt = load_prompt(a["system_prompt"])
    return Agent(llm or make_client(model_cfg, models), tools, ctx, prompt, lim,
                 SamplingParams(**a["sampling"], max_tokens=a["max_tokens"]), model_cfg["price_per_1m_tokens"],
                 confirm=confirm, faults=faults,
                 meta={"model": model_cfg["id"], "prompt": prompt.id, "prompt_sha": prompt.sha, "tools": tools_id})
