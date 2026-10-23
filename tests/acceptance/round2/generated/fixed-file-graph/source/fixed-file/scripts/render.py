#!/usr/bin/env python3
"""Compute the summary write plan from a CSV and the summary template.

Reads the CSV and the template, prints one JSON plan to stdout and writes no file.
"""
import argparse
import csv
import io
import json
from pathlib import Path
import re
import sys

REQUIRED_COLUMNS = ("name", "count")
TEMPLATE_PATH = "templates/summary.txt"
INTEGER = re.compile(r"^[0-9]+$")
PLACEHOLDER = re.compile(r"\{[^{}]*\}")

EXIT_ARGUMENT = 2
EXIT_CSV = 3
EXIT_TEMPLATE = 4
EXIT_IO = 5


class Failure(Exception):
    def __init__(self, status, code, detail, path=None):
        super().__init__(detail)
        self.status = status
        self.error = {"code": code, "path": str(path) if path is not None else None,
                      "detail": str(detail)}


def read_text(path, status, code):
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise Failure(status, code, f"file is not UTF-8: {exc}", path)
    except OSError as exc:
        raise Failure(EXIT_IO, "io-error", str(exc), path)


def parse_csv(path):
    text = read_text(path, EXIT_CSV, "invalid-csv")
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        raise Failure(EXIT_CSV, "invalid-csv", "CSV has no header row", path)
    header = [column.strip() for column in header]
    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise Failure(EXIT_CSV, "invalid-csv",
                      "missing required column(s): " + ", ".join(missing), path)
    count_index = header.index("count")
    rows = 0
    total = 0
    for number, record in enumerate(reader, start=2):
        if not record or all(cell.strip() == "" for cell in record):
            continue
        if count_index >= len(record):
            raise Failure(EXIT_CSV, "invalid-csv",
                          f"row {number} has no count value", path)
        value = record[count_index].strip()
        if not INTEGER.match(value):
            raise Failure(EXIT_CSV, "invalid-csv",
                          f"row {number} count is not a non-negative integer: {value!r}", path)
        rows += 1
        total += int(value)
    return rows, total


def render_template(path, total):
    text = read_text(path, EXIT_TEMPLATE, "invalid-template")
    content = text.replace("{total}", str(total))
    leftover = PLACEHOLDER.search(content)
    if leftover:
        raise Failure(EXIT_TEMPLATE, "invalid-template",
                      f"unsupported placeholder {leftover.group(0)!r}; only {{total}} is supported", path)
    return content


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print the JSON write plan for a CSV and the summary template. Writes no file.")
    parser.add_argument("source_csv", help="UTF-8 CSV file with name and count columns")
    parser.add_argument("--template", default=None,
                        help=f"template file (default: {TEMPLATE_PATH} next to this script)")
    args = parser.parse_args(argv)
    template = args.template or str(Path(__file__).resolve().parent.parent / TEMPLATE_PATH)
    try:
        rows, total = parse_csv(args.source_csv)
        content = render_template(template, total)
    except Failure as exc:
        print(json.dumps({"status": "error", "error": exc.error}, ensure_ascii=False))
        return exc.status
    print(json.dumps({"status": "ok", "rows": rows, "total": total,
                      "content": content, "template": args.template or TEMPLATE_PATH},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

