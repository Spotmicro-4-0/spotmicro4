#!/usr/bin/env python3

import curses
from typing import Dict, Optional

from pca9685 import PCA9685
from servo import Servo


class CalibrationHardwareConfig:
    I2C_ADDR = 0x40
    NEUTRAL_ANGLE = 135.0  # Midpoint for 1500us on a 270° servo
    PWM_FREQUENCY = 50
    MIN_PULSE_US = 500
    MAX_PULSE_US = 2500
    ACTUATION_RANGE_DEGREES = 270
    MIN_ANGLE = 0.0
    MAX_ANGLE = 270.0
    SERVOS = {
        "front_shoulder_left": 6,
        "front_leg_left": 7,
        "front_foot_left": 8,
        "front_shoulder_right": 9,
        "front_leg_right": 10,
        "front_foot_right": 11,
        "rear_shoulder_left": 3,
        "rear_leg_left": 4,
        "rear_foot_left": 5,
        "rear_shoulder_right": 0,
        "rear_leg_right": 1,
        "rear_foot_right": 2,
    }


class CalibrationUIConfig:
    HIGHLIGHTED_ROW_PAIR = 1
    INFO_TEXT_PAIR = 2
    SCREEN_BACKGROUND_PAIR = 3
    PANEL_BACKGROUND_PAIR = 4
    EXIT_COMMANDS = {"b", "back", "exit"}
    ESCAPE_CHAR = "\x1b"
    ADDITIONAL_INPUT_CHARACTERS = {".", "-", "+"}
    EXIT_COMMAND_CHARACTERS = set("".join(EXIT_COMMANDS))
    ANGLE_STEP_DEGREES = 1.0
    EXIT_OPTION_LABEL = "Exit"
    EXIT_SHORTCUT_KEY = "q"
    DEFAULT_SERVO_ANGLE = CalibrationHardwareConfig.NEUTRAL_ANGLE
    PANEL_EXTRA_HEIGHT = 10
    PANEL_WIDTH = 60
    MIN_WINDOW_MARGIN = 2
    OPTION_START_ROW = 4
    PROMPT_ROW_OFFSET = 5
    LIST_PADDING = 4
    PANEL_TITLE_ROW = 1
    PANEL_TITLE_COL = 2
    PANEL_INSTRUCTION_ROW = 2
    PANEL_INSTRUCTION_COL = 2
    PANEL_SEPARATOR_ROW = 3
    PANEL_SEPARATOR_COL = 1
    PANEL_TITLE_TEXT = "=== Servo Calibration Menu ==="
    PANEL_INSTRUCTION_TEXT = "Use ↑ ↓ to select, ENTER to set angle, q/ESC to quit"
    SERVO_INDEX_FORMAT = "2d"
    SERVO_NAME_WIDTH = 24
    ANGLE_DISPLAY_WIDTH = 5
    QUIT_KEY_CODES = (ord("q"), ord("Q"), 27)
    ENTER_KEY_CODES = (10, 13)
    HLINE_PADDING = 2
    PANEL_LIST_COL = 2
    INPUT_PROMPT_LABEL = "Input: "


_pca9685: Optional[PCA9685] = None
_servo_objects: Dict[str, Servo] = {}


# ============================================================
# HARDWARE CONTROL
# ============================================================
def init_servo_controller() -> None:
    """Initialise the PWM controller and create Servo objects."""
    global _pca9685, _servo_objects

    if _pca9685 is None:
        _pca9685 = PCA9685(
            CalibrationHardwareConfig.I2C_ADDR,
            CalibrationHardwareConfig.PWM_FREQUENCY,
        )

    if _servo_objects:
        return

    for name, channel in CalibrationHardwareConfig.SERVOS.items():
        _servo_objects[name] = Servo(
            _pca9685.channel(channel),
            min_pulse=CalibrationHardwareConfig.MIN_PULSE_US,
            max_pulse=CalibrationHardwareConfig.MAX_PULSE_US,
            actuation_range=CalibrationHardwareConfig.ACTUATION_RANGE_DEGREES,
            neutral_angle=CalibrationHardwareConfig.NEUTRAL_ANGLE,
            min_angle=CalibrationHardwareConfig.MIN_ANGLE,
            max_angle=CalibrationHardwareConfig.MAX_ANGLE,
        )


def clamp_angle(angle: float) -> float:
    return max(
        CalibrationHardwareConfig.MIN_ANGLE,
        min(CalibrationHardwareConfig.MAX_ANGLE, angle),
    )


def set_servo_angle(name: str, angle: float) -> float:
    """
    Move the requested servo to the provided angle using the Adafruit Servo helper.
    """
    if _pca9685 is None:
        init_servo_controller()

    if name not in _servo_objects:
        raise KeyError(f"Servo '{name}' is not defined in hardware configuration.")

    target = clamp_angle(angle)
    return _servo_objects[name].set_angle(target)


