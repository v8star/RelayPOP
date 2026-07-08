import smtplib

from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
from email.utils import parseaddr


def _connect(profile):

    security = (
        profile.get("security")
        or "none"
    ).lower()

    host = profile["host"]
    port = int(profile.get("port", 25))

    if security == "ssl":

        server = smtplib.SMTP_SSL(
            host,
            port,
            timeout=30
        )

    else:

        server = smtplib.SMTP(
            host,
            port,
            timeout=30
        )

        server.ehlo()

        if security == "starttls":

            server.starttls()
            server.ehlo()

    username = profile.get("username")
    password = profile.get("password")

    if username:

        server.login(
            username,
            password or ""
        )

    return server

# =========================================================
# DELIVERY
# =========================================================

def deliver(raw, profile, account):

    msg = BytesParser(
        policy=policy.default
    ).parsebytes(raw)

    server = _connect(profile)

    recipient = account["pop3"]["username"]

    sender = (
        parseaddr(msg.get("Return-Path", ""))[1]
        or parseaddr(msg.get("Sender", ""))[1]
        or parseaddr(msg.get("From", ""))[1]
        or ""
    )

    response = server.sendmail(
        sender,
        [recipient],
        raw
    )

    server.quit()

    return len(response) == 0

# =========================================================
# TEST CONNECTION
# =========================================================

def test_connection(profile):

    try:

        server = _connect(profile)

        server.quit()

        return True, "Connection OK"

    except Exception as e:

        return False, str(e)


# =========================================================
# TEST SMTP SETTINGS
# =========================================================

def send_test_mail(profile):

    try:

        sender = profile.get("username")

        if not sender or "@" not in sender:

            return (
                False,
                "SMTP username must be a valid email address"
            )

        msg = EmailMessage()

        msg["From"] = sender
        msg["To"] = sender

        msg["Subject"] = "RelayPOP Test Message"

        msg.set_content(
            f"""
SMTP server validated!

This message was generated automatically by RelayPOP.

Profile: {profile.get('name')}
Host: {profile.get('host')}
Port: {profile.get('port')}
Security: {profile.get('security')}
"""
        )

        security = (
            profile.get("security", "none")
            .lower()
            .strip()
        )

        if security == "ssl":

            server = smtplib.SMTP_SSL(
                profile["host"],
                int(profile.get("port", 465)),
                timeout=15
            )

        else:

            server = smtplib.SMTP(
                profile["host"],
                int(profile.get("port", 25)),
                timeout=15
            )

            server.ehlo()

            if security == "starttls":

                server.starttls()
                server.ehlo()

        if profile.get("username"):

            server.login(
                profile["username"],
                profile.get("password", "")
            )

        server.send_message(msg)

        server.quit()

        return (
            True,
            f"Test mail sent to {sender}"
        )

    except Exception as e:

        return (
            False,
            str(e)
        )