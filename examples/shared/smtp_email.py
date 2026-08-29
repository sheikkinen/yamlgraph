"""Shared SMTP email tool (FR-907, CAP-252).

Transport only: it accepts already-rendered strings and has no opinion
about what it carries. Rendering, templating, and subject construction
belong to the caller.

Contract: send_email(subject, text, html=None, to=None, cc=None,
attachments=None) -> {"sent": True, "to": [...]}. Configuration comes
from SMTP_SERVER/SMTP_PORT/SMTP_USER/SMTP_PASSWORD, with optional
SMTP_FROM and SMTP_TO. Every missing key is reported in one error before
a socket is opened; credentials are read at call time, never at import.
CR/LF in any header value is refused. Every failure raises -- there is no
success-shaped return on any path, so an unattended caller cannot report
green while delivering nothing.
"""

from __future__ import annotations

import logging
import mimetypes
import os
import smtplib
from collections.abc import Callable
from email.message import EmailMessage
from pathlib import Path

logger = logging.getLogger(__name__)

REQUIRED_ENV = ("SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD")
IMPLICIT_TLS_PORT = 465
TIMEOUT_SECONDS = 30


class SmtpSendError(RuntimeError):
    """Email could not be sent. Never carries credentials."""


def _load_config() -> dict[str, str]:
    config = {key: os.environ.get(key, "") for key in REQUIRED_ENV}
    missing = [key for key, value in config.items() if not value]
    if missing:
        raise SmtpSendError(f"missing SMTP configuration: {', '.join(missing)}")
    try:
        int(config["SMTP_PORT"])
    except ValueError:
        raise SmtpSendError(
            f"SMTP_PORT is not a number: {config['SMTP_PORT']!r}"
        ) from None
    return config


def _split_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    return [address.strip() for address in value.split(",") if address.strip()]


def _reject_line_breaks(field: str, value: str) -> None:
    if "\n" in value or "\r" in value:
        raise SmtpSendError(f"{field} contains a line break; refusing header injection")


def _attach(message: EmailMessage, paths: list[str]) -> None:
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise SmtpSendError(f"attachment not found: {raw_path}")
        mime_type, _ = mimetypes.guess_type(path.name)
        maintype, _, subtype = (mime_type or "application/octet-stream").partition("/")
        message.add_attachment(
            path.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )


def _build_message(
    subject: str,
    text: str,
    html: str | None,
    sender: str,
    to_addresses: list[str],
    cc_addresses: list[str],
    attachments: list[str],
) -> EmailMessage:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = ", ".join(to_addresses)
    if cc_addresses:
        message["Cc"] = ", ".join(cc_addresses)
    message.set_content(text)
    if html is not None:
        message.add_alternative(html, subtype="html")
    if attachments:
        _attach(message, attachments)
    return message


def send_email(
    subject: str,
    text: str,
    html: str | None = None,
    to: str | None = None,
    cc: str | None = None,
    attachments: list[str] | None = None,
    *,
    smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP,
    smtp_ssl_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP_SSL,
) -> dict:
    """Send one email over SMTP.

    The two factories are the test seam; graph callers pass only the
    documented positional arguments.
    """
    config = _load_config()

    to_addresses = _split_addresses(to) or _split_addresses(os.environ.get("SMTP_TO"))
    if not to_addresses:
        raise SmtpSendError("no recipient: pass 'to' or set SMTP_TO")
    cc_addresses = _split_addresses(cc)

    _reject_line_breaks("subject", subject)
    for address in (*to_addresses, *cc_addresses):
        _reject_line_breaks("recipient", address)

    sender = os.environ.get("SMTP_FROM") or config["SMTP_USER"]
    message = _build_message(
        subject, text, html, sender, to_addresses, cc_addresses, attachments or []
    )

    host = config["SMTP_SERVER"]
    port = int(config["SMTP_PORT"])
    recipients = [*to_addresses, *cc_addresses]

    try:
        if port == IMPLICIT_TLS_PORT:
            with smtp_ssl_factory(host, port, timeout=TIMEOUT_SECONDS) as client:
                client.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
                client.send_message(message)
        else:
            with smtp_factory(host, port, timeout=TIMEOUT_SECONDS) as client:
                client.starttls()
                client.login(config["SMTP_USER"], config["SMTP_PASSWORD"])
                client.send_message(message)
    except Exception as exc:
        # `from None`: a chained SMTPAuthenticationError echoes the credential back.
        raise SmtpSendError(
            f"SMTP send failed via {host}:{port} to {', '.join(recipients)} "
            f"({type(exc).__name__})"
        ) from None

    logger.info("📬 Sent %r to %s", subject, ", ".join(recipients))
    return {"sent": True, "to": recipients}
