from pathlib import Path
from utils import merge_field
import yaml
import hashlib

SMTP_DIR = Path("/config/smtp")
SETTINGS_FILE = Path("/config/settings.yaml")


# =========================================================
# SETTINGS
# =========================================================

def load_settings():

    if not SETTINGS_FILE.exists():
        return {}

    with open(
        SETTINGS_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return yaml.safe_load(f) or {}


def save_settings(data):

    SETTINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True
        )


# =========================================================
# SMTP PROFILES
# =========================================================

def load_smtp_profiles():

    profiles = []

    SMTP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    for file in sorted(
        SMTP_DIR.glob("*.yaml")
    ):

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            profile = yaml.safe_load(f) or {}

            profiles.append(profile)

    return profiles
# =========================================================
# OPEN SMTP PROFILES
# =========================================================
def get_smtp_profile_names():

    return [
        p["name"]
        for p in load_smtp_profiles()
        if p.get("name")
    ]


def load_smtp_profile(name):

    file = SMTP_DIR / f"{name}.yaml"

    if not file.exists():
        return None

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        return yaml.safe_load(f) or {}

# =========================================================
# SAVE SMTP PROFILES
# =========================================================
def save_smtp_profile(profile):

    if not profile.get("name"):
        raise ValueError(
            "SMTP profile name required"
        )

    existing = load_smtp_profile(
        profile["name"]
    ) or {}

    profile["password"] = merge_field(
        profile.get("password"),
        existing.get("password"),
        ""
    )

    SMTP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    file = SMTP_DIR / (
        f"{profile['name']}.yaml"
    )

    with open(
        file,
        "w",
        encoding="utf-8"
    ) as f:

        yaml.safe_dump(
            profile,
            f,
            sort_keys=False,
            allow_unicode=True
        )

# =========================================================
# CHANGE PASSWORD
# =========================================================

SETTINGS_FILE = Path("/config/settings.yaml")


def _hash(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


def change_admin_password(current, new):

    data = load_settings()

    stored = data.get("admin_password_hash")

    if not stored:
        data["admin_password_hash"] = _hash(new)
        save_settings(data)
        return True

    if _hash(current) != stored:
        return False

    data["admin_password_hash"] = _hash(new)
    save_settings(data)

    return True