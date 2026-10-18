"""Спільний інтерфейс для всіх LLM: провайдерських і локальних.

Пайплайн працює лише через LLMClient, тому модель змінюється конфігом, а не кодом.
"""

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel


@dataclass
class SamplingParams:
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 1024


@dataclass
class LLMResult:
    raw_text: str       # що повернула модель — валідуємо вже в пайплайні
    tokens_in: int
    tokens_out: int
    latency_ms: int
    model: str


class LLMError(Exception):
    """Модель недоступна після всіх повторів (мережа, timeout, 5xx)."""


class LLMClient(Protocol):
    name: str  # ідентифікатор моделі, напр. "openai/gpt-4o-mini"

    def generate_structured(
        self,
        messages: list[dict],
        schema: type[BaseModel],
        params: SamplingParams,
    ) -> LLMResult: ...
