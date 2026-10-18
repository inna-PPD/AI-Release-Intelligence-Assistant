"""Схема DefectReport: що витягуємо з сирого баг-репорту про рішення на Power Platform.

Правило для всіх полів: якщо інформації в тексті немає — null (або порожній список),
модель не повинна вгадувати.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComponentType(str, Enum):
    TABLE = "table"                        # таблиця Dataverse (cnt_request, account...)
    CLOUD_FLOW = "cloud_flow"              # Power Automate
    CANVAS_APP = "canvas_app"
    MODEL_DRIVEN_APP = "model_driven_app"
    PLUGIN = "plugin"
    PCF = "pcf"                            # PCF-контрол
    BUSINESS_RULE = "business_rule"
    SECURITY_ROLE = "security_role"
    SOLUTION = "solution"                  # імпорт/експорт/пакування solution
    ALM_TOOLING = "alm_tooling"            # pac CLI, pipelines, build tools
    LEO_PPM = "leo_ppm"                    # LEO PPM / Gantt
    OTHER = "other"


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    UAT = "uat"
    PROD = "prod"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Component(BaseModel):
    """Вкладений об'єкт: один зачеплений компонент рішення."""

    model_config = ConfigDict(extra="forbid")

    type: ComponentType = Field(description="Тип компонента Power Platform")
    name: Optional[str] = Field(description="Назва як у тексті, напр. 'cnt_invoice' або 'Approval Flow v2'; null, якщо не названо")


class DefectReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(description="Короткий заголовок проблеми (до 100 символів), мовою оригіналу")
    is_defect: bool = Field(description="false, якщо це побажання, питання або відомий issue, а не помилка")
    components: list[Component] = Field(description="Усі зачеплені компоненти; порожній список, якщо не зрозуміло")
    environments: list[Environment] = Field(description="Середовища, де відтворюється; порожній список, якщо не вказано")
    severity: Optional[Severity] = Field(description="Серйозність, якщо вказана явно або однозначно випливає з тексту ('блокує деплой', 'критично'); інакше null")
    release_version: Optional[str] = Field(description="Версія релізу/рішення, напр. '1.5.0'; null, якщо не вказано")
    steps_to_reproduce: list[str] = Field(description="Кроки відтворення, по одному на елемент; порожній список, якщо їх немає")
    expected_result: Optional[str] = Field(description="Очікувана поведінка; null, якщо не описано")
    actual_result: Optional[str] = Field(description="Фактична поведінка або текст помилки; null, якщо не описано")
    is_regression: Optional[bool] = Field(description="true, якщо сказано що раніше працювало; false, якщо явно нове; інакше null")
