"""Тесты компонента обработки событий обращений."""

from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timezone
from uuid import UUID

from packages.contracts.pydantic import Severity

from case_processing import (
    BusinessDaysSla,
    CaseEventConsumer,
    CaseInfo,
    Channel,
    EmailOnlyChannel,
    FixedHoursSla,
    InvalidEventError,
    LeastLoadedStrategy,
    NoOwnerAvailableError,
    NotificationDispatcher,
    OwnerCandidate,
    PrimaryOwnerStrategy,
    PushOnlyChannel,
    RoundRobinStrategy,
    SeverityBasedChannel,
    SlaCalculator,
    SlaStrategy,
    StrategyRegistry,
    TopicSla,
)
from case_processing.memory import InMemoryCaseRepository, RecordingNotifyPort

CASE = "7c9e6679-7425-40de-944b-e07fc1f90ae7"
REVIEW = "3f0e4e8c-2b1a-4c1e-9f5a-1a2b3c4d5e6f"
T0 = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)  # пятница


def event(**extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "event_type": "case_created",
        "case_id": CASE,
        "review_id": REVIEW,
        "occurred_at": "2026-11-06T10:00:00Z",
        "severity": "critical",
        "direction": "ипотека",
    }
    base.update(extra)
    return base


def info(severity: Severity | None = Severity.high, direction: str | None = "карты") -> CaseInfo:
    return CaseInfo(UUID(CASE), UUID(REVIEW), T0, severity, direction)


def build(
    sla: SlaStrategy | None = None,
) -> tuple[CaseEventConsumer, InMemoryCaseRepository, RecordingNotifyPort]:
    repo = InMemoryCaseRepository(
        {"ипотека": [OwnerCandidate("owner-1", 5), OwnerCandidate("owner-2", 1)]}
    )
    port = RecordingNotifyPort()
    consumer = CaseEventConsumer(
        repo,
        SlaCalculator(sla or FixedHoursSla(24)),
        PrimaryOwnerStrategy(),
        NotificationDispatcher(SeverityBasedChannel(), port),
    )
    return consumer, repo, port


class SlaStrategies(unittest.TestCase):
    def test_fixed_hours(self) -> None:
        self.assertEqual((T0.day + 1), FixedHoursSla(24).due_at(info()).day)

    def test_topic_uses_direction_and_default(self) -> None:
        topic = TopicSla({"карты": 4}, default_hours=48)
        self.assertEqual(14, topic.due_at(info(direction="карты")).hour)
        self.assertEqual(8, topic.due_at(info(direction="прочее")).day)

    def test_business_days_skip_weekend_and_holiday(self) -> None:
        # пятница + 2 рабочих дня; понедельник 9 ноября объявлен выходным
        strategy = BusinessDaysSla(days=2, holidays=frozenset({date(2026, 11, 9)}))
        self.assertEqual(date(2026, 11, 11), strategy.due_at(info()).date())

    def test_calculator_swaps_strategy_without_changes(self) -> None:
        calc = SlaCalculator(FixedHoursSla(1))
        first = calc.calculate(info())
        calc.set_strategy(FixedHoursSla(48))
        second = calc.calculate(info())
        self.assertEqual("fixed_24h", first.rule)
        self.assertGreater(second.due_at, first.due_at)

    def test_invalid_parameters_rejected(self) -> None:
        with self.assertRaises(ValueError):
            FixedHoursSla(0)
        with self.assertRaises(ValueError):
            BusinessDaysSla(0)


class OwnerStrategies(unittest.TestCase):
    cands = [OwnerCandidate("a", 3), OwnerCandidate("b", 1), OwnerCandidate("c", 1)]

    def test_primary_and_least_loaded(self) -> None:
        self.assertEqual("a", PrimaryOwnerStrategy().choose(self.cands))
        self.assertEqual("b", LeastLoadedStrategy().choose(self.cands))

    def test_round_robin_cycles(self) -> None:
        rr = RoundRobinStrategy()
        self.assertEqual(["a", "b", "c", "a"], [rr.choose(self.cands) for _ in range(4)])

    def test_empty_candidates(self) -> None:
        for strategy in (PrimaryOwnerStrategy(), LeastLoadedStrategy(), RoundRobinStrategy()):
            with self.assertRaises(NoOwnerAvailableError):
                strategy.choose([])


class Channels(unittest.TestCase):
    def test_strategies(self) -> None:
        self.assertEqual((Channel.EMAIL,), EmailOnlyChannel().channels(None))
        self.assertEqual((Channel.PUSH,), PushOnlyChannel().channels(None))
        both = (Channel.EMAIL, Channel.PUSH)
        self.assertEqual(both, SeverityBasedChannel().channels(Severity.critical))
        self.assertEqual((Channel.EMAIL,), SeverityBasedChannel().channels(Severity.low))


class Consumer(unittest.TestCase):
    def test_case_created_assigns_owner_sla_and_notifies(self) -> None:
        consumer, repo, port = build()
        result = consumer.handle(json.dumps(event()))
        assert result is not None
        self.assertEqual("owner-1", result.owner_id)
        self.assertEqual(CASE, str(result.case_id))
        self.assertEqual(result.due_at, repo.assigned[CASE][1])
        self.assertEqual([Channel.EMAIL, Channel.PUSH], [n.channel for n in port.sent])

    def test_dict_and_bytes_accepted(self) -> None:
        consumer, _, _ = build()
        self.assertIsNotNone(consumer.handle(event()))
        consumer2, _, _ = build()
        self.assertIsNotNone(consumer2.handle(json.dumps(event()).encode()))

    def test_redelivery_is_idempotent(self) -> None:
        consumer, _, port = build()
        self.assertIsNotNone(consumer.handle(event()))
        self.assertIsNone(consumer.handle(event()))
        self.assertEqual(2, len(port.sent))  # уведомления ушли только один раз

    def test_other_event_types_ignored(self) -> None:
        consumer, repo, port = build()
        self.assertIsNone(consumer.handle(event(event_type="case_closed")))
        self.assertEqual({}, repo.assigned)
        self.assertEqual([], port.sent)

    def test_contract_violations_raise_invalid_event(self) -> None:
        consumer, _, _ = build()
        for bad in ("не json", json.dumps(event(case_id="123")), json.dumps(event(extra=1)),
                    json.dumps({"event_type": "case_created"})):
            with self.assertRaises(InvalidEventError):
                consumer.handle(bad)

    def test_no_owner_for_direction(self) -> None:
        consumer, _, port = build()
        with self.assertRaises(NoOwnerAvailableError):
            consumer.handle(event(direction="отделения"))
        self.assertEqual([], port.sent)

    def test_owner_strategy_swap(self) -> None:
        consumer, _, _ = build()
        consumer.set_owner_strategy(LeastLoadedStrategy())
        result = consumer.handle(event())
        assert result is not None
        self.assertEqual("owner-2", result.owner_id)


class Registry(unittest.TestCase):
    def test_register_create_names(self) -> None:
        registry: StrategyRegistry[SlaStrategy] = StrategyRegistry()
        registry.register("fixed_24h", FixedHoursSla)
        registry.register("business_days_15", BusinessDaysSla)
        self.assertEqual(["business_days_15", "fixed_24h"], registry.names())
        self.assertIsInstance(registry.create("fixed_24h"), FixedHoursSla)
        with self.assertRaises(KeyError):
            registry.create("нет такой")
        with self.assertRaises(ValueError):
            registry.register("fixed_24h", FixedHoursSla)


if __name__ == "__main__":
    unittest.main()
