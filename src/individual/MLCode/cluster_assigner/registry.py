"""Реестр стратегий: выбор алгоритма по имени из конфигурации воркера."""

from __future__ import annotations

from collections.abc import Callable

from .strategies import ClusterAssignmentStrategy

StrategyFactory = Callable[[], ClusterAssignmentStrategy]


class StrategyRegistry:
    """Хранит фабрики стратегий по именам.

    Новая стратегия регистрируется здесь и не требует правок в ClusterAssigner.
    """

    def __init__(self) -> None:
        self._factories: dict[str, StrategyFactory] = {}

    def register(self, name: str, factory: StrategyFactory) -> None:
        if name in self._factories:
            raise ValueError(f"стратегия {name!r} уже зарегистрирована")
        self._factories[name] = factory

    def create(self, name: str) -> ClusterAssignmentStrategy:
        try:
            factory = self._factories[name]
        except KeyError:
            known = ", ".join(sorted(self._factories)) or "нет"
            raise KeyError(f"неизвестная стратегия {name!r}; доступны: {known}") from None
        return factory()

    def names(self) -> list[str]:
        return sorted(self._factories)
