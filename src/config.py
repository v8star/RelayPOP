import yaml
import time
from pathlib import Path
from utils import merge_field


CONFIG_DIR = Path("/config/accounts")

CACHE_TTL = 2

_CACHE = {
    "ts": 0,
    "data": []
}


# =========================================================
# LOAD FROM DISK
# =========================================================
def _load_from_disk():

    accounts = []

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    for file in sorted(CONFIG_DIR.glob("*.yaml")):

        with open(file, "r", encoding="utf-8") as f:

            data = yaml.safe_load(f)

            if data:
                accounts.append(data)

    return accounts


# =========================================================
# LOAD ALL ACCOUNTS
# =========================================================
def load_accounts(force=False):

    now = time.time()

    if not force and (now - _CACHE["ts"] < CACHE_TTL):
        return _CACHE["data"]

    data = _load_from_disk()

    _CACHE["data"] = data
    _CACHE["ts"] = now

    return data


# =========================================================
# GET ACCOUNT
# =========================================================
def get_account(name, force=False):

    accounts = load_accounts(force=force)

    return next((a for a in accounts if a["name"] == name), None)


# =========================================================
# SAFE FIELD MERGE
# =========================================================
def merge_field(form_value, existing_value, default=None):

    if form_value is None:
        return existing_value or default

    if isinstance(form_value, str) and form_value.strip() == "":
        return existing_value or default

    return form_value


# =========================================================
# SAVE ACCOUNT
# =========================================================
def save_account(form):

    name = form["name"]

    existing = get_account(name) or {}

    existing_pop3 = existing.get("pop3", {})

    new_password = form.get("pop3_pass")

    account = {

        "name": name,

        "poll_interval": int(form.get("poll_interval", 1)),

        "retention_days": int(form.get("retention_days", 7)),

       "enabled": form.get("enabled") == "on",

        "smtp_profile": form.get("smtp_profile"),

        "pop3": {

            "host": form.get("pop3_host"),

            "port": int(form.get("pop3_port", 995)),

            "username": form.get("pop3_user"),

            "password": merge_field(
                new_password,
                existing_pop3.get("password"),
                ""
            )
        }
    }

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    file = CONFIG_DIR / f"{name}.yaml"

    with open(file, "w", encoding="utf-8") as f:

        yaml.safe_dump(
            account,
            f,
            sort_keys=False,
            allow_unicode=True
        )

    _CACHE["ts"] = 0


# =========================================================
# DELETE ACCOUNT
# =========================================================
def delete_account(name):

    file = CONFIG_DIR / f"{name}.yaml"

    if file.exists():
        file.unlink()

    _CACHE["ts"] = 0