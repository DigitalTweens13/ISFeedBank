"""Пакет контрактов: сгенерированные Pydantic-модели.

Публичный API:
    from packages.contracts.pydantic import (
        ReviewsLabelingTaskV1, CasesEventV1,       # события брокера
        CaseDto, ReviewBatch, BatchReport,          # REST-модели
    )
"""
from .api import (
    BatchReport,
    BatchStatusDto,
    ByDirectionItem,
    CaseDetailsDto,
    CaseDto,
    CaseStatus,
    DashboardDto,
    DeviceRegistration,
    DictionaryEntryDto,
    Dynamic,
    Module,
    Period,
    Platform,
    Provider,
    RawReview,
    ReportDto,
    ReviewBatch,
    Role,
    Sentiment,
    SessionDto,
    State,
    StatusChange,
    StatusChangeRecord,
    StrategySwitch,
    Topic,
)
from .events import (
    CasesEventV1,
    EventType,
    ReviewsLabelingTaskV1,
    Severity,
    Source,
)

__all__ = [
    # api
    "BatchReport",
    "BatchStatusDto",
    "ByDirectionItem",
    "CaseDetailsDto",
    "CaseDto",
    "CaseStatus",
    "DashboardDto",
    "DeviceRegistration",
    "DictionaryEntryDto",
    "Dynamic",
    "Module",
    "Period",
    "Platform",
    "Provider",
    "RawReview",
    "ReportDto",
    "ReviewBatch",
    "Role",
    "Sentiment",
    "SessionDto",
    "State",
    "StatusChange",
    "StatusChangeRecord",
    "StrategySwitch",
    "Topic",
    # events
    "CasesEventV1",
    "EventType",
    "ReviewsLabelingTaskV1",
    "Severity",
    "Source",
]