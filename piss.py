#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

URI = "wss://push.lightstreamer.com/lightstreamer"
PROTOCOLS = ["TLCP-2.5.0.lightstreamer.com"]


async def main():
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
                        "LS_requested_max_frequency=0.01&"
                        "LS_ack=false"
                    )
                elif cmd.startswith("U,1,1,"):
                    value = cmd[6:]
                    # Output JSON for Waybar
                    data = {
                        "text": f" | ISS PISS: {value}%",
                        "tooltip": f"ISS piss value: {value}%",
                        "class": "piss",
                    }
                    print(json.dumps(data), flush=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
