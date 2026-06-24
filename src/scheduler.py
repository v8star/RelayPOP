import time
import config
import connector
import database

# stato interno scheduler
_last_run = {}


def scheduler_loop():

    database.init_database()

    while True:

        accounts = config.load_accounts()
        now = time.time()

        for account in accounts:

            name = (account.get("name") or "").strip()

            if not name:
                continue

            # account disabilitato
            if not account.get("enabled", True):
                continue

            interval_min = int(
                account.get("poll_interval") or 1
            )

            interval = interval_min * 60

            last = _last_run.get(name, 0)

            if now - last < interval:
                continue

            try:

                connector.poll_account(account)

                _last_run[name] = now

            except Exception as e:

                database.log_event(
                    name,
                    "ERROR",
                    "SCHEDULER",
                    f"poll_failed: {str(e)}"
                )

        time.sleep(5)