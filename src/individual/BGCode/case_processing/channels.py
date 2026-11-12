"""Стратегии выбора каналов уведомления (bg_channel_strategy)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from packages.contracts.pydantic import Severity

from .models import Channel


class ChannelStrategy(ABC):
    """Контракт выбора каналов доставки для обращения заданной важности."""

    name: str

    @abstractmethod
    def channels(self, severity: Severity | None) -> tuple[Channel, ...]:
        """Непустой набор каналов."""


class EmailOnlyChannel(ChannelStrategy):
    name = "email_only"

    def channels(self, severity: Severity | None) -> tuple[Channel, ...]:
        return (Channel.EMAIL,)


class PushOnlyChannel(ChannelStrategy):
    name = "push_only"

    def channels(self, severity: Severity | None) -> tuple[Channel, ...]:
        return (Channel.PUSH,)


class SeverityBasedChannel(ChannelStrategy):
    """Критичные и важные обращения — почта и push, остальные — только почта."""

    name = "severity_based"

    def channels(self, severity: Severity | None) -> tuple[Channel, ...]:
        if severity in (Severity.critical, Severity.high):
            return (Channel.EMAIL, Channel.PUSH)
        return (Channel.EMAIL,)
