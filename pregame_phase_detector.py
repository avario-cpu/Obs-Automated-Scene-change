import atexit
import os

import cv2
import cv2 as cv
import mss
import numpy as np
from skimage.metrics import structural_similarity as ssim
import asyncio
import my_classes as my
import single_instance
import terminal_window_manager_v4 as twm
import denied_slots_db_handler as denied_sdh
import slots_db_handler as sdh
import websockets
from websockets import WebSocketException, ConnectionClosedError
import constants
import logging
from enum import Enum, auto
import time


class InterruptType(Enum):
    DOTA_TAB_OUT = auto()
    DESKTOP_TAB_OUT = auto()
    GAME_CANCEL = auto()
    SETTINGS_SCREEN = auto()
    VERSUS_SCREEN = auto()
    TRANSITION_MESSAGE = auto()


class Tabbed:
    def __init__(self):
        self._out_to_desktop = False
        self._in_dota_menu = False
        self._in_settings_screen = False

    @property
    def out_to_desktop(self):
        return self._out_to_desktop

    @out_to_desktop.setter
    def out_to_desktop(self, value):
        if value:
            self._set_all_false()
        self._out_to_desktop = value

    @property
    def in_dota_menu(self):
        return self._in_dota_menu

    @in_dota_menu.setter
    def in_dota_menu(self, value):
        if value:
            self._set_all_false()
        self._in_dota_menu = value

    @property
    def in_settings_screen(self):
        return self._in_settings_screen

    @in_settings_screen.setter
    def in_settings_screen(self, value):
        if value:
            self._set_all_false()
        self._in_settings_screen = value

    def _set_all_false(self):
        self._out_to_desktop = False
        self._in_dota_menu = False
        self._in_settings_screen = False

    def current_state(self):
        if self._out_to_desktop:
            return "Out to desktop"
        elif self._in_dota_menu:
            return "In Dota menu"
        elif self._in_settings_screen:
            return "In settings screen"
        else:
            return "No state is True"


class PreGamePhases:

    def __init__(self):
        self._finding_game = False
        self._hero_pick = False
        self._starting_buy = False
        self._in_settings = False
        self._versus_screen = False
        self._in_game = False

    @property
    def finding_game(self):
        return self._finding_game

    @finding_game.setter
    def finding_game(self, value):
        if value:
            self._set_all_false()
        self._finding_game = value

    @property
    def hero_pick(self):
        return self._hero_pick

    @hero_pick.setter
    def hero_pick(self, value):
        if value:
            self._set_all_false()
        self._hero_pick = value

    @property
    def starting_buy(self):
        return self._starting_buy

    @starting_buy.setter
    def starting_buy(self, value):
        if value:
            self._set_all_false()
        self._starting_buy = value

    @property
    def in_settings(self):
        return self._in_settings

    @in_settings.setter
    def in_settings(self, value):
        if value:
            self._set_all_false()
        self._in_settings = value

    @property
    def versus_screen(self):
        return self._versus_screen

    @versus_screen.setter
    def versus_screen(self, value):
        if value:
            self._set_all_false()
        self._versus_screen = value

    @property
    def in_game(self):
        return self._in_game

    @in_game.setter
    def in_game(self, value):
        if value:
            self._set_all_false()
        self._in_game = value

    def _set_all_false(self):
        self._finding_game = False
        self._hero_pick = False
        self._starting_buy = False
        self._in_settings = False
        self._versus_screen = False
        self._in_game = False


DOTA_TAB_AREA = {"left": 1860, "top": 10, "width": 60, "height": 40}
STARTING_BUY_AREA = {"left": 860, "top": 120, "width": 400, "height": 30}
IN_GAME_AREA = {"left": 1820, "top": 1020, "width": 80, "height": 60}
PLAY_DOTA_BUTTON_AREA = {"left": 1525, "top": 1005, "width": 340, "height": 55}
DESKTOP_TAB_AREA = {"left": 1750, "top": 1040, "width": 50, "height": 40}
SETTINGS_AREA = {"left": 170, "top": 85, "width": 40, "height": 40}
HERO_PICK_AREA = {"left": 1658, "top": 1028, "width": 62, "height": 38}
NEW_AREA = {"left": 0, "top": 0, "width": 0, "height": 0}

DOTA_TAB_TEMPLATE = cv2.imread("opencv/dota_power_icon.jpg",
                               cv.IMREAD_GRAYSCALE)
IN_GAME_TEMPLATE = cv2.imread("opencv/deliver_items_icon.jpg",
                              cv.IMREAD_GRAYSCALE)
STARTING_BUY_TEMPLATE = cv2.imread("opencv/strategy-load-out-world-guides.jpg",
                                   cv.IMREAD_GRAYSCALE)
PLAY_DOTA_BUTTON_TEMPLATE = cv2.imread("opencv/play_dota.jpg",
                                       cv.IMREAD_GRAYSCALE)
DESKTOP_TAB_TEMPLATE = cv2.imread("opencv/desktop_icons.jpg",
                                  cv.IMREAD_GRAYSCALE)
