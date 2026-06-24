def compute_status(events):

    status = {}

    for e in events:

        acc = (e["account"] or "").strip().lower()

        if e["level"] == "ERROR":
            status[acc] = "red"

        elif e["component"] == "SCHEDULER" and "poll_ok" in e["message"]:
            status.setdefault(acc, "green")

        elif e["component"] == "POP3":
            status.setdefault(acc, "green")

    return status