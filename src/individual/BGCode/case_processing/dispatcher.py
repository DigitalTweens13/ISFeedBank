"""Рассылка уведомлений (bg_notification_comp): каналы выбирает стратегия, отправляет порт."""

from __future__ import annotations

from .channels import ChannelStrategy
from .models import CaseInfo, Channel, Notification, SlaResult
from .ports import NotifyPort


class NotificationDispatcher:
    """Контекст паттерна «Стратегия» для каналов уведомления."""

    def __init__(self, strategy: ChannelStrategy, port: NotifyPort) -> None:
        self._strategy = strategy
        self._port = port

    def set_strategy(self, strategy: ChannelStrategy) -> None:
        self._strategy = strategy

    def notify_new_case(self, case: CaseInfo, owner_id: str, sla: SlaResult) -> tuple[Channel, ...]:
        """Сообщает владельцу о новом обращении по всем каналам выбранной стратегии."""
        channels = self._strategy.channels(case.severity)
        if not channels:
            raise ValueError(f"стратегия {self._strategy.name!r} вернула пустой набор каналов")
        for channel in channels:
            self._port.send(
                Notification(
                    case_id=case.case_id,
                    recipient_id=owner_id,
                    channel=channel,
                    subject="Новое обращение по вашему направлению",
                    body=f"Обращение {case.case_id}, ответить до {sla.due_at:%d.%m.%Y %H:%M}",
                )
            )
        return channels
