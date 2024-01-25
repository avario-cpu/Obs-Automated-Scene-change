"""
Module used to transform the terminal windows of running scripts so that they
fit my screen nicely on my second monitor, in accordance with the amount of
windows already present
"""

import time
import pygetwindow as gw
import os
import slots_db_handler


def resize_and_move_window(window_title, new_properties):
    new_width, new_height, new_x, new_y = new_properties

    # Set a time-out time for the loop to exist
    timeout = 3
    start_time = time.time()

    # Poll for the window recently renamed.
    while True:
        if time.time() - start_time > timeout:
            print("Window Search timed out.")
            break

        # Obtain a list with the matching title windows
        window = gw.getWindowsWithTitle(window_title)
        if window:
            window = window[0]
            window.resizeTo(new_width, new_height)
            window.moveTo(new_x, new_y)
            break
        else:
            print(f"Window "'{window_title}'" not found. trying again")
            time.sleep(0.01)  # limit the speed of the loop


def assign_slot_and_rename_window() -> (int, str):
    """assign a slot to the cmd window that just spawned
    and rename it accordingly."""

    # Assign a slot number to the terminal window
    slot_assigned = slots_db_handler.populate_first_free_slot()
    if slot_assigned:
        # Rename the terminal window if a slot was found
        new_window_title = "MYNAME" + str(slot_assigned)
        os.system(f"title {new_window_title}")
        return slot_assigned, new_window_title,
    else:
        raise ValueError(f"{slot_assigned} was {type(slot_assigned)}. "
                         f"Could not assign to a slot.")


def calculate_new_window_properties(slot_number) -> tuple:
    # Check that the parameter is an integer
    if not isinstance(slot_number, int):
        raise TypeError("slot_number must be of type int")

    # Use the slot number to calculate the desired new position and size
    width = 600
    height = 260
    x_pos = -600 * (1 + slot_number // 4)
    y_pos = 260 * (slot_number % 4)

    return width, height, x_pos, y_pos


def free_slot(slot):
    # Free up the occupied slot when the window is closed
    slots_db_handler.free_occupied_slot(slot)


def adjust_window() -> int:
    try:
        slot, title = assign_slot_and_rename_window()
        properties = calculate_new_window_properties(slot)
        resize_and_move_window(title, properties)
        return slot
    except ValueError as e:
        print(e)


def close_window(slot):
    free_slot(slot)


def main():
    slot, title = assign_slot_and_rename_window()
    properties = calculate_new_window_properties(slot)
    resize_and_move_window(title, properties)
    input("press enter to close and free the slot")
    free_slot(slot)


if __name__ == '__main__':
    main()

# slots_db_handler.free_all_occupied_slots()