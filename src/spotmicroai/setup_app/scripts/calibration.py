#!/usr/bin/env python3

import curses
import sys
from typing import Dict, Optional

try:
    from spotmicroai.configuration import ConfigProvider, ServoName
    from spotmicroai.drivers import PCA9685, Servo
    from spotmicroai.setup_app import labels as LABELS, theme as THEME, ui_utils
except ImportError as e:
    print(f"ERROR: Missing required dependencies: {e}", file=sys.stderr)
    print("\nPlease install dependencies with:", file=sys.stderr)
    print("  pip install -r spotmicroai/requirements.txt", file=sys.stderr)
    sys.exit(1)


class CalibrationUI:
    """Configuration constants for the calibration UI."""

    ANGLE_STEP_DEGREES = 1.0
    DEFAULT_SERVO_ANGLE = 135
    PANEL_WIDTH = 60
    PANEL_HEIGHT_BASE = 10
    MIN_WINDOW_HEIGHT = 20
    MIN_WINDOW_WIDTH = 70

    # UI Layout
    PANEL_TITLE_ROW = 1
    PANEL_TITLE_COL = 2
    PANEL_INSTRUCTION_ROW = 2
    PANEL_INSTRUCTION_COL = 2
    PANEL_SEPARATOR_ROW = 3
    PANEL_SEPARATOR_COL = 1
    OPTION_START_ROW = 4
    PROMPT_ROW_OFFSET = 5
    PANEL_LIST_COL = 2
    SERVO_INDEX_FORMAT = "2d"
    SERVO_NAME_WIDTH = 24
    ANGLE_DISPLAY_WIDTH = 5
    HLINE_PADDING = 2


_pca9685: Optional[PCA9685] = None
_servo_objects: Dict[str, Servo] = {}


# ============================================================
# HARDWARE CONTROL
# ============================================================
def init_servo_controller() -> None:
    """Initialise the PWM controller and create Servo objects."""
    global _pca9685, _servo_objects

    if _servo_objects:
        return

    _pca9685 = PCA9685()
    _pca9685.activate_board()
    config_provider = ConfigProvider()
    _servo_objects = {}

    for servo_name in ServoName:
        servo_config = config_provider.get_servo(servo_name)
        _servo_objects[servo_name.value] = Servo(
            _pca9685.get_channel(servo_config.channel),
            min_pulse=servo_config.min_pulse,
            max_pulse=servo_config.max_pulse,
            actuation_range=servo_config.range,
            rest_angle=servo_config.rest_angle,
        )


def clamp_angle(angle: float) -> float:
    return max(0, min(270, angle))


def set_servo_angle(name: str, angle: float) -> float:
    """Move the requested servo to the provided angle."""
    if _pca9685 is None:
        init_servo_controller()

    if name not in _servo_objects:
        raise KeyError(f"Servo '{name}' is not defined in hardware configuration.")

    target = clamp_angle(angle)
    _servo_objects[name].angle = target
    return target


