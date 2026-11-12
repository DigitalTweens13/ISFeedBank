"""Реализации портов в памяти для демонстрации и тестов (без БД и сервиса уведомлений)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from .models import Notification, OwnerCandidate


class InMemoryCaseRepository:
    def __init__(self, owners: dict[str, list[OwnerCandidate]]) -> None:
        self._owners = owners
        self.assigned: dict[str, tuple[str, datetime]] = {}

    def owner_candidates(self, direction: str | None) -> Sequence[OwnerCandidate]:
        return self._owners.get(direction or "", [])

    def assign(self, case_id: str, owner_id: str, due_at: datetime) -> bool:
        if case_id in self.assigned:
            return False
        self.assigned[case_id] = (owner_id, due_at)
        return True


class RecordingNotifyPort:
    def __init__(self) -> None:
        self.sent: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.sent.append(notification)
