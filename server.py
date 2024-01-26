"""
Websocket server made for listening to a basic StreamDeck Websocket client
plugin. This is where the scripts will be launched from... and sometimes
communicated with, although this is the kind of complex stuff I'll worry
about later.
"""

import asyncio
import websockets
from websockets import WebSocketServerProtocol
import subprocess
import os
import terminal_window_manager_v3 as twm_v3

venv_python_path = "venv/Scripts/python.exe"


def control_scanner(message):
    if message == "start scanner":
        # remove the stop flag that stopped the previous scanner loop
        if os.path.exists("temp/stop.flag"):
            os.remove("temp/stop.flag")
        # Open the process in a new separate cmd window
        subprocess.Popen(["cmd.exe", "/c", "start",
                          venv_python_path, "main.py"])
    elif message == "stop scanner":
        with open("temp/stop.flag", "w") as f:
            pass


def operate_launcher(message):
    if message in ["start scanner", "stop scanner"]:
        control_scanner(message)
    else:
        print('not a suitable launcher path message')


async def handler(websocket: WebSocketServerProtocol, path: str):
    print(f"Connection established on path: {path}")

    async for message in websocket:
        print(f"Received: message {message} on path: {path}")

        if path == "/launcher":  # Path to start and end scripts
            operate_launcher(message)

        elif path == "/windows":  # Path to manipulate windows properties
            if message == "bring to top":
                # print('reached')
                twm_v3.bring_windows_on_top()

        else:
            print(f"Unknown path: {path}.")


def main():
    print("Welcome to the server, bro. You know what to do.")

    if not os.path.exists("temp"):
        os.makedirs("temp")

    start_server = websockets.serve(handler, "localhost", 8765)

    twm_v3.adjust_window(twm_v3.WindowType.SERVER, 'SERVER')

    try:
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('KeyboardInterrupt')


if __name__ == "__main__":
    main()
