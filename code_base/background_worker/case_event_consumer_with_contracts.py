# background_worker/case_event_consumer.py — с контрактом
import json
import pika
from packages.contracts.pydantic import CasesEventV1

def on_message(ch, method, properties, body: bytes) -> None:
    raw = json.loads(body)
    try:
        event = CasesEventV1.model_validate(raw)
    except Exception as exc:
        # Некорректное сообщение: не подтверждаем, отправляем в dlq
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        log_error("invalid case event", raw, exc)
        return

    if event.event_type == "case_created":
        notify_owner(event.case_id, event.review_id, event.severity)
    elif event.event_type == "case_escalated":
        notify_head(event.case_id, event.severity)
    elif event.event_type == "case_closed":
        close_case(event.case_id)

    ch.basic_ack(delivery_tag=method.delivery_tag)