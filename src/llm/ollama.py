"""Локальні моделі через Ollama: JSON-схема передається в параметр format."""

import time

import httpx
from pydantic import BaseModel

from .base import LLMError, LLMResult, SamplingParams


class OllamaClient:
    def __init__(self, model: str, base_url: str = "http://localhost:11434", timeout_s: float = 60, retries: int = 2):
        self.name = model
        self.retries = retries
        self._http = httpx.Client(base_url=base_url, timeout=timeout_s)

    def check(self) -> None:
        """Перевіряє, що Ollama запущена і модель завантажена (ollama pull <model>)."""
        try:
            tags = self._http.get("/api/tags").json()
        except httpx.HTTPError as e:
            raise LLMError(f"Ollama недоступна ({e}). Запустіть Ollama.") from e
        names = {m["name"] for m in tags.get("models", [])}
        if self.name not in names and f"{self.name}:latest" not in names:
            raise LLMError(f"Модель {self.name} не завантажена: виконайте `ollama pull {self.name}`")
        # прогрів: завантажує модель у пам'ять, щоб час завантаження не потрапив у latency першого документа
        self._http.post("/api/generate", json={"model": self.name, "keep_alive": "30m"})

    def generate_structured(
        self, messages: list[dict], schema: type[BaseModel], params: SamplingParams
    ) -> LLMResult:
        payload = {
            "model": self.name,
            "messages": messages,
            "format": schema.model_json_schema(),
            "stream": False,
            "options": {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "num_predict": params.max_tokens,
            },
        }
        for attempt in range(self.retries + 1):
            start = time.perf_counter()
            try:
                r = self._http.post("/api/chat", json=payload)
                r.raise_for_status()
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                error = e
            else:
                data = r.json()
                return LLMResult(
                    raw_text=data["message"]["content"],
                    tokens_in=data.get("prompt_eval_count", 0),
                    tokens_out=data.get("eval_count", 0),
                    latency_ms=int((time.perf_counter() - start) * 1000),
                    model=self.name,
                )
            if attempt < self.retries:
                time.sleep(2 ** attempt)
        raise LLMError(f"{type(error).__name__}: {error}") from error
