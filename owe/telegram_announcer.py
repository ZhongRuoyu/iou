from logging import Logger

import requests

from .record import Record
from .user import User

TELEGRAM_DEFAULT_SEND_TIMEOUT = 15


class TelegramAnnouncer:
  """Send Owe notifications to a Telegram chat."""

  bot_token: str
  chat_id: str
  currency: str
  logger: Logger | None
  send_timeout: int

  def __init__(
    self,
    *,
    bot_token: str,
    chat_id: str,
    currency: str,
    logger: Logger | None = None,
    send_timeout: int = TELEGRAM_DEFAULT_SEND_TIMEOUT,
  ) -> None:
    """Initialize the announcer with required Telegram settings."""
    self.bot_token = bot_token
    self.chat_id = chat_id
    self.currency = currency
    self.logger = logger
    self.send_timeout = send_timeout

  @staticmethod
  def try_get_user_name(email: str, users_by_email: dict[str, User]) -> str:
    """Resolve a user email to display name, falling back to the email."""
    if email in users_by_email:
      return users_by_email[email].name
    return email

  def record_message(
    self,
    record: Record,
    users_by_email: dict[str, User],
  ) -> str:
    """Format one record as a human-readable notification line."""
    lender = self.try_get_user_name(record.lender, users_by_email)
    borrower = self.try_get_user_name(record.borrower, users_by_email)
    amount = record.amount / 100
    message = (
      f"[{record.type}] {lender} -> {borrower}: {self.currency} {amount:.2f}"
    )
    if record.remarks:
      message += f" ({record.remarks})"
    return message

  def format_records(self, records: list[Record], users: list[User]) -> str:
    """Format grouped new-record notifications for Telegram."""
    users_by_email = {user.email: user for user in users}

    records_by_creator: dict[str, list[Record]] = {}
    for record in records:
      records_by_creator.setdefault(record.created_by, []).append(record)
    records_by_creator = dict(sorted(records_by_creator.items()))

    messages = []
    for creator, creator_records in records_by_creator.items():
      creator_name = self.try_get_user_name(creator, users_by_email)
      record_count = len(creator_records)
      records_word = "record" if record_count == 1 else "records"
      message = (
        f"{record_count} new Owe {records_word} added by {creator_name}:\n"
      )
      for record in creator_records:
        message += f"- {self.record_message(record, users_by_email)}\n"
      messages.append(message)
    return "\n\n".join(messages)

  def format_record_status_change(
    self,
    records: list[Record],
    users: list[User],
    requester: str,
    *,
    active: bool,
  ) -> str:
    """Format record status update notifications for Telegram."""
    users_by_email = {user.email: user for user in users}

    requester_name = self.try_get_user_name(requester, users_by_email)
    record_count = len(records)
    records_word = "record" if record_count == 1 else "records"
    action = "activated" if active else "canceled"
    message = (
      f"{record_count} Owe {records_word} {action} by {requester_name}:\n"
    )
    for record in records:
      message += f"- {self.record_message(record, users_by_email)}\n"
    return message

  def post_message(self, message: str) -> None:
    """Send a message to a Telegram chat and log failures."""
    try:
      response = requests.post(
        f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
        json={"chat_id": self.chat_id, "text": message},
        timeout=self.send_timeout,
      )
      response.raise_for_status()
    except requests.RequestException:
      if self.logger:
        self.logger.exception("Telegram notification failed")

  def announce_records(self, records: list[Record], users: list[User]) -> None:
    """Build and send a new-record announcement to Telegram."""
    self.post_message(self.format_records(records, users))

  def announce_record_status_change(
    self,
    records: list[Record],
    users: list[User],
    requester: str,
    *,
    active: bool,
  ) -> None:
    """Build and send a record-status announcement to Telegram."""
    self.post_message(
      self.format_record_status_change(
        records,
        users,
        requester,
        active=active,
      )
    )
