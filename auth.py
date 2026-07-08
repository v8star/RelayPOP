import hashlib

import settings
from flask import session, redirect


def authenticate(password):

    data = settings.load_settings()

    stored = data.get("admin_password_hash")

    # primo avvio (nessuna password configurata)
    if not stored:
        return True

    return hashlib.sha256(
        password.encode()
    ).hexdigest() == stored


def login_required(func):

    def wrapper(*args, **kwargs):

        if not session.get("logged_in"):
            return redirect("/login")

        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__

    return wrapper


def login_user():

    session["logged_in"] = True


def logout_user():

    session.clear()