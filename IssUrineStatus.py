#!/usr/bin/env python3

# Update Test
import asyncio
import websockets
import json
import sys
import time
import os
import aiohttp
import subprocess
from desktop_notifier import DesktopNotifier, Urgency


SELF_PATH = os.path.abspath(__file__)
VERSION_FILE = os.path.expanduser("~/.config/waybar/scripts/urine_version.txt")
UPDATE_LOCK_FILE = os.path.expanduser("~/.config/waybar/scripts/VersionControll.lock")
LOG = os.path.expanduser("~/.config/waybar/scripts/urine_log.txt")

URI = "wss://push.lightstreamer.com/lightstreamer"
PROTOCOLS = ["TLCP-2.5.0.lightstreamer.com"]

notifier = DesktopNotifier(app_name="ISS Urine Tank Percentage")


# ------------------------------
# Core worker
# ------------------------------
async def main():
    if not await check_internet():
        data = {
            "text": "No Internet",
            "tooltip": "Can't access repository",
            "class": "piss",
        }
        print(json.dumps(data), flush=True)
        return

    async with websockets.connect(URI, subprotocols=PROTOCOLS) as ws:
        await ws.send("wsok")
        await ws.send(
            "create_session\r\n"
            "LS_adapter_set=ISSLIVE&"
            "LS_cid=pcYgxn8m8%20feOojyA1V661f3g2.pz482h95IL5h&"
            "LS_send_sync=false&"
            "LS_cause=api"
        )

        async for msg in ws:
            for cmd in msg.strip().split("\r\n"):
                if cmd == "CONS,unlimited":
                    await ws.send(
                        "control\r\n"
                        "LS_reqId=1&"
                        "LS_op=add&"
                        "LS_subId=1&"
                        "LS_mode=MERGE&"
                        "LS_group=NODE3000005&"
                        "LS_schema=Value&"
                        "LS_snapshot=true&"
                        "LS_requested_max_frequency=1.0&"
                        "LS_ack=false"
                    )
                elif cmd.startswith("U,1,1,"):
                    value = cmd[6:]
                    data = {
                        # Toilet emoji: 🚽
                        "text": f" 🚽{value}%",
                        "tooltip": f"last update: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        "class": "piss",
                    }
                    print(json.dumps(data), flush=True)


def log(text: str):
    with open(LOG, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {text}\n")
    print(f"LOG: {text}")


# ------------------------------
# Network utilities
# ------------------------------
async def fetch_text(url: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
    except aiohttp.ClientError:
        return None
    return None


async def check_internet() -> bool:
    url = "https://github.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin"
    text = await fetch_text(url)
    return text is not None


async def download_version_file():
    url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/version.txt"
    text = await fetch_text(url)
    if text:
        with open(VERSION_FILE, "w") as f:
            f.write(text)
        log("Downloaded version file.")
    else:
        log("Failed to download version file.")


# ------------------------------
# Rofi prompts (blocking, run in executor)
# ------------------------------


def ask_user_download():
    if SessionState.prompted_for_download:
        return
    SessionState.prompted_for_download = True
    log(
        f"Session flags: download_prompted={SessionState.prompted_for_download}, update_prompted={SessionState.prompted_for_update}"
    )
    try:
        rofi = subprocess.run(
            ["rofi", "-dmenu", "-p", "Version file missing. Download now?"],
            input="Yes\nNo\n".encode(),
            capture_output=True,
        )
        choice = rofi.stdout.decode().strip()
        if choice == "Yes":
            asyncio.run(download_version_file())
        else:
            log("User declined to download version file.")
            ask_user_continue_update_checks()
    except FileNotFoundError:
        log("Rofi not installed or not in PATH")


# ------------------------------
# Update handling
# ------------------------------


def create_update_lock():
    with open(UPDATE_LOCK_FILE, "w") as f:
        f.write(f"Lock created on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def ask_user_continue_update_checks():
    if SessionState.prompted_for_continue_checks:
        return
    SessionState.prompted_for_continue_checks = True
    log(
        f"Session flags: download_prompted={SessionState.prompted_for_download}, update_prompted={SessionState.prompted_for_update}"
    )
    try:
        rofi = subprocess.run(
            [
                "rofi",
                "-dmenu",
                "-p",
                "Would you like to check for updates in the future?",
            ],
            input="Yes\nNo\n".encode(),
            capture_output=True,
        )
        choice = rofi.stdout.decode().strip()
        if choice == "No":
            log("User opted out of future update checks.")
            create_update_lock()
    except FileNotFoundError:
        log("Rofi not installed or not in PATH")


async def ask_user_update():
    if SessionState.prompted_for_update:
        return
    SessionState.prompted_for_update = True
    log(
        f"Session flags: download_prompted={SessionState.prompted_for_download}, update_prompted={SessionState.prompted_for_update}"
    )

    try:
        rofi = subprocess.run(
            ["rofi", "-dmenu", "-p", "Update available. Update now?"],
            input="Yes\nNo\n".encode(),
            capture_output=True,
        )
        choice = rofi.stdout.decode().strip()
        if choice == "Yes":
            await update()
        else:
            log("User declined update.")
            ask_user_continue_update_checks()
    except FileNotFoundError:
        log("Rofi not installed or not in PATH")


async def update():
    log("Update available, starting update...")
    print(
        json.dumps({"text": "updating...", "tooltip": "Updating...", "class": "piss"}),
        flush=True,
    )
    log(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Updating...")
    await notifier.send(
        title="Update Available", message="Starting update...", urgency=Urgency.Normal
    )

    url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/IssUrineStatus.py"
    text = await fetch_text(url)
    if not text:
        await notifier.send(
            title="Update Failed",
            message="Could not fetch code.",
            urgency=Urgency.Critical,
        )
        return

    try:
        with open(SELF_PATH, "w") as f:
            f.write(text)
        await download_version_file()
    except Exception as e:
        log(f"Failed to write update: {e}")
        return

    await notifier.send(
        title="Update Complete", message="Restarting...", urgency=Urgency.Normal
    )

    # Restart with new code
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def up_to_date() -> bool:
    url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/version.txt"
    remote = await fetch_text(url)
    if not remote:
        return True
    if not os.path.exists(VERSION_FILE):
        return False
    with open(VERSION_FILE) as f:
        return f.read().strip() == remote.strip()


async def version_controll():
    if not await check_internet():
        log("No internet connection. Skipping version check.")
        return

    if os.path.exists(UPDATE_LOCK_FILE):
        log("Update checks disabled by user.")
        return

    if not os.path.exists(VERSION_FILE):
        # Ask to download version file
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, ask_user_download)

    # If the user declined to download version.txt, stop here
    if not os.path.exists(VERSION_FILE):
        log("User declined version file download.")
        return

    # Check version and prompt if update is available
    if not await up_to_date():
        await ask_user_update()
    else:
        log("Script is up to date.")


# ------------------------------
# Entrypoint
# ------------------------------
if __name__ == "__main__":
    # Check if log exists, if not, create

    if not os.path.exists(LOG):
        with open(LOG, "w") as f:
            f.write(
                f"==== Urine Tank Log ====\nCreated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )
        print("Created log file with header.")

    try:
        asyncio.run(version_controll())
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)


class SessionState:
    prompted_for_download = False
    prompted_for_update = False
    prompted_for_continue_checks = False