# ============================================================
# MAIN MENU LOGIC
# ============================================================
def servo_adjustment_loop(win, name, angle_memory, prompt_row):
    """Keep prompting for servo angles until the user opts to return."""
    exit_commands = CalibrationUIConfig.EXIT_COMMANDS
    angle_step = CalibrationUIConfig.ANGLE_STEP_DEGREES

    curses.noecho()
    win.keypad(True)

    input_buffer = ""
    status_message = ""
    current_angle = angle_memory[name]
    current_angle = set_servo_angle(name, current_angle)
    angle_memory[name] = current_angle
    instruction_row = prompt_row + 1
    input_row = prompt_row + 2
    status_row = prompt_row + 3

    try:
        while True:
            win.attrset(curses.color_pair(CalibrationUIConfig.PANEL_BACKGROUND_PAIR))

            # Draw prompt line
            win.move(prompt_row, 0)
            win.clrtoeol()
            win.addstr(
                prompt_row,
                0,
                f"{name} angle: {current_angle:.1f}°  (default is last set value)",
            )

            # Draw instruction line
            win.move(instruction_row, 0)
            win.clrtoeol()
            win.addstr(
                instruction_row,
                0,
                f"↑/↓ adjust ±{angle_step:.0f}°. ENTER moves. b/ESC exits.",
            )

            # Draw input buffer line
            win.move(input_row, 0)
            win.clrtoeol()
            win.addstr(
                input_row,
                0,
                f"{CalibrationUIConfig.INPUT_PROMPT_LABEL}{input_buffer}",
            )

            # Draw status message if present
            win.move(status_row, 0)
            win.clrtoeol()
            if status_message:
                win.addstr(status_row, 0, status_message)

            win.refresh()
            status_message = ""

            key = win.get_wch()

            # Handle printable characters and control codes
            if isinstance(key, str):
                if key in ("\n", "\r"):
                    entry = input_buffer.strip()
                    input_buffer = ""

                    if entry == "":
                        # Reapply current angle for quick confirmation
                        current_angle = set_servo_angle(name, current_angle)
                        angle_memory[name] = current_angle
                        status_message = f"Reapplied {name} to {current_angle:.1f}°"
                        continue

                    if entry.lower() in exit_commands:
                        break

                    try:
                        new_angle = float(entry)
                    except ValueError:
                        status_message = "Invalid angle. Use a numeric value."
                        continue

                    applied_angle = set_servo_angle(name, new_angle)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = f"Moved {name} to {current_angle:.1f}°"

                elif key in ("\b", "\x7f", "\x08"):  # handle backspace variations
                    input_buffer = input_buffer[:-1]

                elif len(key) == 1 and (
                    key.isdigit()
                    or key in CalibrationUIConfig.ADDITIONAL_INPUT_CHARACTERS
                    or key.lower() in CalibrationUIConfig.EXIT_COMMAND_CHARACTERS
                ):
                    input_buffer += key

                elif key == CalibrationUIConfig.ESCAPE_CHAR:  # ESC clears current buffer
                    status_message = "Returning to menu."
                    break

                else:
                    status_message = "Unsupported key. Use digits, ENTER, arrows, or b/ESC."

            else:  # Special keys (arrows, etc.)
                if key == curses.KEY_UP:
                    applied_angle = set_servo_angle(name, current_angle + angle_step)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = f"Moved {name} to {current_angle:.1f}°"

                elif key == curses.KEY_DOWN:
                    applied_angle = set_servo_angle(name, current_angle - angle_step)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = f"Moved {name} to {current_angle:.1f}°"

                elif key == curses.KEY_ENTER:
                    # Treat keypad enter the same as newline
                    input_buffer = ""
                    current_angle = set_servo_angle(name, current_angle)
                    angle_memory[name] = current_angle
                    status_message = f"Reapplied {name} to {current_angle:.1f}°"

                else:
                    status_message = "Unsupported key. Use digits, ENTER, arrows, or b/ESC."

    finally:
        # Clean up prompt area before returning to menu
        win.move(prompt_row, 0)
        win.clrtoeol()
        win.move(instruction_row, 0)
        win.clrtoeol()
        win.move(input_row, 0)
        win.clrtoeol()
        win.move(status_row, 0)
        win.clrtoeol()
        win.refresh()


