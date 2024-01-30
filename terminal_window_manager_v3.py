"""
Module used to transform the terminal windows of running scripts so that they
fit my screen nicely on my second monitor, in accordance with the amount of
windows already present
"""
import time
import pygetwindow as gw
import os
import slots_db_handler as sdh
import win32gui
import win32con
from enum import Enum, auto
import re


class WindowType(Enum):
    DENIED_SCRIPT = auto()
    ACCEPTED_SCRIPT = auto()
    RUNNING_SCRIPT = auto()
    SERVER = auto()


def assign_slot_and_rename_window(name: str) -> (int, str):
    """
    Assign a slot in the database to the terminal window that just spawned
    and rename it accordingly.
    """

    slot_assigned = sdh.occupy_first_free_slot()
    if slot_assigned is not None:
        new_window_title = f"{name} - slot {slot_assigned}"
        os.system(f"title {new_window_title}")

        # Register that new name in the database
        sdh.name_slot(slot_assigned, new_window_title)

        return slot_assigned, new_window_title
    else:
        raise ValueError(f"slot assigned was {type(slot_assigned)}. "
                         f"Could not assign to a slot.")


def join_secondaries_to_main_window(main_slot: int,
                                    secondary_windows: list[str]):
    """
    Adjust the positions of the secondary windows that spawn from the
     main script, so that they fit on top of the latter.
    :param main_slot: The slot attributed to the main window in the
    database.
    :param secondary_windows: List of the secondary window names.
    """
    for i in range(0, len(secondary_windows)):
        width = 150  # fixed size, might change in the future
        height = 150
        x_pos = (-600 * (1 + main_slot // 4)) + (3 - i) * 150
        y_pos = 260 * (main_slot % 4)
        properties = (width, height, x_pos, y_pos)
        # Move without resizing
        resize_and_move_window(secondary_windows[i], properties, False)


def calculate_new_window_properties(slot_number: int) \
        -> tuple[int, int, int, int]:
    width = 600
    height = 260
    x_pos = -600 * (1 + slot_number // 4)
    y_pos = 260 * (slot_number % 4)

    return width, height, x_pos, y_pos


def resize_and_move_window(window_title: str,
                           new_properties: tuple[int, int, int, int],
                           resize: bool = True,
                           move: bool = True):
    """ Reposition and/or and transform a window"""
    new_width, new_height, new_x, new_y = new_properties

    timeout = 3  # time-out time for while loop
    start_time = time.time()

    # Poll for the recently renamed window: sometimes, it needs a bit of time
    # to be found because the rename is not instantaneous
    while True:
        if time.time() - start_time > timeout:
            print("Window Search timed out.")
            break

        window = gw.getWindowsWithTitle(window_title)
        if window:
            window = window[0]
            window.restore()  # in case it was minimized
            if resize:
                window.resizeTo(new_width, new_height)
            if move:
                window.moveTo(new_x, new_y)
            break
        else:
            print(f"Window '{window_title}' not found. trying again",
                  end="\r")
            time.sleep(0.01)  # limit the speed of the loop


def set_windows_to_topmost():
    """Set all the cmd windows of the running scripts to be topmost"""
    windows_names_list = sdh.get_all_names()
    windows_names_list.append("SERVER")

    # Reverse the order of the list in order to have the secondary windows
    # displayed  over the main window when set to "TOPMOST" (the first
    # windows passed to SetWindowPos get "TOPMOST" priority)
    windows_names_list.reverse()

    for name in windows_names_list:
        window = win32gui.FindWindow(None, name)
        if window:
            win32gui.SetWindowPos(window,
                                  win32con.HWND_TOPMOST,
                                  0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def unset_windows_to_topmost():
    """Set terminal windows fore/background behavior back to normal"""
    windows_names_list = sdh.get_all_names()
    windows_names_list.append("SERVER")

    for name in windows_names_list:
        window = win32gui.FindWindow(None, name)
        if window:
            win32gui.SetWindowPos(window,
                                  win32con.HWND_NOTOPMOST,
                                  0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)


def close_window(slot):
    # Free up the occupied database slot
    sdh.free_slot(slot)


def get_all_windows_titles():
    print(gw.getAllTitles())


def adjust_window(window_type: WindowType, window_name: str,
                  secondary_windows: list[str] = None) -> int:
    """
    Decide which the recently spawned terminal window is of the following:

    1. A denied script that will soon exit automatically. (lock file)
    2. An accepted script that will give continuous feedback.
    3. An already running script that needs to be repositioned.
    4. The server script.

    And adjust the terminal window accordingly
    """

    if window_type == WindowType.DENIED_SCRIPT:
        pass

    elif window_type == WindowType.ACCEPTED_SCRIPT:
        slot, title = assign_slot_and_rename_window(window_name)
        properties = calculate_new_window_properties(slot)
        resize_and_move_window(title, properties)
        if secondary_windows:
            sdh.name_secondary_windows(slot, secondary_windows)
            # Note: the secondary windows positions cannot be adjusted at the
            # script launch, since they usually appear later, after some script
            # logic has been executed.
        return slot

    elif window_type == WindowType.SERVER:
        os.system(f"title SERVER")  # make sure the SERVER cmd prompt is,
        # in fact, named "SERVER"
        time.sleep(0.2)  # give time to windows for renaming the cmd
        server_window = win32gui.FindWindow(None, "SERVER")
        win32gui.SetWindowPos(server_window, None, -1920, 640, 700, 400, 0)


def readjust_windows():
    """Look if they are free slots before the ones currently displayed. If
    there are some, move the windows to fill those earlier slots."""

    # Look for free and occupied slots
    free_slots = sdh.get_all_free_slots_ids()
    occupied_slots = sdh.get_all_occupied_slots_id()

    # Check if the latest occupied slot is higher than the earliest free slot.
    # E.g. slot 7 occupied while slot 3 is free
    occupied_slots.reverse()
    if free_slots:
        for i in range(0, len(free_slots)):
            if occupied_slots[i] > free_slots[i]:
                names = sdh.get_full_window_names(occupied_slots[i])
                sdh.occupy_slot(free_slots[i], names)
                sdh.free_slot(occupied_slots[i])

                # Once the new slot is, taken get the main window name
                main_name = sdh.get_main_window_name(occupied_slots[i])
                # Remove the previous " - slot X" suffix
                if main_name is not None:
                    pattern = r' - slot \d+'
                    main_name = re.sub(pattern, "", main_name)
                # Add the new suffix in accordance to new slot taken
                new_main_title = f"{main_name} - slot {free_slots[i]}"
                os.system(f"title {new_main_title}")
            else:
                print(f"slot {free_slots[i]} is free but comes later than "
                      f"latest slot {occupied_slots[i]} occupied")
                break

    else:
        print('no free slots found')


def main():
    slot, title = assign_slot_and_rename_window("test")
    properties = calculate_new_window_properties(slot)
    resize_and_move_window(title, properties)
    input("press enter to close and free the slot")
    close_window(slot)


if __name__ == '__main__':
    readjust_windows()
