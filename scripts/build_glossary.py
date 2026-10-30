import csv
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parent

CSV_PATH = BASE_DIR / "docs" / "glossary" / "components.csv"
MD_PATH  = BASE_DIR / "docs" / "glossary" / "components.md"


def load(path: Path = CSV_PATH) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def validate(rows: list[dict]) -> None:
    ids = [r["id"] for r in rows]
    dupes = [i for i, c in Counter(ids).items() if c > 1]
    if dupes:
        raise ValueError(f"Дубли ID: {dupes}")
    for r in rows:
        if r["container_id"] not in {"api_backend", "message_broker", "labeling_worker",
                                     "background_worker", "web_panel", "mobile_app", "shared"}:
            raise ValueError(f"Неизвестный контейнер: {r['container_id']} в {r['id']}")


def print_summary(rows: list[dict]) -> None:
    """Сводка в консоль: по контейнерам, видам и общий счётчик."""
    print(f"Всего позиций: {len(rows)}\n")

    print("По контейнерам:")
    for container, count in Counter(r["container"] for r in rows).most_common():
        print(f"  {container:<20} {count}")

    print("\nПо видам (kind):")
    for kind, count in Counter(r["kind"] for r in rows).most_common():
        print(f"  {kind:<20} {count}")

    print("\nПо контейнерам (container_id):")
    for cid, count in Counter(r["container_id"] for r in rows).most_common():
        print(f"  {cid:<20} {count}")


def to_markdown(rows: list[dict]) -> str:
    lines = ["| ID | Название | Вид | Контейнер | Назначение |",
             "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| `{r['id']}` | {r['name']} | {r['kind']} | {r['container']} | {r['purpose']} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    rows = load()
    validate(rows)
    print_summary(rows)
    MD_PATH.write_text(to_markdown(rows), encoding="utf-8")
    print(f"\nЗаписано: {MD_PATH.relative_to(BASE_DIR)}")