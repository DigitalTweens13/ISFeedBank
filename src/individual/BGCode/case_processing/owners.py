"""Стратегии выбора владельца обращения (bg_owner_assignment_strategy)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .errors import NoOwnerAvailableError
from .models import OwnerCandidate


class OwnerAssignmentStrategy(ABC):
    """Контракт выбора владельца среди кандидатов направления."""

    name: str

    def choose(self, candidates: Sequence[OwnerCandidate]) -> str:
        """Возвращает owner_id. Пустой список кандидатов — ошибка для всех стратегий."""
        if not candidates:
            raise NoOwnerAvailableError("для направления не найден ни один владелец")
        return self._pick(candidates)

    @abstractmethod
    def _pick(self, candidates: Sequence[OwnerCandidate]) -> str:
        """Выбор из непустого списка."""


class PrimaryOwnerStrategy(OwnerAssignmentStrategy):
    """Всегда первый (основной) владелец направления."""

    name = "primary_owner"

    def _pick(self, candidates: Sequence[OwnerCandidate]) -> str:
        return candidates[0].owner_id


class LeastLoadedStrategy(OwnerAssignmentStrategy):
    """Владелец с наименьшим числом открытых обращений; при равенстве — первый в списке."""

    name = "least_loaded"

    def _pick(self, candidates: Sequence[OwnerCandidate]) -> str:
        return min(candidates, key=lambda c: c.open_cases).owner_id


class RoundRobinStrategy(OwnerAssignmentStrategy):
    """Владельцы по кругу. Счётчик хранится в стратегии, поэтому один экземпляр на воркер."""

    name = "round_robin"

    def __init__(self) -> None:
        self._counter = 0

    def _pick(self, candidates: Sequence[OwnerCandidate]) -> str:
        chosen = candidates[self._counter % len(candidates)]
        self._counter += 1
        return chosen.owner_id
