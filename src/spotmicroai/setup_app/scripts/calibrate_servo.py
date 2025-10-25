#!/usr/bin/env python3
"""
Interactive servo calibration script.

Allows user to adjust servo parameters (min pulse, max pulse, rest angle, range)
using arrow keys and save the calibrated values to the configuration.

Usage: calibrate_servo_interactive.py <SERVO_ID> <MODE>
Modes: min, max, rest, range
"""

import curses
import sys
from enum import Enum

from spotmicroai.configuration import ServoName
from spotmicroai.setup_app import theme as THEME, ui_utils
from spotmicroai.setup_app.scripts.servo_controller import ServoController


class CalibrationMode(Enum):
    """Valid calibration modes."""

    MIN = "min"
    MAX = "max"
    REST = "rest"
    RANGE = "range"


def calibrate_minimum_pulse(stdscr, servo_controller: ServoController) -> bool:
    """Interactive calibration for minimum pulse width."""
    servo = servo_controller.servo

    # Start with current min pulse
    current_pulse = servo.min_pulse
    step = 10  # microseconds

    h, w = stdscr.getmaxyx()
    popup_height = 14
    popup_width = 70
    start_y = max(1, (h - popup_height) // 2)
    start_x = max(1, (w - popup_width) // 2)

    popup_win = curses.newwin(popup_height, popup_width, start_y, start_x)
    popup_win.keypad(True)
    popup_win.bkgd(' ', curses.color_pair(THEME.REGULAR_ROW))

    try:
        while True:
            popup_win.erase()
            popup_win.box()

            # Title
            title = f"Calibrate Minimum Pulse - {servo_controller.servo_name.value}"
            title_x = (popup_width - len(title)) // 2
            popup_win.addstr(1, title_x, title, curses.A_BOLD)

            # Separator
            popup_win.hline(2, 1, curses.ACS_HLINE, popup_width - 2)

            # Details
            details = [
                f"Current Min Pulse: {current_pulse} µs",
                f"Current Max Pulse: {servo.max_pulse} µs",
                f"Range: {servo.range}°",
                f"Rest Angle: {servo.rest_angle}°",
                "",
                "The servo will move to the minimum position.",
            ]

            for i, detail in enumerate(details):
                popup_win.addstr(4 + i, 3, detail)

            # Instructions
            popup_win.addstr(10, 3, f"↑/↓ adjust ±{step} µs", curses.A_DIM)
            popup_win.addstr(11, 3, "ENTER to save, ESC to cancel", curses.A_DIM)

            popup_win.refresh()

            # Set servo to minimum pulse position
            servo_controller.set_servo_pulse(current_pulse)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_pulse = servo_controller.clamp_pulse(current_pulse + step)
            elif key == curses.KEY_DOWN:
                current_pulse = servo_controller.clamp_pulse(current_pulse - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                servo_controller.config_provider.set_servo_min_pulse(servo_controller.servo_name, int(current_pulse))
                servo_controller.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_maximum_pulse(stdscr, servo_controller: ServoController) -> bool:
    """Interactive calibration for maximum pulse width."""
    servo = servo_controller.servo

    # Start with current max pulse
    current_pulse = servo.max_pulse
    step = 10  # microseconds

    h, w = stdscr.getmaxyx()
    popup_height = 14
    popup_width = 70
    start_y = max(1, (h - popup_height) // 2)
    start_x = max(1, (w - popup_width) // 2)

    popup_win = curses.newwin(popup_height, popup_width, start_y, start_x)
    popup_win.keypad(True)
    popup_win.bkgd(' ', curses.color_pair(THEME.REGULAR_ROW))

    try:
        while True:
            popup_win.erase()
            popup_win.box()

            # Title
            title = f"Calibrate Maximum Pulse - {servo_controller.servo_name.value}"
            title_x = (popup_width - len(title)) // 2
            popup_win.addstr(1, title_x, title, curses.A_BOLD)

            # Separator
            popup_win.hline(2, 1, curses.ACS_HLINE, popup_width - 2)

            # Details
            details = [
                f"Current Min Pulse: {servo.min_pulse} µs",
                f"Current Max Pulse: {current_pulse} µs",
                f"Range: {servo.range}°",
                f"Rest Angle: {servo.rest_angle}°",
                "",
                "The servo will move to the maximum position.",
            ]

            for i, detail in enumerate(details):
                popup_win.addstr(4 + i, 3, detail)

            # Instructions
            popup_win.addstr(10, 3, f"↑/↓ adjust ±{step} µs", curses.A_DIM)
            popup_win.addstr(11, 3, "ENTER to save, ESC to cancel", curses.A_DIM)

            popup_win.refresh()

            # Set servo to maximum pulse position
            servo_controller.set_servo_pulse(current_pulse)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_pulse = servo_controller.clamp_pulse(current_pulse + step)
            elif key == curses.KEY_DOWN:
                current_pulse = servo_controller.clamp_pulse(current_pulse - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                servo_controller.config_provider.set_servo_max_pulse(servo_controller.servo_name, int(current_pulse))
                servo_controller.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_rest_angle(stdscr, servo_controller: ServoController) -> bool:
    """Interactive calibration for rest angle."""
    servo = servo_controller.servo

    # Start with current rest angle
    current_angle = servo.rest_angle
    step = 1.0  # degrees

    h, w = stdscr.getmaxyx()
    popup_height = 14
    popup_width = 70
    start_y = max(1, (h - popup_height) // 2)
    start_x = max(1, (w - popup_width) // 2)

    popup_win = curses.newwin(popup_height, popup_width, start_y, start_x)
    popup_win.keypad(True)
    popup_win.bkgd(' ', curses.color_pair(THEME.REGULAR_ROW))

    try:
        while True:
            popup_win.erase()
            popup_win.box()

            # Title
            title = f"Calibrate Rest Angle - {servo_controller.servo_name.value}"
            title_x = (popup_width - len(title)) // 2
            popup_win.addstr(1, title_x, title, curses.A_BOLD)

            # Separator
            popup_win.hline(2, 1, curses.ACS_HLINE, popup_width - 2)

            # Calculate pulse width
            pulse_us = servo.min_pulse + (current_angle / servo.range) * (servo.max_pulse - servo.min_pulse)

            # Details
            details = [
                f"Current Rest Angle: {current_angle:.1f}°",
                f"Pulse Width: {pulse_us:.0f} µs",
                f"Min Pulse: {servo.min_pulse} µs",
                f"Max Pulse: {servo.max_pulse} µs",
                f"Range: {servo.range}°",
            ]

            for i, detail in enumerate(details):
                popup_win.addstr(4 + i, 3, detail)

            # Instructions
            popup_win.addstr(10, 3, f"↑/↓ adjust ±{step:.0f}°", curses.A_DIM)
            popup_win.addstr(11, 3, "ENTER to save, ESC to cancel", curses.A_DIM)

            popup_win.refresh()

            # Set servo to current angle
            servo_controller.set_servo_angle(current_angle)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_angle = servo_controller.clamp_angle(current_angle + step)
            elif key == curses.KEY_DOWN:
                current_angle = servo_controller.clamp_angle(current_angle - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                servo_controller.config_provider.set_servo_rest_angle(servo_controller.servo_name, int(current_angle))
                servo_controller.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_range(stdscr, servo_controller: ServoController) -> bool:
    """Interactive calibration for range."""
    servo = servo_controller.servo

    # Start with current range
    current_range = servo.range
    step = 5.0  # degrees

    h, w = stdscr.getmaxyx()
    popup_height = 14
    popup_width = 70
    start_y = max(1, (h - popup_height) // 2)
    start_x = max(1, (w - popup_width) // 2)

    popup_win = curses.newwin(popup_height, popup_width, start_y, start_x)
    popup_win.keypad(True)
    popup_win.bkgd(' ', curses.color_pair(THEME.REGULAR_ROW))

    try:
        while True:
            popup_win.erase()
            popup_win.box()

            # Title
            title = f"Calibrate Range - {servo_controller.servo_name.value}"
            title_x = (popup_width - len(title)) // 2
            popup_win.addstr(1, title_x, title, curses.A_BOLD)

            # Separator
            popup_win.hline(2, 1, curses.ACS_HLINE, popup_width - 2)

            # Details
            details = [
                f"Current Range: {current_range:.1f}°",
                f"Min Pulse: {servo.min_pulse} µs",
                f"Max Pulse: {servo.max_pulse} µs",
                f"Rest Angle: {servo.rest_angle}°",
                "",
                "This is the total actuation range of the servo.",
            ]

            for i, detail in enumerate(details):
                popup_win.addstr(4 + i, 3, detail)

            # Instructions
            popup_win.addstr(10, 3, f"↑/↓ adjust ±{step:.0f}°", curses.A_DIM)
            popup_win.addstr(11, 3, "ENTER to save, ESC to cancel", curses.A_DIM)

            popup_win.refresh()

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_range = max(1, current_range + step)
            elif key == curses.KEY_DOWN:
                current_range = max(1, current_range - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                servo_controller.config_provider.set_servo_range(servo_controller.servo_name, int(current_range))
                servo_controller.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def main(servo_id: str, mode: str) -> None:
    """Main entry point for interactive servo calibration."""
    try:
        # Validate servo ID
        try:
            servo_enum = ServoName(servo_id)
        except ValueError:
            print(f"Error: Invalid servo ID '{servo_id}'")
            print(f"Valid servo IDs: {', '.join([s.value for s in ServoName])}")
            sys.exit(1)

        # Validate mode
        try:
            calibration_mode = CalibrationMode(mode)
        except ValueError:
            valid_modes = [m.value for m in CalibrationMode]
            print(f"Error: Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")
            sys.exit(1)

        # Initialize the servo controller with the specific servo
        servo_controller = ServoController(servo_enum)

        # Run the appropriate calibration mode
        def calibration_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            stdscr.bkgd(' ', curses.color_pair(THEME.BACKGROUND))

            if calibration_mode == CalibrationMode.MIN:
                return calibrate_minimum_pulse(stdscr, servo_controller)
            elif calibration_mode == CalibrationMode.MAX:
                return calibrate_maximum_pulse(stdscr, servo_controller)
            elif calibration_mode == CalibrationMode.REST:
                return calibrate_rest_angle(stdscr, servo_controller)
            elif calibration_mode == CalibrationMode.RANGE:
                return calibrate_range(stdscr, servo_controller)

        result = curses.wrapper(calibration_wrapper)

        if result:
            print(f"\n✓ Successfully calibrated {servo_id} - {mode}")
        else:
            print(f"\n✗ Calibration cancelled for {servo_id} - {mode}")

    except KeyboardInterrupt:
        print("\n✗ Calibration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during calibration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: calibrate_servo_interactive.py <SERVO_ID> <MODE>")
        print("Modes: min, max, rest, range")
        sys.exit(1)

    servo_id_arg = sys.argv[1]
    mode_arg = sys.argv[2]
    main(servo_id_arg, mode_arg)
