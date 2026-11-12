"""Исключения компонента. Брокер по ним выбирает стратегию подтверждения (ack / в .dlq)."""

from __future__ import annotations


class InvalidEventError(ValueError):
    """Сообщение не соответствует схеме cases.events.v1: повторять доставку бессмысленно."""


class NoOwnerAvailableError(RuntimeError):
    """В справочнике нет владельца для направления: нужна ручная разборка."""
