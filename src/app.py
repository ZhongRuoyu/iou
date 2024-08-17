import csv
from datetime import datetime
from itertools import combinations, permutations
import os
import subprocess
from textwrap import dedent
from collections import namedtuple

from flask import Flask, request
from flask_cors import CORS
import sqlite3

from dotenv import load_dotenv

Record = namedtuple("Record", [
    "type",
    "lender",
    "borrower",
    "amount",
    "created_by",
    "created_at",
    "remarks",
])

load_dotenv()

DATABASE = os.getenv("DATABASE", "iou.db")
BILLING_REPO = os.getenv("BILLING_REPO", None)


def init():
  with sqlite3.connect(DATABASE) as con:
    con.cursor().execute(
        dedent("""
          CREATE TABLE IF NOT EXISTS Users(
            name TEXT PRIMARY KEY
          );
        """)).execute(
            dedent("""
              CREATE TABLE IF NOT EXISTS Records(
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                type       TEXT NOT NULL,
                lender     TEXT NOT NULL,
                borrower   TEXT NOT NULL,
                amount     INTEGER NOT NULL,
                created_by TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                remarks    TEXT,
                active     BOOLEAN DEFAULT TRUE,
                FOREIGN KEY(lender) REFERENCES Users(name),
                FOREIGN KEY(borrower) REFERENCES Users(name),
                FOREIGN KEY(created_by) REFERENCES Users(name),
                CHECK(lender != borrower),
                CHECK(amount > 0)
              );
            """))


init()
app = Flask(__name__)
CORS(app)


def dict_factory(cursor, row):
  return dict(zip(list(column[0] for column in cursor.description), row))


def ceildiv(a, b):
  return -(a // -b)


@app.route("/users")
def get_users():
  with sqlite3.connect(DATABASE) as con:
    con.row_factory = dict_factory
    return con.cursor().execute("SELECT * FROM Users;").fetchall()


@app.route("/records")
def get_records():
  with sqlite3.connect(DATABASE) as con:
    con.row_factory = dict_factory
    records = con.cursor().execute("SELECT * FROM Records;").fetchall()
    return {record["id"]: record for record in records}


@app.route("/summary")
def summary():
  with sqlite3.connect(DATABASE) as con:
    con.row_factory = dict_factory

    users = con.cursor().execute("SELECT * FROM Users;").fetchall()
    payment = {
        pair: 0
        for pair in permutations(list(user["name"] for user in users), 2)
    }

    records = con.cursor().execute(
        dedent("""
          SELECT * FROM Records
          WHERE active = TRUE;
        """)).fetchall()
    for record in records:
      pair = (record["borrower"], record["lender"])
      payment[pair] += record["amount"]

    for pair in combinations(list(user["name"] for user in users), 2):
      reverse_pair = (pair[1], pair[0])
      if payment[pair] < payment[reverse_pair]:
        pair, reverse_pair = reverse_pair, pair
      payment[pair] -= payment[reverse_pair]
      payment.pop(reverse_pair)
      if payment[pair] == 0:
        payment.pop(pair)

    return [{
        "from": pair[0],
        "to": pair[1],
        "amount": amount
    } for pair, amount in payment.items()]


@app.route("/record", methods=["POST"])
def new_record():
  req = request.get_json()
  for key in ["type", "lender", "borrowers", "amount", "created_by", "remarks"]:
    if key not in req:
      return {"success": False, "error": f"Missing field: {key}"}, 400

  record_type = req["type"]
  lender = req["lender"]
  borrowers = req["borrowers"]
  amount = req["amount"]
  created_by = req["created_by"]
  created_at = int(datetime.now().timestamp() * 1000)
  remarks = req["remarks"]
  amount_per_borrower = ceildiv(amount, len(borrowers))
  records = [
      Record(
          record_type,
          lender,
          borrower,
          amount_per_borrower,
          created_by,
          created_at,
          remarks,
      ) for borrower in borrowers if borrower != lender
  ]

  with sqlite3.connect(DATABASE) as con:
    con.row_factory = dict_factory
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = ON;").executemany(
        dedent("""
          INSERT INTO Records(
            type,
            lender,
            borrower,
            amount,
            created_by,
            created_at,
            remarks)
          VALUES(?, ?, ?, ?, ?, ?, ?);
        """), records)
    con.commit()

  if BILLING_REPO is not None:
    subprocess.run(["git", "fetch", "origin", "main"],
                   cwd=BILLING_REPO,
                   check=True)
    subprocess.run(["git", "reset", "--hard", "origin/main"],
                   cwd=BILLING_REPO,
                   check=True)
    for record in records:
      borrower = record.borrower
      lender = record.lender
      amount = record.amount / 100
      remarks = record.remarks
      message = f"{lender} -> {borrower}: ${amount:.2f}"
      if remarks:
        message += f" ({remarks})"
      with open(
          f"{BILLING_REPO}/records.csv", "a", encoding="utf-8",
          newline="") as csv_file:
        csv.writer(csv_file).writerow(record)
      subprocess.run(["git", "add", "records.csv"],
                     cwd=BILLING_REPO,
                     check=True)
      subprocess.run(["git", "commit", "-m", message],
                     cwd=BILLING_REPO,
                     check=True)
    subprocess.run(["git", "push", "origin"], cwd=BILLING_REPO, check=True)

  return {"success": True}
