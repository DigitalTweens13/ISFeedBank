#!/usr/bin/env python3
"""
Валидатор использования глоссария в C4-диаграммах ISFeedBank.

Проверяет, что в диаграммах L0, L1, L2, deployment и dynamic алиасы
элементов C4 передаются через переменные глоссария ($ID_...), а не
голыми строками.

Не проверяет:
  - L3 (Component): локальные ID компонентов, не входят в глоссарий;
  - L4 (class diagram): имена классов, не ID элементов C4.

Уровень проверки: предупреждение (return code 0). Рендер продолжается.
"""
import re
import sys
from pathlib import Path

# Директории с диаграммами
COMMON_DIR = Path("src")
INDIVIDUAL_DIR = Path("src/individual")

# Какие файлы считаются проверяемыми (по суффиксу имени).
# L3 (_l3) и L4 (_l4) исключены намеренно.
CHECKABLE_SUFFIXES = (
    "_landscape_l0",
    "_context_l1",
    "_containers_l2",
    "_deployment",
    "_dynamic",
)

# Макросы C4, у которых первый аргумент — алиас элемента.
# Включаем только те, что создают элементы (не Rel/BiRel).
ELEMENT_MACROS = (
    "Person",
    "Person_Ext",
    "System",
    "System_Ext",
    "SystemDb",
    "SystemDb_Ext",
    "Container",
    "ContainerDb",
    "Container_Boundary",
    "Component",
    "ComponentDb",
    "Deployment_Node",
    "Node",
    "Enterprise_Boundary",
    "System_Boundary",
)

# Регулярка: MACRO(  <первый аргумент до запятой или закрывающей скобки>
MACRO_CALL_RE = re.compile(
    r'\b(' + '|'.join(ELEMENT_MACROS) + r')\s*\(\s*([^,)\s]+)'
)

# Признак «это переменная глоссария»
GLOSSARY_VAR_RE = re.compile(r'^\$ID_[A-Z0-9_]+$')

# Признак «это локальный алиас, разрешённый в L3/L4» (не используется здесь,
# но полезно для будущего расширения)


def is_checkable(path: Path) -> bool:
    """Проверяем только L0/L1/L2/deployment/dynamic."""
    stem = path.stem.lower()
    return any(stem.endswith(sfx) or sfx in stem for sfx in CHECKABLE_SUFFIXES)


def check_file(path: Path) -> list[str]:
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Пропускаем комментарии
        if stripped.startswith("'"):
            continue

        for m in MACRO_CALL_RE.finditer(line):
            macro = m.group(1)
            alias = m.group(2).strip()

            # Алиас уже переменная глоссария — ок
            if GLOSSARY_VAR_RE.match(alias):
                continue

            # Алиас в кавычках — это строка, а не переменная; тоже предупреждение
            if alias.startswith('"') or alias.startswith("'"):
                warnings.append(
                    f"{path}:{lineno}: {macro}({alias}, ...) — алиас задан строкой. "
                    f"Используйте переменную глоссария, например ${suggest_var(macro)}."
                )
                continue

            warnings.append(
                f"{path}:{lineno}: {macro}({alias}, ...) — алиас не из глоссария. "
                f"Используйте переменную $ID_... из glossary.puml "
                f"(например ${suggest_var(macro)})."
            )

    return warnings


def suggest_var(macro: str) -> str:
    """Подсказка: какой переменной, скорее всего, хотели воспользоваться."""
    if macro.startswith("Person"):
        return "ID_CX_ANALYST"
    if macro.startswith("Deployment_Node") or macro == "Node":
        return "ID_DN_API"
    if macro.startswith("Container"):
        return "ID_API_BACKEND"
    if macro.startswith("Component"):
        return "ID_LW_TASK_CONSUMER"
    if macro.startswith("System_Ext"):
        return "ID_BANK_IAM"
    if macro.startswith("System"):
        return "ID_FEEDBACK_SYSTEM"
    return "ID_..."


def main() -> int:
    all_warnings: list[str] = []
    files: list[Path] = []

    for root in (COMMON_DIR, INDIVIDUAL_DIR):
        if root.exists():
            for f in root.rglob("*.puml"):
                if is_checkable(f):
                    files.append(f)

    if not files:
        print("Не найдено проверяемых .puml (L0/L1/L2/deployment/dynamic).")
        return 0

    for f in files:
        all_warnings.extend(check_file(f))

    # Аннотации в GitHub Actions
    for w in all_warnings:
        print(f"::warning::{w}")

    if all_warnings:
        print("\nПРЕДУПРЕЖДЕНИЯ (рендер продолжится):\n")
        for w in all_warnings:
            print(f"  - {w}")
        print()

    print(
        f"Проверено файлов: {len(files)}. "
        f"Предупреждений: {len(all_warnings)}."
    )

    # Всегда 0: это предупреждения, не ошибки
    return 0


if __name__ == "__main__":
    sys.exit(main())