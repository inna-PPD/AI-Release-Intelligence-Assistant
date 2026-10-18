"""Провайдерські моделі через OpenRouter (OpenAI-сумісний API) зі structured output."""

import os
import time

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError
from openai.lib._pydantic import to_strict_json_schema
from pydantic import BaseModel

from .base import LLMError, LLMResult, SamplingParams

BASE_URL = "https://openrouter.ai/api/v1"
RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError)


class OpenRouterClient:
    def __init__(self, model: str, timeout_s: float = 60, retries: int = 2):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise LLMError("OPENROUTER_API_KEY не задано: скопіюйте .env.example у .env і впишіть ключ")
        self.name = model
        self.retries = retries
        # власні повтори нижче, тому вбудовані в SDK вимикаємо
        self._client = OpenAI(base_url=BASE_URL, api_key=api_key, timeout=timeout_s, max_retries=0)

    def generate_structured(
        self, messages: list[dict], schema: type[BaseModel], params: SamplingParams
    ) -> LLMResult:
        response_format = {
            "type": "json_schema",
            "json_schema": {"name": schema.__name__, "strict": True, "schema": to_strict_json_schema(schema)},
        }
        for attempt in range(self.retries + 1):
            start = time.perf_counter()
            try:
                r = self._client.chat.completions.create(
                    model=self.name,
                    messages=messages,
                    response_format=response_format,
                    temperature=params.temperature,
                    top_p=params.top_p,
                    max_tokens=params.max_tokens,
                )
            except RETRYABLE as e:
                error = e
            except APIStatusError as e:
                if e.status_code < 500:
                    raise LLMError(f"{e.status_code}: {e.message}") from e
                error = e
            else:
                return LLMResult(
                    raw_text=r.choices[0].message.content or "",
                    tokens_in=r.usage.prompt_tokens if r.usage else 0,
                    tokens_out=r.usage.completion_tokens if r.usage else 0,
                    latency_ms=int((time.perf_counter() - start) * 1000),
                    model=self.name,
                )
            if attempt < self.retries:
                time.sleep(2 ** attempt)  # 1 c, 2 c, ...
        raise LLMError(f"{type(error).__name__}: {error}") from error
