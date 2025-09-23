import asyncio
import websockets
import json
import time
import logging

URI = "wss://push.lightstreamer.com/lightstreamer"
PROTOCOLS = ["TLCP-2.5.0.lightstreamer.com"]


async def run_stream():
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
                        "text": f"{value}",
                        "tooltip": f"last update: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                        "class": "iss-tank",
                    }
                    print(json.dumps(data), flush=True)
