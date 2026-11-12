"""Модели данных компонента обработки событий обращений (L4, воркер фоновых задач)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from packages.contracts.pydantic import Severity


class Channel(StrEnum):
    """Канал доставки уведомления. Значения совпадают с протоколами на диаграмме L2."""

    EMAIL = "email"  # SMTP / TLS
    PUSH = "push"  # APNs / FCM


@dataclass(frozen=True, slots=True)
class CaseInfo:
    """Минимум данных об обращении, нужный для расчёта срока и выбора владельца."""

    case_id: UUID
    review_id: UUID
    created_at: datetime
    severity: Severity | None
    direction: str | None


@dataclass(frozen=True, slots=True)
class OwnerCandidate:
    """Кандидат в владельцы обращения из справочника владельцев."""

    owner_id: str
    open_cases: int


@dataclass(frozen=True, slots=True)
class SlaResult:
    """Контрольный срок и имя правила, по которому он получен."""

    due_at: datetime
    rule: str


@dataclass(frozen=True, slots=True)
class Notification:
    """Уведомление одному получателю по одному каналу."""

    case_id: UUID
    recipient_id: str
    channel: Channel
    subject: str
    body: str


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    """Итог обработки события case_created."""

    case_id: UUID
    owner_id: str
    due_at: datetime
    sla_rule: str
    channels: tuple[Channel, ...]
