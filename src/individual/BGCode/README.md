# ЛР № 3 (TL): прототип компонента «Потребитель событий обращений»

Компонент `bg_case_event_consumer` воркера фоновых задач и связанная с ним рассылка `bg_notification_comp`
(см. `../BGDiagramsCode/bg_l3.puml`). Диаграмма классов: `../BGDiagramsCode/bg_l4.puml`.

Что делает: получает событие `case_created` из очереди `cases.events`, проверяет его по контракту
`CasesEventV1`, назначает обращению владельца и контрольный срок и уведомляет владельца.
Алгоритмы подменяются стратегиями:

| Точка вариативности | Интерфейс (ID глоссария) | Реализации |
|---|---|---|
| Контрольный срок | `SlaStrategy` (`bg_sla_strategy`), контекст `SlaCalculator` (`bg_sla_calculator`) | `fixed_24h`, `topic_sla`, `business_days_15` |
| Владелец | `OwnerAssignmentStrategy` (`bg_owner_assignment_strategy`) | `primary_owner`, `least_loaded`, `round_robin` |
| Каналы уведомления | `ChannelStrategy` (`bg_channel_strategy`) | `email_only`, `push_only`, `severity_based` |

Имена стратегий срока и владельца совпадают с модулем «Управление ответами и статусами» Backend API (BE_lab3).

Запуск из этой папки (нужен Python 3.11+ и `pydantic>=2.6`; контракты берутся из `docs/packages/contracts/pydantic`,
путь добавляется автоматически):

```
pip install -r requirements.txt
python demo.py                         # три набора стратегий на одних и тех же событиях
python -m unittest -v                  # 17 тестов
mypy                                   # строгая типизация (настройки в mypy.ini)
```

Правила синхронизации: поля сообщения не дублируются — модель `CasesEventV1` импортируется из контрактов;
при несовместимом изменении схемы создаётся `cases.events.v2.json`, а этот компонент переходит на неё через PR
с ревью владельца контейнера. Порты `CaseRepository` и `NotifyPort` реализуются слоем SQLAlchemy и адаптером
`notify_service`; в прототипе их заменяют `memory.py`.
