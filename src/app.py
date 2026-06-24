from threading import Thread
import logging

from scheduler import scheduler_loop
from web.routes import app
import database


def start_scheduler():
    t = Thread(target=scheduler_loop, daemon=True)
    t.start()
    return t


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s"
    )

    database.init_database()

    start_scheduler()

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
        use_reloader=False
    )