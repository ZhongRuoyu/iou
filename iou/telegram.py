from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from iou.record import Record

import requests


def format_records(records: list[Record], currency: str) -> str:
  records_by_creator: dict[str, list[Record]] = {}
  for record in records:
    records_by_creator.setdefault(record.created_by, []).append(record)
  records_by_creator = dict(sorted(records_by_creator.items()))

  messages = []
  for creator, creator_records in records_by_creator.items():
    record_count = len(creator_records)
    records_word = "record" if record_count == 1 else "records"
    message = f"{record_count} new IOU {records_word} added by {creator}:\n"
    for record in creator_records:
      message += f"- {record.message(currency)}\n"
    messages.append(message)
  return "\n\n".join(messages)


def announce_records(
  records: list[Record],
  currency: str,
  bot_token: str,
  chat_id: str,
) -> None:
  message = format_records(records, currency)
  requests.post(
    f"https://api.telegram.org/bot{bot_token}/sendMessage",
    json={"chat_id": chat_id, "text": message},
    timeout=10,
  )
