import logging
from datetime import datetime
from email import policy
from email.parser import BytesParser

import database
import pop3
import smtp
import settings


def poll_account(account):

    name = account["name"]

    retention = int(
        account.get("retention_days") or 7
    )

    try:

        mailbox = pop3.connect(account)

        database.log_event(
            name,
            "INFO",
            "POP3",
            "connected"
        )

        logging.info(
            "[%s] POP3 connected",
            name
        )

        uid_map = pop3.get_uid_map(mailbox)

        for number, uid in pop3.list_uid(mailbox):

            if database.already_delivered(
                name,
                uid
            ):
                continue

            raw = pop3.get_message(
                mailbox,
                number
            )

            msg = BytesParser(
                policy=policy.default
            ).parsebytes(raw)

            # ==========================================
            # SMTP PROFILE
            # ==========================================
            profile_name = account.get(
                "smtp_profile"
            )

            smtp_cfg = settings.load_smtp_profile(
                profile_name
            )

            if not smtp_cfg:

                database.log_event(
                    name,
                    "ERROR",
                    "SMTP",
                    f"missing smtp_profile: {profile_name}"
                )

                continue

            ok = smtp.deliver(
                raw,
                smtp_cfg
            )

            if not ok:

                database.log_event(
                    name,
                    "ERROR",
                    "SMTP",
                    "delivery failed"
                )

                continue

            sender = msg.get("From", "")
            subject = msg.get("Subject", "")
            message_id = msg.get("Message-ID", "")
            recipient = ",".join(
                msg.get_all("To", [])
            )

            database.save_delivery(
                name,
                uid,
                message_id,
                sender,
                recipient,
                subject,
                250,
                datetime.utcnow().isoformat()
            )

            database.log_event(
                name,
                "INFO",
                "DELIVERY",
                f"From: {sender} | Subject: {subject}"
            )

            if retention == 0:

                msg_number = uid_map.get(uid)

                if msg_number:

                    try:

                        pop3.delete_message(
                            mailbox,
                            msg_number
                        )

                        database.log_event(
                            name,
                            "INFO",
                            "RETENTION",
                            f"immediate delete uid={uid}"
                        )

                    except Exception as e:

                        database.log_event(
                            name,
                            "WARNING",
                            "RETENTION",
                            str(e)
                        )

        try:
            mailbox.quit()
        except:
            pass

    except Exception as e:

        database.log_event(
            name,
            "ERROR",
            "POP3",
            str(e)
        )