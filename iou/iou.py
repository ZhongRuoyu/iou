import logging
import threading
from typing import TypedDict

import iou.database as db
from iou.config import (
  CURRENCY,
  DATABASE,
  TELEGRAM_BOT_TOKEN,
  TELEGRAM_CHAT_ID,
)
from iou.record import AggregatedRecord, Record
from iou.telegram import announce_record_status_change, announce_records
from iou.user import User

logger = logging.getLogger(__name__)

SummaryTransaction = TypedDict(
  "SummaryTransaction",
  {"from": str, "to": str, "amount": int},
)


def get_active_users() -> list[User]:
  """Return all active users."""
  return db.get_users(DATABASE, active_only=True)


def get_records() -> list[Record]:
  """Return all records."""
  return db.get_records(DATABASE)


def add_records(record: AggregatedRecord) -> None:
  """Create new records and trigger notifications."""

  records = record.to_records()
  db.add_records(DATABASE, records)
  logger.info(
    "Added %d record(s) of type %s by %s",
    len(records),
    record.type,
    record.created_by,
  )

  if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    users = get_active_users()

    threading.Thread(
      target=announce_records,
      args=(records, CURRENCY, users, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID),
      daemon=False,
    ).start()


def set_records_active(
  ids: list[int],
  *,
  active: bool,
  requester: str,
) -> None:
  """Activate or cancel records and trigger notifications."""

  db.set_records_active(DATABASE, ids, active=active)
  action = "activated" if active else "canceled"
  logger.info("%d records %s by %s", len(ids), action, requester)

  if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    records = [record for record in get_records() if record.id in set(ids)]
    users = db.get_users(DATABASE)
    threading.Thread(
      target=announce_record_status_change,
      args=(
        records,
        CURRENCY,
        users,
        requester,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
      ),
      kwargs={"active": active},
      daemon=False,
    ).start()


def get_summary() -> list[SummaryTransaction]:
  """Return a minimized transfer plan from current balances."""
  net_balances = db.get_net_balances(DATABASE)
  creditors = [
    (user, balance) for user, balance in net_balances.items() if balance > 0
  ]
  debtors = [
    (user, -balance) for user, balance in net_balances.items() if balance < 0
  ]
  creditors.sort(key=lambda x: x[1], reverse=True)
  debtors.sort(key=lambda x: x[1], reverse=True)

  transactions: list[SummaryTransaction] = []
  creditor_idx = 0
  debtor_idx = 0
  while creditor_idx < len(creditors) and debtor_idx < len(debtors):
    creditor_user, credit_amount = creditors[creditor_idx]
    debtor_user, debt_amount = debtors[debtor_idx]

    transfer_amount = min(credit_amount, debt_amount)
    if transfer_amount > 0:
      transactions.append(
        {"from": debtor_user, "to": creditor_user, "amount": transfer_amount}
      )
    creditors[creditor_idx] = (creditor_user, credit_amount - transfer_amount)
    debtors[debtor_idx] = (debtor_user, debt_amount - transfer_amount)

    if creditors[creditor_idx][1] == 0:
      creditor_idx += 1
    if debtors[debtor_idx][1] == 0:
      debtor_idx += 1

  return transactions