# ============================================================
# SERVO ADJUSTMENT LOOP
# ============================================================
def servo_adjustment_loop(win, name, angle_memory, prompt_row):
    """Keep prompting for servo angles until the user opts to return."""
    exit_commands = {"b", "back", "exit"}
    angle_step = CalibrationUI.ANGLE_STEP_DEGREES

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

    # Get servo config for pulse width calculation
    config_provider = ConfigProvider()
    servo_name = ServoName(name)
    servo_config = config_provider.get_servo(servo_name)

    def angle_to_pulse_us(angle: float) -> float:
        """Convert angle to pulse width in microseconds."""
        min_pulse = servo_config.min_pulse
        max_pulse = servo_config.max_pulse
        actuation_range = servo_config.range
        return min_pulse + (angle / actuation_range) * (max_pulse - min_pulse)

    try:
        while True:
            win.attrset(curses.color_pair(THEME.REGULAR_ROW))

            # Calculate pulse width
            pulse_us = angle_to_pulse_us(current_angle)
            indent = CalibrationUI.PANEL_LIST_COL

            # Clear and draw instruction line
            ui_utils.CursesUIHelper.clear_line(win, prompt_row)
            instruction_text = LABELS.CAL_SERVO_ADJUST_INSTRUCTION.format(angle_step)
            ui_utils.CursesUIHelper.draw_text(win, prompt_row, indent, instruction_text)

            # Clear and draw angle/pulse line
            ui_utils.CursesUIHelper.clear_line(win, instruction_row)
            angle_text = LABELS.CAL_SERVO_DISPLAY.format(name, current_angle, pulse_us)
            ui_utils.CursesUIHelper.draw_text(win, instruction_row, indent, angle_text)

            # Clear and draw input buffer line
            ui_utils.CursesUIHelper.clear_line(win, input_row)
            input_text = f"{LABELS.CAL_INPUT_PROMPT}{input_buffer}"
            ui_utils.CursesUIHelper.draw_text(win, input_row, indent, input_text)

            # Clear and draw status message if present
            ui_utils.CursesUIHelper.clear_line(win, status_row)
            if status_message:
                ui_utils.CursesUIHelper.draw_text(win, status_row, indent, status_message)

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
                        status_message = LABELS.CAL_STATUS_REAPPLIED.format(name, current_angle)
                        continue

                    if entry.lower() in exit_commands:
                        break

                    try:
                        new_angle = float(entry)
                    except ValueError:
                        status_message = LABELS.CAL_STATUS_INVALID_ANGLE
                        continue

                    applied_angle = set_servo_angle(name, new_angle)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = LABELS.CAL_STATUS_MOVED.format(name, current_angle)

                elif key in ("\b", "\x7f", "\x08"):  # handle backspace variations
                    input_buffer = input_buffer[:-1]

                elif len(key) == 1 and (key.isdigit() or key in ".-+" or key.lower() in "bexta"):
                    input_buffer += key

                elif key == "\x1b":  # ESC
                    status_message = LABELS.CAL_STATUS_RETURNING
                    break

                else:
                    status_message = LABELS.CAL_STATUS_UNSUPPORTED_KEY

            else:  # Special keys (arrows, etc.)
                if key == curses.KEY_UP:
                    applied_angle = set_servo_angle(name, current_angle + angle_step)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = LABELS.CAL_STATUS_MOVED.format(name, current_angle)

                elif key == curses.KEY_DOWN:
                    applied_angle = set_servo_angle(name, current_angle - angle_step)
                    current_angle = applied_angle
                    angle_memory[name] = applied_angle
                    status_message = LABELS.CAL_STATUS_MOVED.format(name, current_angle)

                elif key in (curses.KEY_ENTER, 10, 13):
                    # Treat keypad enter the same as newline
                    input_buffer = ""
                    current_angle = set_servo_angle(name, current_angle)
                    angle_memory[name] = current_angle
                    status_message = LABELS.CAL_STATUS_REAPPLIED.format(name, current_angle)

                else:
                    status_message = LABELS.CAL_STATUS_UNSUPPORTED_KEY

    finally:
        # Clean up prompt area before returning to menu
        ui_utils.CursesUIHelper.clear_line(win, prompt_row)
        ui_utils.CursesUIHelper.clear_line(win, instruction_row)
        ui_utils.CursesUIHelper.clear_line(win, input_row)
        ui_utils.CursesUIHelper.clear_line(win, status_row)
        win.refresh()


