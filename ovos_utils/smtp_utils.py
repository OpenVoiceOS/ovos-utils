from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from ovos_utils.log import LOG


def send_smtp(user, pswd, sender,
              destinatary, subject, contents,
              host, port=465):
    with SMTP_SSL(host=host, port=port) as server:
        server.login(user, pswd)
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = destinatary
        msg['Subject'] = subject
        msg.attach(MIMEText(contents))
        server.sendmail(sender, destinatary, msg.as_string())


def send_email(subject, body, recipient=None):
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
