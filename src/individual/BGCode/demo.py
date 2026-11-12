"""Демонстрация подмены стратегий при обработке события «обращение создано».

Запуск из папки src/individual/BGCode:  python demo.py
Базы данных и сервиса уведомлений нет: используются реализации портов в памяти.
"""

from __future__ import annotations

import json

from case_processing import (
    BusinessDaysSla,
    CaseEventConsumer,
    EmailOnlyChannel,
    FixedHoursSla,
    LeastLoadedStrategy,
    NotificationDispatcher,
    OwnerCandidate,
    PrimaryOwnerStrategy,
    SeverityBasedChannel,
    SlaCalculator,
    TopicSla,
)
from case_processing.memory import InMemoryCaseRepository, RecordingNotifyPort


def message(n: int, severity: str) -> str:
    return json.dumps({
        "event_type": "case_created",
        "case_id": f"00000000-0000-4000-8000-{n:012d}",
        "review_id": f"11111111-1111-4111-8111-{n:012d}",
        "occurred_at": "2026-11-06T10:00:00Z",
        "severity": severity,
        "direction": "ипотека",
    })


def run(title: str, sla: SlaCalculator, consumer_owner: PrimaryOwnerStrategy | LeastLoadedStrategy,
        channel: SeverityBasedChannel | EmailOnlyChannel) -> None:
    repo = InMemoryCaseRepository({"ипотека": [OwnerCandidate("owner-1", 7), OwnerCandidate("owner-2", 2)]})
    port = RecordingNotifyPort()
    consumer = CaseEventConsumer(repo, sla, consumer_owner, NotificationDispatcher(channel, port))
    print(f"== {title}")
    for n, severity in enumerate(("critical", "low"), start=1):
        result = consumer.handle(message(n, severity))
        assert result is not None
        print(f"  {severity:<8} владелец={result.owner_id} срок={result.due_at:%d.%m.%Y %H:%M} "
              f"правило={result.sla_rule} каналы={[c.value for c in result.channels]}")


if __name__ == "__main__":
    run("fixed_24h + primary_owner + severity_based", SlaCalculator(FixedHoursSla(24)),
        PrimaryOwnerStrategy(), SeverityBasedChannel())
    run("topic_sla + least_loaded + email_only", SlaCalculator(TopicSla({"ипотека": 8})),
        LeastLoadedStrategy(), EmailOnlyChannel())
    run("business_days_15 + primary_owner + severity_based", SlaCalculator(BusinessDaysSla()),
        PrimaryOwnerStrategy(), SeverityBasedChannel())
