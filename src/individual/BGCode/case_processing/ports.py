"""Порты компонента: интерфейсы к соседним элементам. Реализации подставляются снаружи."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from .models import Notification, OwnerCandidate


class CaseRepository(Protocol):
    """Доступ к базе данных (database, SQL / TCP). Реализует слой SQLAlchemy воркера."""

    def owner_candidates(self, direction: str | None) -> Sequence[OwnerCandidate]:
        """Владельцы направления из справочника."""
        ...

    def assign(self, case_id: str, owner_id: str, due_at: datetime) -> bool:
        """Записывает владельца и срок. False, если обращение уже назначено (повторная доставка)."""
        ...


class NotifyPort(Protocol):
    """Порт сервиса уведомлений (bg_notify_port): SMTP / TLS и HTTPS."""

    def send(self, notification: Notification) -> None:
        """Передаёт одно уведомление во внешний сервис."""
        ...
