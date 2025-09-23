#!/usr/bin/env python3
import asyncio
import sys
import json
import logging

from stream import run_stream
from updates import version_control
from desktop_notifier import DesktopNotifier, Urgency

logging.basicConfig(
    filename="urine.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

notifier = DesktopNotifier(app_name="ISS Urine Tank Percentage")


async def main():
    # First, check updates
    await version_control(notifier)

    # Now run stream
    try:
        await run_stream()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logging.exception("Fatal error in main loop")
        data = {
            "text": "Error",
            "tooltip": f"Stream failed: {e}",
            "class": "iss-tank",
        }
        print(json.dumps(data), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