# ============================================================
# MAIN MENU
# ============================================================
def main_menu(stdscr):
    """Main calibration menu loop."""
    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()

    # Initialize colors using the shared theme
    ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)

    stdscr.keypad(True)
    stdscr.bkgd(' ', curses.color_pair(THEME.BACKGROUND))
    stdscr.attrset(curses.color_pair(THEME.BACKGROUND))

    servo_names = [servo.value for servo in ServoName] + [LABELS.CAL_EXIT_LABEL]
    selected = 0
    num_items = len(servo_names)
    angle_memory = {name: CalibrationUI.DEFAULT_SERVO_ANGLE for name in [servo.value for servo in ServoName]}

    init_servo_controller()

    max_y, max_x = stdscr.getmaxyx()
    panel_height = num_items + CalibrationUI.PANEL_HEIGHT_BASE
    panel_width = CalibrationUI.PANEL_WIDTH

    is_valid, error_msg = ui_utils.CursesUIHelper.validate_terminal_size(
        max_y, max_x, CalibrationUI.MIN_WINDOW_HEIGHT, CalibrationUI.MIN_WINDOW_WIDTH
    )

    if not is_valid:
        stdscr.clear()
        stdscr.addstr(0, 0, error_msg)
        stdscr.refresh()
        stdscr.getch()
        return

    top = (max_y - panel_height) // 2
    left = (max_x - panel_width) // 2
    panel_win = curses.newwin(panel_height, panel_width, top, left)
    panel_win.keypad(True)
    panel_win.bkgd(' ', curses.color_pair(THEME.REGULAR_ROW))
    panel_win.attrset(curses.color_pair(THEME.REGULAR_ROW))

    while True:
        stdscr.erase()
        stdscr.attrset(curses.color_pair(THEME.BACKGROUND))
        stdscr.refresh()

        panel_win.erase()
        panel_win.attrset(curses.color_pair(THEME.REGULAR_ROW))
        panel_win.box()

        # Draw title
        ui_utils.CursesUIHelper.draw_text(
            panel_win,
            CalibrationUI.PANEL_TITLE_ROW,
            CalibrationUI.PANEL_TITLE_COL,
            LABELS.CAL_TITLE,
            attrs=curses.A_BOLD,
        )

        # Draw instruction
        ui_utils.CursesUIHelper.draw_text(
            panel_win,
            CalibrationUI.PANEL_INSTRUCTION_ROW,
            CalibrationUI.PANEL_INSTRUCTION_COL,
            LABELS.CAL_INSTRUCTION,
        )

        # Draw separator
        try:
            panel_win.hline(
                CalibrationUI.PANEL_SEPARATOR_ROW,
                CalibrationUI.PANEL_SEPARATOR_COL,
                curses.ACS_HLINE,
                panel_width - CalibrationUI.HLINE_PADDING,
            )
        except curses.error:
            pass

        # Draw servo list
        option_start_row = CalibrationUI.OPTION_START_ROW
        line_width = panel_width - 4
        for i, name in enumerate(servo_names):
            row = option_start_row + i
            if name == LABELS.CAL_EXIT_LABEL:
                text = f"  {LABELS.CAL_EXIT_SHORTCUT}. {LABELS.CAL_EXIT_LABEL}"
            else:
                text = (
                    f" {i+1:{CalibrationUI.SERVO_INDEX_FORMAT}}. "
                    f"{name:<{CalibrationUI.SERVO_NAME_WIDTH}}  "
                    f"[{angle_memory[name]:>{CalibrationUI.ANGLE_DISPLAY_WIDTH}.1f}°]"
                )
            padded_text = text.ljust(line_width)

            if i == selected:
                ui_utils.CursesUIHelper.draw_highlighted_text(
                    panel_win, row, CalibrationUI.PANEL_LIST_COL, padded_text[:line_width]
                )
            else:
                ui_utils.CursesUIHelper.draw_text(
                    panel_win, row, CalibrationUI.PANEL_LIST_COL, padded_text[:line_width]
                )

        panel_win.refresh()

        key = panel_win.getch()

        if key == curses.KEY_UP:
            selected = (selected - 1) % num_items
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % num_items
        elif key in (ord("q"), ord("Q"), 27):  # q/Q or ESC
            break
        elif key in (curses.KEY_ENTER, 10, 13):
            name = servo_names[selected]
            if name == LABELS.CAL_EXIT_LABEL:
                break

            prompt_row = num_items + CalibrationUI.PROMPT_ROW_OFFSET
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