def main_menu(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(
        CalibrationUIConfig.HIGHLIGHTED_ROW_PAIR,
        curses.COLOR_WHITE,
        curses.COLOR_RED,
    )
    curses.init_pair(
        CalibrationUIConfig.INFO_TEXT_PAIR,
        curses.COLOR_BLACK,
        curses.COLOR_WHITE,
    )
    curses.init_pair(
        CalibrationUIConfig.SCREEN_BACKGROUND_PAIR,
        curses.COLOR_WHITE,
        curses.COLOR_BLUE,
    )
    curses.init_pair(
        CalibrationUIConfig.PANEL_BACKGROUND_PAIR,
        curses.COLOR_BLACK,
        curses.COLOR_WHITE,
    )
    stdscr.keypad(True)
    stdscr.bkgd(" ", curses.color_pair(CalibrationUIConfig.SCREEN_BACKGROUND_PAIR))
    stdscr.attrset(curses.color_pair(CalibrationUIConfig.SCREEN_BACKGROUND_PAIR))

    servo_names = list(CalibrationHardwareConfig.SERVOS.keys()) + [CalibrationUIConfig.EXIT_OPTION_LABEL]
    selected = 0
    num_items = len(servo_names)
    angle_memory = {
        name: CalibrationUIConfig.DEFAULT_SERVO_ANGLE for name in CalibrationHardwareConfig.SERVOS.keys()
    }  # remember angles only for servos

    init_servo_controller()

    max_y, max_x = stdscr.getmaxyx()
    panel_height = num_items + CalibrationUIConfig.PANEL_EXTRA_HEIGHT
    panel_width = CalibrationUIConfig.PANEL_WIDTH
    required_height = panel_height + CalibrationUIConfig.MIN_WINDOW_MARGIN
    required_width = panel_width + CalibrationUIConfig.MIN_WINDOW_MARGIN
    if required_height > max_y or required_width > max_x:
        stdscr.clear()
        stdscr.addstr(0, 0, "Terminal window too small for interface.")
        stdscr.addstr(1, 0, f"Requires at least {required_height}x{required_width}.")
        stdscr.refresh()
        stdscr.getch()
        return

    top = (max_y - panel_height) // 2
    left = (max_x - panel_width) // 2
    panel_win = curses.newwin(panel_height, panel_width, top, left)
    panel_win.keypad(True)
    panel_win.bkgd(" ", curses.color_pair(CalibrationUIConfig.PANEL_BACKGROUND_PAIR))
    panel_win.attrset(curses.color_pair(CalibrationUIConfig.PANEL_BACKGROUND_PAIR))

    while True:
        stdscr.erase()
        stdscr.attrset(curses.color_pair(CalibrationUIConfig.SCREEN_BACKGROUND_PAIR))
        stdscr.refresh()

        panel_win.erase()
        panel_win.attrset(curses.color_pair(CalibrationUIConfig.PANEL_BACKGROUND_PAIR))
        panel_win.box()
        panel_win.addstr(
            CalibrationUIConfig.PANEL_TITLE_ROW,
            CalibrationUIConfig.PANEL_TITLE_COL,
            CalibrationUIConfig.PANEL_TITLE_TEXT,
            curses.A_BOLD | curses.color_pair(CalibrationUIConfig.INFO_TEXT_PAIR),
        )
        panel_win.addstr(
            CalibrationUIConfig.PANEL_INSTRUCTION_ROW,
            CalibrationUIConfig.PANEL_INSTRUCTION_COL,
            CalibrationUIConfig.PANEL_INSTRUCTION_TEXT,
            curses.color_pair(CalibrationUIConfig.INFO_TEXT_PAIR),
        )
        panel_win.hline(
            CalibrationUIConfig.PANEL_SEPARATOR_ROW,
            CalibrationUIConfig.PANEL_SEPARATOR_COL,
            curses.ACS_HLINE,
            panel_width - CalibrationUIConfig.HLINE_PADDING,
        )

        # Draw servo list inside panel
        option_start_row = CalibrationUIConfig.OPTION_START_ROW
        line_width = panel_width - CalibrationUIConfig.LIST_PADDING
        for i, name in enumerate(servo_names):
            row = option_start_row + i
            if name == CalibrationUIConfig.EXIT_OPTION_LABEL:
                text = f"  {CalibrationUIConfig.EXIT_SHORTCUT_KEY}. {CalibrationUIConfig.EXIT_OPTION_LABEL}"
            else:
                text = (
                    f" {i+1:{CalibrationUIConfig.SERVO_INDEX_FORMAT}}. "
                    f"{name:<{CalibrationUIConfig.SERVO_NAME_WIDTH}}  "
                    f"[{angle_memory[name]:>{CalibrationUIConfig.ANGLE_DISPLAY_WIDTH}.1f}°]"
                )
            padded_text = text.ljust(line_width)
            if i == selected:
                panel_win.addstr(
                    row,
                    CalibrationUIConfig.PANEL_LIST_COL,
                    padded_text[:line_width],
                    curses.color_pair(CalibrationUIConfig.HIGHLIGHTED_ROW_PAIR),
                )
            else:
                panel_win.addstr(
                    row,
                    CalibrationUIConfig.PANEL_LIST_COL,
                    padded_text[:line_width],
                )

        panel_win.refresh()

        key = panel_win.getch()

        if key == curses.KEY_UP:
            selected = (selected - 1) % num_items
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % num_items
        elif key in CalibrationUIConfig.QUIT_KEY_CODES:
            break
        elif key in CalibrationUIConfig.ENTER_KEY_CODES:
            name = servo_names[selected]
            if name == CalibrationUIConfig.EXIT_OPTION_LABEL:
                break  # Exit option chosen

            prompt_row = num_items + CalibrationUIConfig.PROMPT_ROW_OFFSET
            servo_adjustment_loop(panel_win, name, angle_memory, prompt_row)

        panel_win.refresh()


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    try:
        curses.wrapper(main_menu)
    except KeyboardInterrupt:
        print("\nCalibration terminated.")
