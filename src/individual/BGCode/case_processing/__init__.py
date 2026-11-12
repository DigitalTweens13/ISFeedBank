"""Прототип компонента «Потребитель событий обращений» воркера фоновых задач (ЛР № 3, уровень L4)."""

from . import _contracts_path  # noqa: F401  (должен идти первым)
from .channels import ChannelStrategy, EmailOnlyChannel, PushOnlyChannel, SeverityBasedChannel
from .consumer import CaseEventConsumer
from .dispatcher import NotificationDispatcher
from .errors import InvalidEventError, NoOwnerAvailableError
from .models import CaseInfo, Channel, Notification, OwnerCandidate, ProcessingResult, SlaResult
from .owners import (
    LeastLoadedStrategy,
    OwnerAssignmentStrategy,
    PrimaryOwnerStrategy,
    RoundRobinStrategy,
)
from .ports import CaseRepository, NotifyPort
from .registry import StrategyRegistry
from .sla import BusinessDaysSla, FixedHoursSla, SlaCalculator, SlaStrategy, TopicSla

__all__ = [
    "BusinessDaysSla", "CaseEventConsumer", "CaseInfo", "CaseRepository", "Channel",
    "ChannelStrategy", "EmailOnlyChannel", "FixedHoursSla", "InvalidEventError",
    "LeastLoadedStrategy", "NoOwnerAvailableError", "Notification", "NotificationDispatcher",
    "NotifyPort", "OwnerAssignmentStrategy", "OwnerCandidate", "PrimaryOwnerStrategy",
    "ProcessingResult", "PushOnlyChannel", "RoundRobinStrategy", "SeverityBasedChannel",
    "SlaCalculator", "SlaResult", "SlaStrategy", "StrategyRegistry", "TopicSla",
]
