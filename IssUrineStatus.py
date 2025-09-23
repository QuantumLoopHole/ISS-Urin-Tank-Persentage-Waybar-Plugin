#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
import time
import os
import requests
import subprocess
from desktop_notifier import DesktopNotifier, Urgency


URI = "wss://push.lightstreamer.com/lightstreamer"
PROTOCOLS = ["TLCP-2.5.0.lightstreamer.com"]


# It screams in pain, but hey, it works
async def main():
    if not check_internet():
        data = {
            "text": "No Internet",
            "tooltip": "Can't access repository",
            "class": "piss",
        }
        print(json.dumps(data), flush=True)
        return

    # Handel display and data retrival
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
                    # Output JSON for Waybar
                    data = {
                        "text": f"{value}",
                        "tooltip": f"last update: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        "class": "piss",
                    }
                    print(json.dumps(data), flush=True)


async def download_version_file():
    try:
        url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/version.txt"
        response = requests.get(url)
        response.raise_for_status()
    except EnvironmentError:
        print("Failed to fetch version info")
    file_path = "./version.txt"
    with open(file_path, "w") as file:
        file.write(response.text)


def check_internet():
    try:
        url = (
            "https://github.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin"
        )
        response = requests.get(url)
        response.raise_for_status()

        if response.status_code == 200:
            return True
        else:
            return False
    except EnvironmentError:
        return False


def ask_user_download():
    try:
        # Present a simple Yes/No menu
        rofi = subprocess.run(
            ["rofi", "-dmenu", "-p", "Version file is missing. Download now?"],
            input="Yes\nNo\n".encode(),
            capture_output=True,
        )
        choice = rofi.stdout.decode().strip()
        if choice == "Yes":
            download_version_file()
        else:
            print("User chose not to download")
            ask_user_continue_update_checks()
    except FileNotFoundError:
        print("Rofi not installed or not in PATH")


def ask_user_continue_update_checks():
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
            # Create lockout file
            with open("./VersionControll.lock", "w") as file:
                file.write("User opted out of update checks.")
    except FileNotFoundError:
        print("Rofi not installed or not in PATH")


notifier = DesktopNotifier(app_name="ISS Urine Tank Percentage")


async def update():
    # Show status to user

    data = {
        "text": "updating...",
        "tooltip": "Updating code, please wait",
        "class": "piss",
    }
    print(json.dumps(data), flush=True)

    await notifier.send(
        title="Update Available", message="Starting update...", urgency=Urgency.Normal
    )

    # Download new code
    try:
        url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/IssUrineStatus.py"
        response = requests.get(url)
        response.raise_for_status()
    except EnvironmentError:
        response = requests.Response()
        response.status_code = 404
        print("Failed to fetch update info")

    if response.status_code != 200:
        print("Failed to fetch update info")
        await notifier.send(
            title="Update Check Failed",
            message="Could not fetch update info.",
            urgency=Urgency.Critical,
        )

    # Update new code
    try:
        with open("./IssUrineStatus.py", "w") as file:
            file.write(response.text)

        await download_version_file()
    except Exception as e:
        print(f"Failed to write update: {e}")

    return


def up_to_date():
    try:
        url = "https://raw.githubusercontent.com/QuantumLoopHole/ISS-Urine-Tank-Percentage-Waybar-Plugin/refs/heads/main/version.txt"
        response = requests.get(url)
        response.raise_for_status()
    except EnvironmentError:
        response = requests.Response()
        response.status_code = 404
        print("Failed to fetch update info")

    with open("./version.txt", "r") as file:
        if file.read().strip() == response.text.strip():
            return True
        else:
            return False


async def version_controll():
    # Lockout file to see if user wants to check for updates
    if check_internet() is False:
        return

    if os.path.exists("./VersionControll.lock"):
        return

    if not os.path.exists("./version.txt"):
        # Run rofi prompt in a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, ask_user_download)

    if up_to_date():
        return
    await update()


if __name__ == "__main__":
    # Version controll
    asyncio.run(version_controll())
    # Main code
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
