"""Реестр стратегий: выбор алгоритма по имени из конфигурации воркера."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

S = TypeVar("S")


class StrategyRegistry(Generic[S]):
    """Хранит фабрики стратегий одного вида. Новая стратегия добавляется без правок контекстов."""

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], S]] = {}

    def register(self, name: str, factory: Callable[[], S]) -> None:
        if name in self._factories:
            raise ValueError(f"стратегия {name!r} уже зарегистрирована")
        self._factories[name] = factory

    def create(self, name: str) -> S:
        try:
            return self._factories[name]()
        except KeyError:
            known = ", ".join(sorted(self._factories)) or "нет"
            raise KeyError(f"неизвестная стратегия {name!r}; доступны: {known}") from None

    def names(self) -> list[str]:
        return sorted(self._factories)
