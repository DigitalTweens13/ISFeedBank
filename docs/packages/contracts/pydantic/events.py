"""Сгенерированные модели событий брокера.

Источники:
- packages/contracts/events/reviews.labeling.v1.json
- packages/contracts/events/cases.events.v1.json

Регенерация: python -m scripts.generate_contracts
"""
from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, conint, constr


# ─── reviews.labeling.v1 ────────────────────────────────────────────

class Source(StrEnum):
    banki_ru = 'banki_ru'
    sravni_ru = 'sravni_ru'
    app_store = 'app_store'
    google_play = 'google_play'
    file_import = 'file_import'
    api_batch = 'api_batch'


class ReviewsLabelingTaskV1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    review_id: UUID = Field(..., description='Идентификатор отзыва в базе данных.')
    text: constr(min_length=1, max_length=20000) = Field(
        ..., description='Обезличенный текст отзыва.'
    )
    source: Source = Field(..., description='Источник отзыва.')
    rating: conint(ge=1, le=5) = Field(..., description='Оценка автора от 1 до 5.')
    published_at: AwareDatetime = Field(..., description='Момент публикации отзыва.')
    batch_id: UUID | None = Field(
        None,
        description='Пакет, в составе которого пришёл отзыв. Не задан для отзывов, собранных по расписанию.',
    )


# ─── cases.events.v1 ────────────────────────────────────────────────

class EventType(StrEnum):
    case_created = 'case_created'
    case_escalated = 'case_escalated'
    case_closed = 'case_closed'


class Severity(StrEnum):
    critical = 'critical'
    high = 'high'
    medium = 'medium'
    low = 'low'


class CasesEventV1(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
    )
    event_type: EventType = Field(
        ...,
        description='Тип события. На текущем этапе Воркер разметки публикует только case_created.',
    )
    case_id: UUID = Field(..., description='Идентификатор обращения.')
    review_id: UUID = Field(
        ..., description='Идентификатор отзыва, из которого создано обращение.'
    )
    occurred_at: AwareDatetime = Field(..., description='Момент события.')
    severity: Severity | None = Field(
        None,
        description='Важность обращения. Используется политикой приоритета CriticalCasesFirst в брокере.',
    )
    direction: str | None = Field(
        None,
        description='Продуктовое направление: ипотека, карты, приложение, отделения.',
    )
