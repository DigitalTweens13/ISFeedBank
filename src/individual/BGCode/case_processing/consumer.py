"""Потребитель событий обращений (bg_case_event_consumer): обработка события case_created."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from packages.contracts.pydantic import CasesEventV1, EventType

from .dispatcher import NotificationDispatcher
from .errors import InvalidEventError
from .models import CaseInfo, ProcessingResult
from .owners import OwnerAssignmentStrategy
from .ports import CaseRepository
from .sla import SlaCalculator


class CaseEventConsumer:
    """Проверяет событие, назначает владельца и срок, запускает рассылку.

    Все алгоритмы подставляются снаружи: срок — через SlaCalculator,
    владелец — через OwnerAssignmentStrategy, каналы — через NotificationDispatcher.
    """

    def __init__(
        self,
        repository: CaseRepository,
        sla: SlaCalculator,
        owners: OwnerAssignmentStrategy,
        dispatcher: NotificationDispatcher,
    ) -> None:
        self._repository = repository
        self._sla = sla
        self._owners = owners
        self._dispatcher = dispatcher

    def set_owner_strategy(self, strategy: OwnerAssignmentStrategy) -> None:
        self._owners = strategy

    def handle(self, message: bytes | str | Mapping[str, Any]) -> ProcessingResult | None:
        """Обрабатывает одно сообщение очереди cases.events.

        Возвращает None, если событие не требует действий (не case_created) или обращение
        уже назначено при предыдущей доставке. InvalidEventError означает неисправимое
        сообщение: стратегия подтверждения брокера отправит его в cases.events.dlq.
        """
        event = self._parse(message)
        if event.event_type is not EventType.case_created:
            return None
        case = CaseInfo(
            case_id=event.case_id,
            review_id=event.review_id,
            created_at=event.occurred_at,
            severity=event.severity,
            direction=event.direction,
        )
        sla = self._sla.calculate(case)
        owner_id = self._owners.choose(self._repository.owner_candidates(case.direction))
        if not self._repository.assign(str(case.case_id), owner_id, sla.due_at):
            return None
        channels = self._dispatcher.notify_new_case(case, owner_id, sla)
        return ProcessingResult(case.case_id, owner_id, sla.due_at, sla.rule, channels)

    @staticmethod
    def _parse(message: bytes | str | Mapping[str, Any]) -> CasesEventV1:
        try:
            if isinstance(message, (bytes, str)):
                return CasesEventV1.model_validate_json(message)
            return CasesEventV1.model_validate(dict(message))
        except (ValidationError, json.JSONDecodeError) as exc:
            raise InvalidEventError(str(exc)) from exc
