import yaml
import hashlib
import hmac
import settings
from pathlib import Path
from flask import session, redirect

CONFIG_FILE = Path("/config/settings.yaml")


def authenticate(username, password):

    data = settings.load_settings()

    stored = data.get("admin_password_hash")

    # primo avvio (nessuna password settata)
    if not stored:
        return True

    return hashlib.sha256(password.encode()).hexdigest() == stored

def login_required(func):
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def login_user(username):
    session["logged_in"] = True
    session["user"] = username


def logout_user():
    session.clear()