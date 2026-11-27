"""HTTP-слой на FastAPI. Тонкий: разбирает запрос, вызывает сервис, сериализует ответ.

Бизнес-логики здесь нет. Сервисы синхронные, поэтому эндпоинты объявлены как
обычные ``def`` — FastAPI исполняет их в пуле потоков и не блокирует event loop.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, FastAPI, Header, Query, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from ..container import Container, Settings, build_container
from ..analytics.domain import AnalyticsQuery, Sentiment
from ..responses.domain import StatusHistoryEntry, Ticket, TicketFilter, TicketStatus
from ..shared import DomainError, Operation, ValidationFailed
from ..shared.http import extract_bearer


# ------------------------------- схемы -------------------------------------- #
class StatusChangeIn(BaseModel):
    status: TicketStatus
    reason: Optional[str] = Field(None, max_length=2000)
    expected_version: Optional[int] = None


class AssignOwnerIn(BaseModel):
    owner_id: Optional[str] = None      # пусто -> выберет стратегия назначения


class ReportIn(BaseModel):
    date_from: date
    date_to: date
    topics: list[str] = []
    sources: list[str] = []
    sentiments: list[Sentiment] = []
    granularity: str = "day"
    metrics: Optional[list[str]] = None
    format: Optional[str] = None


class StrategySwitchIn(BaseModel):
    module: str
    kind: str
    name: str


# ------------------------------- сериализация ------------------------------- #
def ticket_out(t: Ticket) -> dict:
    return {"id": t.id, "feedback_id": t.feedback_id, "topic": t.topic_code, "summary": t.summary,
            "status": t.status.value, "owner_id": t.owner_id,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "rejection_reason": t.rejection_reason, "escalated": t.escalated,
            "created_at": t.created_at.isoformat(), "updated_at": t.updated_at.isoformat(),
            "version": t.version}


def history_out(h: StatusHistoryEntry) -> dict:
    return {"id": h.id, "from": h.from_status.value if h.from_status else None,
            "to": h.to_status.value, "changed_by": h.changed_by,
            "changed_at": h.changed_at.isoformat(), "comment": h.comment}


def _query(date_from: date, date_to: date, topics, sources, sentiments, granularity) -> AnalyticsQuery:
    return AnalyticsQuery(date_from, date_to, tuple(topics), tuple(sources),
                          tuple(sentiments), granularity)


# ------------------------------- приложение --------------------------------- #
def create_app(container: Optional[Container] = None) -> FastAPI:
    c = container or build_container(Settings.from_env())
    app = FastAPI(title="Feedback Management Backend API", version="1.0.0")

    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.http_status == 401 else None
        return JSONResponse(status_code=exc.http_status, headers=headers, content={
            "error": {"code": exc.code, "message": exc.message, "details": exc.details}})

    # ---- модуль авторизации ------------------------------------------------ #
    auth = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @auth.get("/me")
    def me(authorization: Optional[str] = Header(None, include_in_schema=False)):
        p = c.auth.identify(extract_bearer(authorization))
        return {"subject": p.subject, "name": p.display_name, "roles": sorted(r.value for r in p.roles)}

    # ---- приём и валидация отзывов (связь 3) -------------------------------- #
    ingest = APIRouter(prefix="/api/v1/feedback", tags=["ingestion"])

    @ingest.post("/batches", status_code=202, openapi_extra={"requestBody": {"required": True, "content": {
        "application/json": {"schema": {"type": "object"}},
        "text/csv": {"schema": {"type": "string"}}}}})
    async def upload_batch(request: Request, profile: Optional[str] = Query(None),
                           authorization: Optional[str] = Header(None, include_in_schema=False)):
        token = extract_bearer(authorization)
        ctype = (request.headers.get("content-type") or "application/json").split(";")[0].strip().lower()
        parser = {"application/json": "json", "text/csv": "csv"}.get(ctype)
        if parser is None:
            raise ValidationFailed("Content-Type must be application/json or text/csv")
        body = await request.body()
        report = await run_in_threadpool(c.ingestion.ingest, token, body,
                                         parser=parser, validation=profile)
        return report.as_dict()

    # ---- аналитика (связи 7, 11) ------------------------------------------- #
    an = APIRouter(prefix="/api/v1", tags=["analytics"])

    @an.get("/analytics/dashboard")
    def dashboard(date_from: date, date_to: date, metric: Optional[str] = None,
                  granularity: str = "day", topics: list[str] = Query([]),
                  sources: list[str] = Query([]), sentiments: list[Sentiment] = Query([]),
                  authorization: Optional[str] = Header(None, include_in_schema=False)):
        q = _query(date_from, date_to, topics, sources, sentiments, granularity)
        return c.analytics.dashboard(extract_bearer(authorization), q, metric)

    @an.get("/feedback")
    def feedback_registry(date_from: date, date_to: date, topics: list[str] = Query([]),
                          sources: list[str] = Query([]), sentiments: list[Sentiment] = Query([]),
                          limit: int = 50, offset: int = 0,
                          authorization: Optional[str] = Header(None, include_in_schema=False)):
        q = _query(date_from, date_to, topics, sources, sentiments, "day")
        return c.analytics.list_feedback(extract_bearer(authorization), q, limit, offset)

    @an.get("/references")
    def references(authorization: Optional[str] = Header(None, include_in_schema=False)):
        return c.analytics.references(extract_bearer(authorization))

    @an.post("/analytics/reports")
    def export_report(body: ReportIn, authorization: Optional[str] = Header(None, include_in_schema=False)):
        q = _query(body.date_from, body.date_to, body.topics, body.sources, body.sentiments, body.granularity)
        return c.analytics.export_report(extract_bearer(authorization), q, body.metrics, body.format)

    # ---- управление ответами и статусами (связи 12, 13) ---------------------- #
    tk = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])

    @tk.get("")
    def list_tickets(status: list[TicketStatus] = Query([]), owner_id: Optional[str] = None,
                     topic: Optional[str] = None, unassigned: bool = False, overdue: bool = False,
                     escalated: bool = False, limit: int = 50, offset: int = 0,
                     authorization: Optional[str] = Header(None, include_in_schema=False)):
        flt = TicketFilter(tuple(status), owner_id, topic, unassigned, overdue, escalated, limit, offset)
        return [ticket_out(t) for t in c.responses.list_tickets(extract_bearer(authorization), flt)]

    @tk.get("/{ticket_id}")
    def get_ticket(ticket_id: str, authorization: Optional[str] = Header(None, include_in_schema=False)):
        ticket, history = c.responses.get_ticket(extract_bearer(authorization), ticket_id)
        return {**ticket_out(ticket), "history": [history_out(h) for h in history]}

    @tk.post("/{ticket_id}/status")
    def change_status(ticket_id: str, body: StatusChangeIn, authorization: Optional[str] = Header(None, include_in_schema=False)):
        t = c.responses.change_status(extract_bearer(authorization), ticket_id, body.status,
                                      body.reason, body.expected_version)
        return ticket_out(t)

    @tk.post("/{ticket_id}/owner")
    def assign_owner(ticket_id: str, body: AssignOwnerIn, authorization: Optional[str] = Header(None, include_in_schema=False)):
        return ticket_out(c.responses.assign_owner(extract_bearer(authorization), ticket_id, body.owner_id))

    # ---- администрирование стратегий ---------------------------------------- #
    adm = APIRouter(prefix="/api/v1/admin/strategies", tags=["admin"])

    @adm.get("")
    def list_strategies(authorization: Optional[str] = Header(None, include_in_schema=False)):
        c.auth.authorize(extract_bearer(authorization), Operation.MANAGE_STRATEGIES)
        return {m: cat.describe() for m, cat in c.catalogs().items()}

    @adm.put("")
    def switch_strategy(body: StrategySwitchIn, authorization: Optional[str] = Header(None, include_in_schema=False)):
        c.auth.authorize(extract_bearer(authorization), Operation.MANAGE_STRATEGIES)
        catalogs = c.catalogs()
        if body.module not in catalogs:
            raise ValidationFailed(f"Unknown module '{body.module}'", details={"available": sorted(catalogs)})
        catalogs[body.module].switch(body.kind, body.name)
        return catalogs[body.module].describe()

    for r in (auth, ingest, an, tk, adm):
        app.include_router(r)

    def openapi_with_bearer():
        """Добавляет в Swagger кнопку Authorize (схема Bearer JWT)."""
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
            "type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        schema["security"] = [{"bearerAuth": []}]
        app.openapi_schema = schema
        return schema

    app.openapi = openapi_with_bearer

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    return app
