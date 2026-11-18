"""Outgoing email. MAIL_DRIVER=log (local/testing) or smtp (production)."""

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from typing import ClassVar, Protocol

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Mail:
    to: str
    subject: str
    body: str


class Mailer(Protocol):
    def send(self, mail: Mail) -> None: ...


class LogMailer:
    """Writes emails to the log instead of sending them. Keeps an outbox for tests."""

    outbox: ClassVar[list[Mail]] = []

    def send(self, mail: Mail) -> None:
        self.outbox.append(mail)
        logger.info("Email to %s: %s\n%s", mail.to, mail.subject, mail.body)


class SmtpMailer:
    def send(self, mail: Mail) -> None:
        settings = get_settings()
        message = EmailMessage()
        message["From"] = formataddr((settings.mail_from_name, settings.mail_from_address))
        message["To"] = mail.to
        message["Subject"] = mail.subject
        message.set_content(mail.body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_username and settings.smtp_password:
                smtp.login(settings.smtp_username, settings.smtp_password.get_secret_value())
            smtp.send_message(message)


def get_mailer() -> Mailer:
    return SmtpMailer() if get_settings().mail_driver == "smtp" else LogMailer()


def send_safely(mailer: Mailer, mail: Mail) -> None:
    """Background-task wrapper: a mail server problem must never crash the request that queued it."""
    try:
        mailer.send(mail)
    except Exception:
        logger.exception("Could not send email to %s", mail.to)
