# Пакет контрактов ISFeedBank

Содержит описания стыков между контейнерами системы.

## Состав

| Папка | Что внутри | Генерируется |
|---|---|---|
| `openapi/` | REST-контракт Backend API (OpenAPI 3.1.0) | вручную, поддерживается как источник правды |
| `events/` | JSON Schema сообщений брокера | вручную, поддерживается как источник правды |
| `pydantic/` | Python-модели | `python -m scripts.generate_contracts` |
| `typescript/` | TypeScript-типы для фронтенда | вручную по `openapi/` и `events/` |

## Регенерация Python-моделей

```cmd
cd <корень репозитория>
python -m scripts.generate_contracts