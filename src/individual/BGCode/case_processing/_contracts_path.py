"""Добавляет docs/ в sys.path, чтобы импортировался пакет контрактов packages.contracts.pydantic.

В CI вместо этого задаётся PYTHONPATH=docs; здесь путь вычисляется от расположения файла.
"""

from __future__ import annotations

import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[4] / "docs"
if (DOCS_DIR / "packages").is_dir() and str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))
