"""Проверка, что все классы, упомянутые в components.csv, реально объявлены
в packages/contracts/pydantic/*.py и packages/contracts/typescript/src/*.ts.

Запуск из корня репозитория:
    python -m scripts.check_glossary
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent
DOCS_DIR = BASE_DIR / "docs"
CONTRACTS = DOCS_DIR / "packages" / "contracts"
GLOSSARY = DOCS_DIR / "glossary" / "components.csv"

PYDANTIC_FILES = [CONTRACTS / "pydantic" / "api.py", CONTRACTS / "pydantic" / "events.py"]
TS_FILES = [CONTRACTS / "typescript" / "src" / "api.ts", CONTRACTS / "typescript" / "src" / "events.ts"]

# Python: "class Foo(" или "class Foo:" или "class Foo(BaseModel):"
PY_CLASS_RE = re.compile(r"^class\s+(\w+)\b", re.MULTILINE)

# TS: "export interface Foo {" или "export type Foo ="
TS_DECL_RE = re.compile(r"^export\s+(?:interface|type)\s+(\w+)\b", re.MULTILINE)


def collect_names(paths: list[Path], pattern: re.Pattern[str]) -> set[str]:
    names: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        names.update(pattern.findall(text))
    return names


def main() -> int:
    if not GLOSSARY.exists():
        print(f"ОШИБКА: не найден {GLOSSARY}", file=sys.stderr)
        return 1

    py_names = collect_names(PYDANTIC_FILES, PY_CLASS_RE)
    ts_names = collect_names(TS_FILES, TS_DECL_RE)

    print(f"pydantic: {len(py_names)} классов — {sorted(py_names)}")
    print(f"typescript: {len(ts_names)} типов — {sorted(ts_names)}")
    print()

    missing: list[tuple[str, str, str]] = []  # (row_id, source, name)

    with GLOSSARY.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            cell = (row.get("l4_classes") or "").strip()
            if not cell:
                continue
            for item in cell.split(","):
                item = item.strip()
                if ":" not in item:
                    continue
                source, name = item.split(":", 1)
                source = source.strip()
                name = name.strip()
                if source == "pydantic" and name not in py_names:
                    missing.append((row["id"], source, name))
                elif source == "typescript" and name not in ts_names:
                    missing.append((row["id"], source, name))

    if missing:
        print("ОШИБКИ: следующие классы упомянуты в глоссарии, но не объявлены:", file=sys.stderr)
        for row_id, source, name in missing:
            print(f"  {row_id}: {source}:{name}", file=sys.stderr)
        return 1

    print(f"OK: все ссылки на pydantic/typescript в глоссарии валидны.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())