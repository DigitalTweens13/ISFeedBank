from packages.contracts.pydantic import (
    CasesEventV1,
    EventType,
    ReviewsLabelingTaskV1,
    Severity,
    Source,
)

# Валидное сообщение разметки
task = ReviewsLabelingTaskV1.model_validate({
    "review_id": "3f0e4e8c-2b1a-4c1e-9f5a-1a2b3c4d5e6f",
    "text": "Списали комиссию за перевод без предупреждения",
    "source": "sravni_ru",
    "rating": 1,
    "published_at": "2026-10-24T10:00:00Z",
})
print("OK task:", task.source, task.rating)

# Невалидное — рейтинг вне диапазона
try:
    ReviewsLabelingTaskV1.model_validate({
        "review_id": "3f0e4e8c-2b1a-4c1e-9f5a-1a2b3c4d5e6f",
        "text": "x",
        "source": "sravni_ru",
        "rating": 9,
        "published_at": "2026-10-24T10:00:00Z",
    })
except Exception as e:
    print("OK invalid rejected:", str(e).splitlines()[0])

# Валидное событие
event = CasesEventV1.model_validate({
    "event_type": "case_created",
    "case_id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
    "review_id": "3f0e4e8c-2b1a-4c1e-9f5a-1a2b3c4d5e6f",
    "occurred_at": "2026-10-24T10:00:05Z",
    "severity": "critical",
})
print("OK event:", event.event_type, event.severity)

# Невалидное — неизвестный event_type
try:
    CasesEventV1.model_validate({
        "event_type": "case_deleted",
        "case_id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
        "review_id": "3f0e4e8c-2b1a-4c1e-9f5a-1a2b3c4d5e6f",
        "occurred_at": "2026-10-24T10:00:05Z",
    })
except Exception as e:
    print("OK unknown event rejected:", str(e).splitlines()[0])

from packages.contracts.pydantic import (
    BatchReport,
    CaseDto,
    ReviewBatch,
    Role,
    SessionDto,
)

# Простая проверка: классы создались и знают свои поля
print("OK api models loaded")
print("OK Role values:", [r.value for r in Role])
print("OK CaseDto fields:", list(CaseDto.model_fields.keys()))
print("OK SessionDto fields:", list(SessionDto.model_fields.keys()))

# Проверка: все классы из api.py импортируются через публичный API пакета
from packages.contracts.pydantic import (
    BatchReport, BatchStatusDto, ByDirectionItem, CaseDetailsDto, CaseDto,
    CaseStatus, DashboardDto, DeviceRegistration, DictionaryEntryDto, Dynamic,
    Module, Period, Platform, Provider, RawReview, ReportDto, ReviewBatch,
    Role, Sentiment, SessionDto, State, StatusChange, StatusChangeRecord,
    StrategySwitch, Topic,
)
print("OK all api models importable:", 25)