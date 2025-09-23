import os
import requests
import tempfile
import logging
from prompts import ask_user

VERSION_FILE = "./version.txt"
LOCK_FILE = "./VersionControl.lock"

# Every file in your repo that should be updated
FILES_TO_UPDATE = [
    "main.py",
    "stream.py",
    "updates.py",
    "prompts.py",
]

BASE_URL = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/"
VERSION_URL = BASE_URL + "version.txt"


def check_internet():
    try:
        r = requests.get("https://github.com", timeout=5)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False


def download_version_file():
    response = requests.get(VERSION_URL, timeout=5)
    response.raise_for_status()
    with open(VERSION_FILE, "w") as f:
        f.write(response.text)


def up_to_date():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        with open(VERSION_FILE, "r") as f:
            return f.read().strip() == response.text.strip()
    except Exception:
        return False


def download_files():
    for fname in FILES_TO_UPDATE:
        url = BASE_URL + fname
        logging.info(f"Fetching {url}")
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        # write safely
        temp = tempfile.NamedTemporaryFile(delete=False)
        with open(temp.name, "w") as f:
            f.write(r.text)

        if os.path.getsize(temp.name) < 10:  # sanity check
            logging.warning(f"Downloaded {fname} looks empty, skipping")
            continue

        os.replace(temp.name, fname)
        logging.info(f"Updated {fname}")


async def update(notifier):
    try:
        download_files()
        download_version_file()
    except requests.exceptions.RequestException as e:
        logging.error(f"Update fetch failed: {e}")
        await notifier.send(
            title="Update Failed",
            message="Could not fetch update info.",
            urgency=2,
        )
        return

    await notifier.send(
        title="Update Complete",
        message="ISS Urine Tank plugin updated.",
        urgency=1,
    )


async def version_control(notifier):
    if not check_internet():
        return

    if os.path.exists(LOCK_FILE):
        return

    if not os.path.exists(VERSION_FILE):
        choice = ask_user("Version file missing. Download now?", ["Yes", "No"])
        if choice == "Yes":
            download_version_file()
        else:
            opt = ask_user("Check for updates in the future?", ["Yes", "No"])
            if opt == "No":
                with open(LOCK_FILE, "w") as f:
                    f.write("User opted out.")
            return

    if up_to_date():
        return

    await update(notifier)

