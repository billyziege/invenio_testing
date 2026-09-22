#!/usr/bin/env python3
"""
Render acceptance_testing/requirements.csv as a Markdown table on stdout.

Usage:
    python3 render_table.py [CSV_PATH]

    CSV_PATH defaults to ../../docs/acceptance_testing/requirements.csv
    relative to this script's location.

    Pipe to a file or paste into the markdown document at the
    "Tests table" section placeholder.
"""

import csv
import sys
from pathlib import Path

_COLS = [
    "test_id",
    "req_id",
    "title",
    "test_type",
    "environment",
    "automation",
    "priority",
    "status",
    "notes",
]

_HEADERS = {
    "test_id":     "Test ID",
    "req_id":      "Requirement",
    "title":       "Title",
    "test_type":   "Type",
    "environment": "Environment",
    "automation":  "Automation",
    "priority":    "Priority",
    "status":      "Status",
    "notes":       "Notes",
}


def _cell(row: dict, col: str) -> str:
    val = row.get(col, "") or ""
    if col == "status":
        ref = (row.get("block_ref") or "").strip()
        if ref:
            return f"[{val}]({ref})"
    return val


def render(csv_path: Path) -> str:
    with csv_path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    headers = [_HEADERS[c] for c in _COLS]
    cells = [[_cell(r, c) for c in _COLS] for r in rows]

    widths = [len(h) for h in headers]
    for row in cells:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(val))

    def fmt(row):
        return "| " + " | ".join(v.ljust(w) for v, w in zip(row, widths)) + " |"

    sep = "| " + " | ".join("-" * w for w in widths) + " |"
    lines = [fmt(headers), sep] + [fmt(r) for r in cells]
    return "\n".join(lines)


def main():
    default = Path(__file__).parent / "../../docs/acceptance_testing/requirements.csv"
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    if not csv_path.exists():
        print(f"error: CSV not found: {csv_path.resolve()}", file=sys.stderr)
        sys.exit(1)
    print(render(csv_path.resolve()))


if __name__ == "__main__":
    main()
