from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from typing import Optional

from ovos_utils.log import LOG


def send_smtp(
    user: str,
    pswd: str,
    sender: str,
    destinatary: str,
    subject: str,
    contents: str,
    host: str,
    port: int = 465,
) -> None:
    """Send an e-mail via SMTP over SSL.

    Args:
        user: SMTP login username.
        pswd: SMTP login password.
        sender: From address shown in the message.
        destinatary: Recipient e-mail address.
        subject: Message subject line.
        contents: Plain-text message body.
        host: SMTP server hostname.
        port: SMTP server port (default 465).
    """
    with SMTP_SSL(host=host, port=port) as server:
        server.login(user, pswd)
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = destinatary
        msg['Subject'] = subject
        msg.attach(MIMEText(contents))
        server.sendmail(sender, destinatary, msg.as_string())


def send_email(subject: str, body: str, recipient: Optional[str] = None) -> None:
    """Send an e-mail using SMTP settings from the OVOS configuration.

    Args:
        subject: Message subject line.
        body: Plain-text message body.
        recipient: Recipient address; falls back to the configured recipient or
            the SMTP username when not provided.

    Raises:
        KeyError: When the email configuration section is missing.
    """
    try:
        from ovos_config.config import read_mycroft_config
        config = read_mycroft_config()
    except ImportError:
        LOG.warning("Config not provided and ovos_config not available")
        config = dict()
    mail_config = config.get("email") or {}
    if not mail_config:
        raise KeyError("email configuration not set")

    smtp_config = mail_config["smtp"]
    user = smtp_config["username"]
    pswd = smtp_config["password"]
    host = smtp_config["host"]
    port = smtp_config.get("port", 465)

    recipient = recipient or mail_config.get("recipient") or user

    send_smtp(user, pswd,
              user, recipient,
              subject, body,
              host, port)
