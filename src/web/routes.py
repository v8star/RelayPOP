from flask import (
    Flask,
    flash,
    render_template,
    request,
    redirect,
    url_for
)

import os

import smtp
import settings
import config
import database
import connector

from web.auth import (
    login_required,
    authenticate,
    login_user,
    logout_user
)

app = Flask(
    __name__,
    template_folder="/opt/pop3connector/web/templates",
    static_folder="/opt/pop3connector/web/static"
)

app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")


# =========================================================
# STATUS ENGINE
# =========================================================
def compute_status(events, accounts=None):

    status = {}
    last_event = {}

    for e in events:
        acc = (e["account"] or "").strip()
        last_event[acc] = e

    if accounts is None:

        for acc, e in last_event.items():
            status[acc] = "red" if e["level"] == "ERROR" else "green"

        return status

    account_map = {a["name"]: a for a in accounts}

    for acc, account in account_map.items():

        e = last_event.get(acc)

        if not account.get("enabled", True):
            status[acc] = "gray"
            continue

        if not e:
            status[acc] = "gray"
            continue

        status[acc] = "red" if e["level"] == "ERROR" else "green"

    return status


# =========================================================
# LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if authenticate(username, password):
            login_user(username)
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


# =========================================================
# DASHBOARD
# =========================================================
@app.route("/")
@login_required
def dashboard():

    accounts = config.load_accounts()

    settings_data = settings.load_settings()
    limit = int(settings_data.get("dashboard_events_limit", 50))

    events_status = database.get_last_events(200)
    events_dashboard = database.get_last_events(limit)

    status = compute_status(events_status, accounts)

    return render_template(
        "dashboard.html",
        accounts=accounts,
        events=events_dashboard,
        status=status
    )

# =========================================================
# POP ACCOUNTS
# =========================================================
@app.route("/accounts")
@login_required
def pop():

    accounts = config.load_accounts()
    events = database.get_last_events(200)

    status = compute_status(events, accounts)

    return render_template(
        "pop.html",
        accounts=accounts,
        status=status
    )


# =========================================================
# POP NEW
# =========================================================
@app.route("/account/new", methods=["GET", "POST"])
@login_required
def pop_new():

    if request.method == "POST":

        config.save_account(request.form)
        return redirect("/accounts")

    return render_template(
        "pop_edit.html",
        account=None,
        smtp_profiles=settings.load_smtp_profiles()
    )


# =========================================================
# POP EDIT
# =========================================================
@app.route("/account/edit/<name>", methods=["GET", "POST"])
@login_required
def pop_edit(name):

    account = config.get_account(name)

    if request.method == "POST":

        config.save_account(request.form)
        return redirect("/accounts")

    return render_template(
        "pop_edit.html",
        account=account,
        smtp_profiles=settings.load_smtp_profiles()
    )


# =========================================================
# POP DELETE
# =========================================================
@app.route("/account/delete/<name>")
@login_required
def account_delete(name):

    config.delete_account(name)

    database.log_event(
        name,
        "INFO",
        "CONFIG",
        "account deleted"
    )

    return redirect("/accounts")


# =========================================================
# MANUAL POLL
# =========================================================
@app.route("/poll/<name>")
@login_required
def poll(name):

    accounts = config.load_accounts()

    account = next(
        (a for a in accounts if a["name"] == name),
        None
    )

    if not account:
        return "Account not found", 404

    try:
        connector.poll_account(account)

    except Exception as e:

        database.log_event(
            name,
            "ERROR",
            "POLL",
            str(e)
        )

    return redirect("/")


# =========================================================
# SMTP LIST
# =========================================================
@app.route("/smtp")
@login_required
def smtp_page():

    profiles = settings.load_smtp_profiles()

    return render_template(
        "smtp.html",
        profiles=profiles
    )


# =========================================================
# SMTP NEW
# =========================================================
@app.route("/smtp/new", methods=["GET", "POST"])
@login_required
def smtp_new():

    if request.method == "POST":

        data = request.form.to_dict()
        settings.save_smtp_profile(data)

        return redirect("/smtp")

    return render_template(
        "smtp_edit.html",
        profile=None
    )


# =========================================================
# SMTP EDIT
# =========================================================
@app.route("/smtp/edit/<name>", methods=["GET", "POST"])
@login_required
def smtp_edit(name):

    profile = settings.load_smtp_profile(name)

    if request.method == "POST":

        data = request.form.to_dict()
        data["name"] = name

        settings.save_smtp_profile(data)

        return redirect("/smtp")

    return render_template(
        "smtp_edit.html",
        profile=profile
    )


# =========================================================
# SMTP DELETE
# =========================================================
@app.route("/smtp/delete/<name>")
@login_required
def smtp_delete(name):

    accounts = config.load_accounts()

    for account in accounts:
        if account.get("smtp_profile") == name:
            flash(f"SMTP profile '{name}' is in use")
            return redirect("/smtp")

    settings.delete_smtp_profile(name)

    database.log_event(
        name,
        "INFO",
        "CONFIG",
        "smtp profile deleted"
    )

    flash(f"SMTP profile '{name}' deleted")

    return redirect("/smtp")


# =========================================================
# SETTINGS (SYSTEM)
# =========================================================
@app.route("/settings")
@login_required
def settings_page():

    data = settings.load_settings()

    return render_template(
        "settings.html",
        settings=data
    )


# =========================================================
# SETTINGS SAVE
# =========================================================
@app.route("/settings/general", methods=["POST"])
@login_required
def settings_general_save():

    data = settings.load_settings()

    data["ui_refresh"] = int(request.form.get("ui_refresh", 10))
    data["default_poll_interval"] = int(request.form.get("default_poll_interval", 1))
    data["dashboard_events_limit"] = int(request.form.get("dashboard_events_limit", 50))

    settings.save_settings(data)

    flash("Settings updated")

    return redirect("/settings")


# =========================================================
# PASSWORD CHANGE
# =========================================================
@app.route("/settings/password", methods=["POST"])
@login_required
def change_password():

    current = request.form.get("current_password")
    new = request.form.get("new_password")
    confirm = request.form.get("confirm_password")

    if not current or not new:
        flash("Missing password fields")
        return redirect("/settings")

    if new != confirm:
        flash("Passwords do not match")
        return redirect("/settings")

    ok = settings.change_admin_password(current, new)

    if not ok:
        flash("Invalid current password")
        return redirect("/settings")

    flash("Password updated")
    return redirect("/settings")


# =========================================================
# SMTP TEST
# =========================================================
@app.route("/smtp/test/<name>")
@login_required
def smtp_test(name):

    profile = settings.load_smtp_profile(name)

    if not profile:
        return "SMTP profile not found", 404

    ok, message = smtp.send_test_mail(profile)

    if ok:

        database.log_event(
            "SYSTEM",
            "INFO",
            "SMTPTEST",
            f"profile={name}"
        )

        flash(message)

    else:

        database.log_event(
            "SYSTEM",
            "ERROR",
            "SMTPTEST",
            f"profile={name}: {message}"
        )

        flash(f"[ERROR] {message}")

    return redirect("/smtp")