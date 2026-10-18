"""Пайплайн extraction: документ → промпт → модель → валідація → (repair) → запис у results/.

Кожен запис містить модель, версію промпту, параметри семплінгу, токени, latency і вартість,
щоб будь-яку цифру зі звіту можна було відтворити.
"""

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from src.extraction.prompts import Prompt
from src.llm import LLMClient, LLMError, SamplingParams

REPAIR_MESSAGE = (
    "Твоя відповідь не пройшла валідацію за схемою:\n{errors}\n"
    "Поверни виправлений JSON строго за схемою, без пояснень."
)


def load_documents(paths: list[Path]) -> list[dict]:
    docs = []
    for path in paths:
        with path.open(encoding="utf-8") as f:
            docs.extend(json.loads(line) for line in f if line.strip())
    return docs


def cost_usd(tokens_in: int, tokens_out: int, price_per_1m: dict) -> float | None:
    if price_per_1m.get("input") is None or price_per_1m.get("output") is None:
        return None
    return (tokens_in * price_per_1m["input"] + tokens_out * price_per_1m["output"]) / 1_000_000


def extract_one(
    client: LLMClient,
    prompt: Prompt,
    doc: dict,
    schema: type[BaseModel],
    params: SamplingParams,
    repair_attempts: int,
) -> dict:
    """Повертає частину запису: status, attempts, output, error, токени, latency."""
    messages = prompt.messages(doc["text"])
    totals = {"tokens_in": 0, "tokens_out": 0, "latency_ms": 0}
    error = None

    for attempt in range(1, repair_attempts + 2):
        try:
            result = client.generate_structured(messages, schema, params)
        except LLMError as e:
            return {**totals, "status": "failed", "attempts": attempt, "output": None, "error": f"llm: {e}"}
        totals["tokens_in"] += result.tokens_in
        totals["tokens_out"] += result.tokens_out
        totals["latency_ms"] += result.latency_ms
        try:
            output = schema.model_validate_json(result.raw_text)
        except ValidationError as e:
            error = e
            messages = messages + [
                {"role": "assistant", "content": result.raw_text},
                {"role": "user", "content": REPAIR_MESSAGE.format(errors=e)},
            ]
            continue
        status = "ok" if attempt == 1 else "repaired"
        # для repaired зберігаємо, що саме було не так у першій відповіді — матеріал для розбору помилок
        note = None if error is None else f"repaired after validation: {describe(error)}"
        return {**totals, "status": status, "attempts": attempt, "output": output.model_dump(mode="json"), "error": note}

    return {**totals, "status": "failed", "attempts": repair_attempts + 1, "output": None,
            "error": f"validation: {describe(error)}"}


def describe(error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(p) for p in first["loc"]) or "<root>"
    return f"{error.error_count()} errors, first: {location} — {first['msg']}"


def run_extraction(
    client: LLMClient,
    prompt: Prompt,
    docs: list[dict],
    schema: type[BaseModel],
    sampling_name: str,
    params: SamplingParams,
    repair_attempts: int,
    price_per_1m: dict,
    results_dir: Path,
) -> tuple[Path, list[dict]]:
    model_slug = client.name.replace("/", "_").replace(":", "-")
    run_id = f"{datetime.now():%Y-%m-%dT%H-%M}_{model_slug}_{prompt.id.replace('/', '-')}_{sampling_name}"
    out_path = results_dir / f"{run_id}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = []
    with out_path.open("w", encoding="utf-8") as f:
        for i, doc in enumerate(docs, 1):
            part = extract_one(client, prompt, doc, schema, params, repair_attempts)
            record = {
                "run_id": run_id,
                "doc_id": doc["id"],
                "model": client.name,
                "prompt_version": prompt.id,
                "prompt_sha": prompt.sha,
                "sampling": {"name": sampling_name, "temperature": params.temperature, "top_p": params.top_p},
                "status": part["status"],
                "attempts": part["attempts"],
                "latency_ms": part["latency_ms"],
                "tokens_in": part["tokens_in"],
                "tokens_out": part["tokens_out"],
                "cost_usd": cost_usd(part["tokens_in"], part["tokens_out"], price_per_1m),
                "output": part["output"],
                "error": part["error"],
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
            records.append(record)
            print(f"  [{i}/{len(docs)}] {doc['id']}: {record['status']} ({record['latency_ms']} ms)")
    return out_path, records
