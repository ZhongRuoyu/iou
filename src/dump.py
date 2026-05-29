"""Script to dump all records from the database to a CSV file."""

import csv
import os
import sqlite3
import sys
from pathlib import Path

from app import DATABASE, Record, dict_factory

RECORDS = os.getenv("RECORDS", "records.csv")


def get_records(database: Path) -> list[Record]:
  with sqlite3.connect(database) as con:
    con.row_factory = dict_factory
    cur = con.cursor()
    rows = cur.execute("SELECT * FROM Records ORDER BY id;").fetchall()
    if not rows:
      return []
    return [Record.from_db_row(row) for row in rows]


def main() -> int:
  database = Path(DATABASE)
  output = Path(RECORDS)

  if not database.exists():
    print(f"Error: Database file {DATABASE} not found")
    return 1

  records = get_records(database)
  if not records:
    print("No records to dump")
    return 0

  print(f"Dumping {len(records)} records to {output}...")

  with output.open("w", encoding="utf-8", newline="") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(Record.csv_header())
    for record in records:
      writer.writerow(record.to_csv_row())

  print(f"Successfully dumped {len(records)} records to {output}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
