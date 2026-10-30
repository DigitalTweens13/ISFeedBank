"""Регенерация пакета packages/contracts/pydantic из исходных контрактов.

Запуск из корня репозитория (где лежит packages/):
    python -m scripts.generate_contracts

Скрипт использует установленный datamodel-code-generator (модуль
datamodel_code_generator) и не требует отдельного ярлыка в PATH.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

# ─── настройки ────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent           # <root>, где лежит packages/

CONTRACTS = BASE_DIR / "docs" / "packages" / "contracts"
PYDANTIC_DIR = CONTRACTS / "pydantic"

TARGET_PYTHON = "3.11"  # при смене версии Python в проекте — поменять здесь

JOBS = [
    {
        "name": "events (JSON Schema)",
        "input": CONTRACTS / "events" / "reviews.labeling.v1.json",
        "input_type": "jsonschema",
        "output": PYDANTIC_DIR / "_events_labeling_tmp.py",
        "class_name": "ReviewsLabelingTaskV1",
        "extra": [],
    },
    {
        "name": "events (cases)",
        "input": CONTRACTS / "events" / "cases.events.v1.json",
        "input_type": "jsonschema",
        "output": PYDANTIC_DIR / "_events_cases_tmp.py",
        "class_name": "CasesEventV1",
        "extra": [],
    },
    {
        "name": "api (OpenAPI)",
        "input": CONTRACTS / "openapi" / "api.v1.yaml",
        "input_type": "openapi",
        "output": PYDANTIC_DIR / "api.py",
        "class_name": None,
        "extra": ["--openapi-scopes", "schemas"],
    },
]

# ─── утилиты ──────────────────────────────────────────────────────────

def check_generator() -> None:
    """Проверить, что datamodel-code-generator установлен."""
    try:
        subprocess.run(
            [sys.executable, "-m", "datamodel_code_generator", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        print(
            "ОШИБКА: datamodel-code-generator не установлен.\n"
            "Установите его командой:\n"
            '    python -m pip install "datamodel-code-generator[http]"\n'
            f"Детали: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def run_generator(job: dict) -> None:
    """Запустить одну генерацию."""
    cmd = [
        sys.executable, "-m", "datamodel_code_generator",
        "--input", str(job["input"]),
        "--input-file-type", job["input_type"],
        "--output", str(job["output"]),
        "--output-model-type", "pydantic_v2.BaseModel",
        "--target-python-version", TARGET_PYTHON,
    ]
    if job["class_name"]:
        cmd += ["--class-name", job["class_name"]]
    cmd += job["extra"]

    print(f"→ {job['name']}: {' '.join(cmd[3:])}")
    try:
        subprocess.run(cmd, check=True, cwd=ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"ОШИБКА при генерации '{job['name']}': код {exc.returncode}", file=sys.stderr)
        raise SystemExit(1)


def merge_events() -> None:
    """Склеить два временных файла событий в один events.py."""
    labeling = PYDANTIC_DIR / "_events_labeling_tmp.py"
    cases = PYDANTIC_DIR / "_events_cases_tmp.py"
    target = PYDANTIC_DIR / "events.py"

    header = '''"""Сгенерированные модели событий брокера.

Источники:
- packages/contracts/events/reviews.labeling.v1.json
- packages/contracts/events/cases.events.v1.json

Регенерация: python -m scripts.generate_contracts
"""
from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, conint, constr


'''

    def strip_header(text: str) -> str:
        """Убрать шапку и импорты из сгенерированного файла."""
        lines = text.splitlines()
        # Пропускаем всё до первого 'class ' — там шапка, импорты, пустые строки
        idx = next(i for i, line in enumerate(lines) if line.startswith("class "))
        return "\n".join(lines[idx:]).strip() + "\n"

    body_labeling = strip_header(labeling.read_text(encoding="utf-8"))
    body_cases = strip_header(cases.read_text(encoding="utf-8"))

    merged = (
        header
        + "# ─── reviews.labeling.v1 ────────────────────────────────────────────\n\n"
        + body_labeling
        + "\n\n"
        + "# ─── cases.events.v1 ────────────────────────────────────────────────\n\n"
        + body_cases
    )

    target.write_text(merged, encoding="utf-8")
    labeling.unlink()
    cases.unlink()
    print(f"→ объединено в {target.relative_to(ROOT)}")


def fix_period_alias() -> None:
    """После генерации api.py проверить, что alias 'from' сохранён.

    Ничего не меняем, только предупреждаем, если поведение изменилось.
    """
    api_py = (PYDANTIC_DIR / "api.py").read_text(encoding="utf-8")
    if "alias='from'" not in api_py and 'alias="from"' not in api_py:
        print(
            "ПРЕДУПРЕЖДЕНИЕ: в api.py не найден alias='from' для поля Period.\n"
            "Проверьте, что в api.v1.yaml Period описан корректно.",
            file=sys.stderr,
        )


# ─── основной сценарий ────────────────────────────────────────────────

def main() -> int:
    if not (ROOT / "packages" / "contracts" / "openapi" / "api.v1.yaml").exists():
        print(
            "ОШИБКА: не найден packages/contracts/openapi/api.v1.yaml.\n"
            "Запускайте скрипт из корня репозитория.",
            file=sys.stderr,
        )
        return 1

    PYDANTIC_DIR.mkdir(parents=True, exist_ok=True)
    check_generator()

    for job in JOBS:
        run_generator(job)

    merge_events()
    fix_period_alias()

    print("\nГотово. Результат:")
    for path in sorted(PYDANTIC_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        size = path.stat().st_size
        print(f"  {path.relative_to(ROOT)}  ({size} байт)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())