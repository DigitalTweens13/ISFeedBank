#!/usr/bin/env python3
"""
Валидатор правил оформления .puml для проекта ISFeedBank.

Уровни проверок:
  ОШИБКИ (return code 1, job падает):
    - отсутствие @startuml / @enduml;
    - запрещённые направленные макросы Rel_D, Rel_U, Rel_L, Rel_R.
  ПРЕДУПРЕЖДЕНИЯ (return code 0, job продолжается):
    - skinparam в индивидуальных файлах (стили не вынесены);
    - Rel() без протокола (нет второго строкового аргумента).
"""
import os
import re
import sys
from pathlib import Path

INDIVIDUAL_DIR = Path("src/individual")

FORBIDDEN_REL_PATTERN = re.compile(r'\bRel_[DULR]\s*\(')
SKINPARAM_PATTERN = re.compile(r'^\s*skinparam\b', re.IGNORECASE)
REL_PATTERN = re.compile(r'\bRel\s*\(([^)]*)\)')
ANNOTATION_RE = re.compile(r'^(.+?):(\d+): (.+)$')


def split_rel_args(args: str) -> list[str]:
    result = []
    current = []
    in_quote = False
    quote_char = ""
    for ch in args:
        if in_quote:
            current.append(ch)
            if ch == quote_char:
                in_quote = False
        elif ch in ('"', "'"):
            in_quote = True
            quote_char = ch
            current.append(ch)
        elif ch == ",":
            result.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        result.append("".join(current).strip())
    return result


def format_rel_call(rel_args: list[str]) -> str:
    parts = []
    for i, arg in enumerate(rel_args):
        if i < 2:
            parts.append(arg)
        else:
            if not (arg.startswith('"') or arg.startswith("'")):
                parts.append(f'"{arg}"')
            else:
                parts.append(arg)
    return f"Rel({', '.join(parts)})"


def emit_annotation(level: str, msg: str) -> None:
    """
    Печатает workflow command с привязкой к файлу и строке,
    если сообщение имеет формат 'путь:строка: текст'.
    Иначе печатает без привязки.
    """
    m = ANNOTATION_RE.match(msg)
    if m:
        path, line, text = m.group(1), m.group(2), m.group(3)
        # Экранируем спецсимволы workflow commands
        text = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::{level} file={path},line={line},title=.puml validation::{text}")
    else:
        text = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::{level}::{text}")


def check_file(path: Path, is_individual: bool) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    if "@startuml" not in text:
        errors.append(f"{path}: отсутствует @startuml")
    if "@enduml" not in text:
        errors.append(f"{path}: отсутствует @enduml")

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        if FORBIDDEN_REL_PATTERN.search(line):
            errors.append(
                f"{path}:{lineno}: запрещён направленный макрос Rel_*. "
                f"Используйте только Rel()."
            )

        if is_individual and SKINPARAM_PATTERN.match(stripped):
            warnings.append(
                f"{path}:{lineno}: skinparam в индивидуальной диаграмме. "
                f"Стили вынесите в общий файл."
            )

        for m in REL_PATTERN.finditer(line):
            args_str = m.group(1)
            rel_args = split_rel_args(args_str)
            str_args = re.findall(r'["\']([^"\']*)["\']', args_str)
            if len(str_args) < 2 or not str_args[1].strip():
                call_repr = format_rel_call(rel_args)
                warnings.append(
                    f"{path}:{lineno}: {call_repr} — нет протокола. "
                    f"Укажите вторым аргументом, например: "
                    f'Rel(a, b, "вызов", "HTTPS/JSON").'
                )

    return errors, warnings


def write_summary(errors: list[str], warnings: list[str]) -> None:
    """Пишет markdown в GITHUB_STEP_SUMMARY, если переменная задана."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = ["## Валидация .puml\n"]
    if errors:
        lines.append(f"### Ошибки ({len(errors)})\n")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")
    if warnings:
        lines.append(f"### Предупреждения ({len(warnings)})\n")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    if not errors and not warnings:
        lines.append("Нарушений нет.\n")

    Path(summary_path).write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    all_errors: list[str] = []
    all_warnings: list[str] = []
    files = list(INDIVIDUAL_DIR.rglob("*.puml")) if INDIVIDUAL_DIR.exists() else []

    if not files:
        print(f"В {INDIVIDUAL_DIR}/ не найдено .puml файлов. Проверка пропущена.")
        return 0

    for f in files:
        errs, warns = check_file(f, is_individual=True)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    for e in all_errors:
        emit_annotation("error", e)
    for w in all_warnings:
        emit_annotation("warning", w)

    if all_errors:
        print("\nОШИБКИ (критические):\n")
        for e in all_errors:
            print(f"  - {e}")
        print()

    if all_warnings:
        print("ПРЕДУПРЕЖДЕНИЯ (рендер продолжится):\n")
        for w in all_warnings:
            print(f"  - {w}")
        print()

    print(
        f"Проверено файлов: {len(files)}. "
        f"Ошибок: {len(all_errors)}, предупреждений: {len(all_warnings)}."
    )

    write_summary(all_errors, all_warnings)

    return 1 if all_errors else 0


if __name__ == "__main__":
    sys.exit(main())