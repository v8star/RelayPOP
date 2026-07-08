import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB = "/data/connector.db"


# =========================================================
# CONNECTION
# =========================================================
def get_connection():

    Path("/data").mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


# =========================================================
# INIT DATABASE
# =========================================================
def init_database():

    with get_connection() as conn:

        # -------------------------
        # DELIVERED MESSAGES
        # -------------------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS delivered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account TEXT NOT NULL,
            uid TEXT NOT NULL,
            message_id TEXT,
            sender TEXT,
            recipient TEXT,
            subject TEXT,
            smtp_code INTEGER,
            delivered_at TEXT,
            UNIQUE(account, uid)
        )
        """)

        # -------------------------
        # EVENTS LOG
        # -------------------------
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TEXT NOT NULL,
            account TEXT,
            level TEXT,
            component TEXT,
            message TEXT
        )
        """)

        conn.commit()


# =========================================================
# DELIVERY TRACKING
# =========================================================
def already_delivered(account, uid):

    with get_connection() as conn:

        cur = conn.execute("""
            SELECT 1
            FROM delivered
            WHERE account=? AND uid=?
            LIMIT 1
        """, (account, uid))

        return cur.fetchone() is not None


def save_delivery(account, uid, message_id, sender, recipient, subject, smtp_code, delivered_at):

    with get_connection() as conn:

        conn.execute("""
            INSERT OR IGNORE INTO delivered (
                account,
                uid,
                message_id,
                sender,
                recipient,
                subject,
                smtp_code,
                delivered_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            account,
            uid,
            message_id,
            sender,
            recipient,
            subject,
            smtp_code,
            delivered_at
        ))

        conn.commit()


# =========================================================
# EVENTS LOG
# =========================================================
def log_event(account, level, component, message):

    with get_connection() as conn:

        conn.execute("""
            INSERT INTO events (
                event_time,
                account,
                level,
                component,
                message
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.now(
                ZoneInfo("Europe/Rome")
            ).isoformat(timespec="seconds"),
            account,
            level,
            component,
            message
        ))

        conn.commit()


# =========================================================
# EVENTS READ (UI DASHBOARD)
# =========================================================
def get_last_events(limit=20):

    with get_connection() as conn:

        cur = conn.execute("""
            SELECT *
            FROM events
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))

        return cur.fetchall()


# =========================================================
# RETENTION CLEANUP (POP3 SAFE MODE)
# =========================================================
def cleanup_retention(account, retention_days, delete_callback, uid_map):

    if retention_days < 0:
        return

    cutoff = datetime.utcnow() - timedelta(days=retention_days)

#    log_event(
#        account,
#        "INFO",
#        "RETENTION",
#        f"cleanup started cutoff={cutoff.isoformat()}"
#    )

    with get_connection() as conn:

        cur = conn.execute("""
            SELECT uid, delivered_at
            FROM delivered
            WHERE account=?
        """, (account,))

        rows = cur.fetchall()

#       log_event(
#            account,
#            "INFO",
#            "RETENTION",
#            f"{len(rows)} entries found"
#        )

        for r in rows:

            uid = r["uid"]

            try:
                delivered_time = datetime.fromisoformat(r["delivered_at"])
            except Exception as e:

                log_event(
                    account,
                    "WARNING",
                    "RETENTION",
                    f"invalid date for uid={uid}: {e}"
                )
                continue

            if delivered_time >= cutoff:
                continue

#            log_event(
#                account,
#                "INFO",
#                "RETENTION",
#                f"expired uid={uid}"
#            )

            msg_number = uid_map.get(uid)

            if not msg_number:

                log_event(
                    account,
                    "WARNING",
                    "RETENTION",
                    f"uid not found on server: {uid}"
                )

                continue

            try:

                log_event(
                    account,
                    "INFO",
                    "RETENTION",
                    f"DELE message #{msg_number}"
                )

                delete_callback(msg_number)

                conn.execute("""
                    DELETE FROM delivered
                    WHERE account=? AND uid=?
                """, (account, uid))

                conn.commit()

#                log_event(
#                    account,
#                    "INFO",
#                    "RETENTION",
#                    f"deleted uid={uid}"
#                )

            except Exception as e:

                log_event(
                    account,
                    "ERROR",
                    "RETENTION",
                    str(e)
                )