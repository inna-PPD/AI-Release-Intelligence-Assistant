from .base import LLMClient, LLMError, LLMResult, SamplingParams
from .ollama import OllamaClient
from .openrouter import OpenRouterClient


def make_client(model_cfg: dict, config: dict) -> LLMClient:
    """Створює клієнта за записом з config/models.yaml → models.<key>."""
    ex = config["extraction"]
    if model_cfg["client"] == "openrouter":
        return OpenRouterClient(model_cfg["id"], timeout_s=ex["timeout_s"], retries=ex["retries"])
    if model_cfg["client"] == "ollama":
        client = OllamaClient(model_cfg["id"], config["ollama"]["base_url"], ex["timeout_s"], ex["retries"],
                              structured=model_cfg.get("structured", True))
        client.check()
        return client
    raise ValueError(f"Невідомий client: {model_cfg['client']}")


__all__ = ["LLMClient", "LLMError", "LLMResult", "SamplingParams", "make_client"]
