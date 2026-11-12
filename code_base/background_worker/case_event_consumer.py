# background_worker/case_event_consumer.py — ЧЕРНОВИК, без контракта
import json
import pika

def on_message(ch, method, properties, body: bytes) -> None:
    data = json.loads(body)

    # «Ну наверное, поле называется case_id»
    case_id = data["case_id"]

    # «Наверное, review_id тоже есть»
    review_id = data["review_id"]

    # «И event_type — чтобы понять, что это за событие»
    event_type = data.get("event_type", "case_created")

    if event_type == "case_created":
        notify_owner(case_id, review_id)

    ch.basic_ack(delivery_tag=method.delivery_tag)