SETTINGS_TEMPLATE = cv2.imread("opencv/dota_settings_icon.jpg",
                               cv.IMREAD_GRAYSCALE)
HERO_PICK_TEMPLATE = cv2.imread("opencv/hero_pick_chat_icons.jpg",
                                cv.IMREAD_GRAYSCALE)

SECONDARY_WINDOWS = [my.SecondaryWindow("main_scanner", 200, 100),
                     my.SecondaryWindow("second_scanner", 200, 100),
                     my.SecondaryWindow("third_scanner", 200, 100),
                     my.SecondaryWindow("fourth_scanner", 200, 100)]
SCRIPT_NAME = constants.SCRIPT_NAME_SUFFIX + os.path.splitext(
    os.path.basename(__file__))[0] if __name__ == "__main__" else __name__
# suffix added to avoid window naming conflicts with cli manager
STREAMERBOT_WS_URL = "ws://127.0.0.1:50001/"

initial_secondary_windows_spawned = asyncio.Event()
secondary_windows_readjusted = asyncio.Event()
mute_main_loop_print_feedback = asyncio.Event()
stop_event = asyncio.Event()

logger = logging.getLogger(SCRIPT_NAME)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(f'temp/logs/{SCRIPT_NAME}.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.info("\n\n\n\n<< New Log Entry >>")


def exit_countdown():
    """Give a bit of time to read terminal exit statements"""
    for seconds in reversed(range(1, 5)):
        print("\r" + f'cmd will close in {seconds} seconds...', end="\r")
        time.sleep(1)
    exit()


async def establish_ws_connection():
    try:
        ws = await websockets.connect(STREAMERBOT_WS_URL)
        logger.info(f"Established connection: {ws}")
        return ws
    except WebSocketException as e:
        logger.debug(f"Websocket error: {e}")
    except OSError as e:
        logger.debug(f"OS error: {e}")
    return None


async def handle_socket_client(reader, writer):
    while True:
        data = await reader.read(1024)
        if not data:
            print("Socket client disconnected")
            break
        message = data.decode()
        if message == constants.STOP_SUBPROCESS_MESSAGE:
            stop_event.set()
        print(f"Received: {message}")
        writer.write(b"ACK from WebSocket server")
        await writer.drain()
    writer.close()


async def run_socket_server():
    logger.info("Starting run_socket_server")
    server = await asyncio.start_server(handle_socket_client, 'localhost',
                                        constants.SUBPROCESSES[SCRIPT_NAME])
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")
    logger.info(f"Serving on {addr}")

    try:
        await server.serve_forever()
    except asyncio.CancelledError:
        print("Socket server task was cancelled. Stopping server")
    finally:
        server.close()
        await server.wait_closed()
        print("Server closed")


async def capture_window(area):
    with mss.mss() as sct:
        img = sct.grab(area)
    return np.array(img)


async def compare_images(image_a, image_b):
    return ssim(image_a, image_b)


async def send_json_requests(ws, json_file_paths: str | list[str]):
    if isinstance(json_file_paths, str):
        json_file_paths = [json_file_paths]

    for json_file in json_file_paths:
        try:
            with open(json_file, 'r') as file:
                await ws.send(file.read())
            response = await ws.recv()
            logger.info(f"WebSocket response: {response}")
        except ConnectionClosedError as e:
            logger.error(f"WebSocket connection closed: {e}")
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")


async def send_streamerbot_ws_request(ws: websockets.WebSocketClientProtocol,
                                      game_phase: PreGamePhases,
                                      tabbed: Tabbed = None):
    if tabbed:
        if tabbed.in_settings_screen:
            await send_json_requests(
                ws, "streamerbot_ws_requests/dslr_hide_for_VS_screen.json")
        elif tabbed.in_dota_menu:
            pass

    elif not tabbed:
        if game_phase.in_game:
            await send_json_requests(
                ws, "streamerbot_ws_requests/switch_to_meta_scene.json")
        elif game_phase.versus_screen:
            await send_json_requests(
                ws, "streamerbot_ws_requests/dslr_hide_for_VS_screen.json")
        elif game_phase.starting_buy:
            await send_json_requests(
                ws, "streamerbot_ws_requests/dslr_move_for_starting_buy.json")
        elif game_phase.hero_pick:
            await send_json_requests(
                ws,
                "streamerbot_ws_requests/scene_change_and_dslr_move_for_pick"
                ".json")
        elif game_phase.finding_game:
            await send_json_requests(
                ws, "streamerbot_ws_requests/switch_to_meta_scene.json")


async def readjust_secondary_windows():
    sdh_slot = sdh.get_slot_by_main_name(SCRIPT_NAME)
    logger.debug(f"Obtained slot from db is {sdh_slot}. Resizing "
                 f"secondary windows ")
    twm.manage_secondary_windows(sdh_slot, SECONDARY_WINDOWS)


async def match_interrupt_template(area, template):
    frame = await capture_window(area)
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    cv.imshow(SECONDARY_WINDOWS[2].name, gray_frame)
    match_value = await compare_images(gray_frame, template)
    return match_value


async def capture_and_process_images(*args: tuple[dict, cv.typing.MatLike]) \
        -> list[float]:
    """Compares a set of screen areas and cv2 templates between them"""
    match_values = []

    for index, (capture_area, template) in enumerate(args):
        if capture_area is not None:
            frame = await capture_window(capture_area)
            gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

            if template is not None:
                match_value = await compare_images(gray_frame, template)
            else:
                match_value = 0.0

            window_index = index
            if window_index < len(SECONDARY_WINDOWS):
                cv.imshow(SECONDARY_WINDOWS[window_index].name, gray_frame)
            else:
                cv.namedWindow(f"Window_{window_index}")
                cv.imshow(f"Window_{window_index}", gray_frame)

            cv.waitKey(1)
            match_values.append(match_value)
            formatted_match_values = [f"{value:.4f}" for value in match_values]
            print(f"SSIMs: {formatted_match_values}", end="\r")

    initial_secondary_windows_spawned.set()

    return match_values


async def detect_hero_pick():
    pick_screen_match = await capture_and_process_images(
        (HERO_PICK_AREA, HERO_PICK_TEMPLATE)
    )
    return True if pick_screen_match[0] >= 0.7 else False


async def detect_starting_buy():
    starting_buy_match = await capture_and_process_images(
        (STARTING_BUY_AREA, STARTING_BUY_TEMPLATE))
    return True if starting_buy_match[0] >= 0.7 else False


async def detect_tab_out():
    dota_tabout_match, desktop_tabout_match = await capture_and_process_images(
        (DOTA_TAB_AREA, DOTA_TAB_TEMPLATE),
        (DESKTOP_TAB_AREA, DESKTOP_TAB_TEMPLATE)
    )
    return True if (dota_tabout_match >= 0.7
                    or desktop_tabout_match >= 0.7) else False


async def detect_settings_screen():
    settings_screen_match = await capture_and_process_images(
        (SETTINGS_AREA, SETTINGS_TEMPLATE)
    )
    return True if settings_screen_match[0] >= 0.7 else False


async def detect_vs_screen():
    vs_screen_match = await capture_and_process_images(
        (HERO_PICK_AREA, HERO_PICK_TEMPLATE),
        (SETTINGS_AREA, SETTINGS_TEMPLATE),
        (DOTA_TAB_AREA, DOTA_TAB_TEMPLATE),
        (DESKTOP_TAB_AREA, DESKTOP_TAB_TEMPLATE)
    )
    return True if max(vs_screen_match) < 0.7 else False


async def check_if_in_game():
    settings_screen_match, _ = await capture_and_process_images(
        (IN_GAME_AREA, IN_GAME_TEMPLATE)
    )
    return True if settings_screen_match >= 0.7 else False


async def wait_for_duration(duration):
    start_time = time.time()
    while time.time() - start_time < duration:
        elapsed_time = time.time() - start_time
        percentage = (elapsed_time / duration) * 100
        print(f"Waiting {duration}s... {percentage:.2f}%", end='\r')


async def capture_new_area(capture_area, filename):
    frame = await capture_window(capture_area)
    gray_frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    cv.imshow("new_area_capture", gray_frame)
    initial_secondary_windows_spawned.set()
    cv.imwrite(filename, gray_frame)


async def detect_pregame_phase(ws: websockets.WebSocketClientProtocol):
    new_capture = False  # Set manually to capture new screen area
    while new_capture:
        await capture_new_area(NEW_AREA, "opencv/XXX.jpg")

    game_phase = PreGamePhases()
    tabbed = Tabbed()

    while not stop_event.is_set():
        print("Waiting to find a game...")
        while not await detect_hero_pick():
            # look for initial game find
            print("test")
            await asyncio.sleep(0.01)
            continue
        print("Found a game !")

        await asyncio.sleep(0.01)
    pass


async def main():
    if single_instance.lock_exists(SCRIPT_NAME):
        slot = twm.manage_window(twm.WinType.DENIED, SCRIPT_NAME)
        atexit.register(denied_sdh.free_slot, slot)
        print("\n>>> Lock file is present: exiting... <<<")
    else:
        slot = twm.manage_window(twm.WinType.ACCEPTED,
                                 SCRIPT_NAME, SECONDARY_WINDOWS)
        single_instance.create_lock_file(SCRIPT_NAME)
        atexit.register(single_instance.remove_lock, SCRIPT_NAME)
        atexit.register(sdh.free_slot_named, SCRIPT_NAME)
        socket_server_task = asyncio.create_task(run_socket_server())
        mute_main_loop_print_feedback.set()
        ws = None
        try:
            ws = await establish_ws_connection()
            main_task = asyncio.create_task(detect_pregame_phase(ws))
            print("1")
            await initial_secondary_windows_spawned.wait()
            print("2")
            twm.manage_secondary_windows(slot, SECONDARY_WINDOWS)
            print("3")
            mute_main_loop_print_feedback.clear()
            await main_task
        except KeyboardInterrupt:
            print("KeyboardInterrupt")
        finally:
            socket_server_task.cancel()
            await socket_server_task
            cv.destroyAllWindows()
            if ws:
                await ws.close()


if __name__ == "__main__":
    asyncio.run(main())
    exit_countdown()
