"""Завантаження конфігу (config/models.yaml) і змінних оточення (.env)."""

from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "models.yaml"


def load_config(path: Path = CONFIG_PATH) -> dict:
    load_dotenv(ROOT / ".env")
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)
