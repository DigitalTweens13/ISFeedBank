"""Стратегии расчёта контрольного срока (bg_sla_strategy) и контекст bg_sla_calculator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import date, datetime, timedelta

from .models import CaseInfo, SlaResult


class SlaStrategy(ABC):
    """Контракт алгоритма расчёта срока. Имена реализаций совпадают с модулем Backend API."""

    name: str

    @abstractmethod
    def due_at(self, case: CaseInfo) -> datetime:
        """Возвращает момент, до которого нужно отреагировать на обращение."""


class FixedHoursSla(SlaStrategy):
    """Одинаковый срок в часах для всех обращений."""

    name = "fixed_24h"

    def __init__(self, hours: int = 24) -> None:
        if hours <= 0:
            raise ValueError("срок должен быть положительным")
        self._hours = hours

    def due_at(self, case: CaseInfo) -> datetime:
        return case.created_at + timedelta(hours=self._hours)


class TopicSla(SlaStrategy):
    """Срок в часах берётся из справочника по продуктовому направлению."""

    name = "topic_sla"

    def __init__(self, hours_by_direction: Mapping[str, int], default_hours: int = 24) -> None:
        self._hours = dict(hours_by_direction)
        self._default = default_hours

    def due_at(self, case: CaseInfo) -> datetime:
        hours = self._hours.get(case.direction or "", self._default)
        return case.created_at + timedelta(hours=hours)


class BusinessDaysSla(SlaStrategy):
    """Срок в рабочих днях (по умолчанию 15) с пропуском выходных и праздников."""

    name = "business_days_15"

    def __init__(self, days: int = 15, holidays: frozenset[date] = frozenset()) -> None:
        if days <= 0:
            raise ValueError("число дней должно быть положительным")
        self._days = days
        self._holidays = holidays

    def due_at(self, case: CaseInfo) -> datetime:
        current = case.created_at
        left = self._days
        while left > 0:
            current += timedelta(days=1)
            if current.weekday() < 5 and current.date() not in self._holidays:
                left -= 1
        return current


class SlaCalculator:
    """Контекст паттерна «Стратегия» (bg_sla_calculator): делегирует расчёт активной стратегии."""

    def __init__(self, strategy: SlaStrategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> SlaStrategy:
        return self._strategy

    def set_strategy(self, strategy: SlaStrategy) -> None:
        self._strategy = strategy

    def calculate(self, case: CaseInfo) -> SlaResult:
        due = self._strategy.due_at(case)
        if due <= case.created_at:
            raise ValueError("срок обязан быть позже момента создания обращения")
        return SlaResult(due_at=due, rule=self._strategy.name)
