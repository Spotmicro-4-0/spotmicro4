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

from spotmicroai.configuration import ConfigProvider, ServoName
from spotmicroai.drivers import PCA9685, Servo
from spotmicroai.setup_app import theme as THEME, ui_utils


class CalibrationMode(Enum):
    """Valid calibration modes."""

    MIN = "min"
    MAX = "max"
    REST = "rest"
    RANGE = "range"


class ServoCalibrator:
    """Manages a single servo hardware control and calibration."""

    def __init__(self, servo_name: ServoName):
        """
        Initialize the servo calibrator for a specific servo.

        Args:
            servo_name: The ServoName enum value for the servo to calibrate.
        """
        self.servo_name = servo_name
        self.config_provider = ConfigProvider()

        # Initialize PCA9685 board
        pca9685 = PCA9685()
        pca9685.activate_board()

        # Get the servo configuration
        servo_config = self.config_provider.get_servo(servo_name)
        channel = pca9685.get_channel(servo_config.channel)

        # Create the servo instance
        self.servo = Servo(
            channel,
            min_pulse=servo_config.min_pulse,
            max_pulse=servo_config.max_pulse,
            actuation_range=servo_config.range,
            rest_angle=servo_config.rest_angle,
        )

    @staticmethod
    def clamp_angle(angle: float) -> float:
        """Clamp angle to valid servo range (0-270 degrees)."""
        return max(0, min(270, angle))

    @staticmethod
    def clamp_pulse(pulse: float) -> float:
        """Clamp pulse width to valid range (500-2500 microseconds)."""
        return max(500, min(2500, pulse))

    def set_servo_angle(self, angle: float) -> float:
        """Move the servo to the provided angle."""
        target = self.clamp_angle(angle)
        self.servo.angle = target
        return target

    def set_servo_pulse(self, pulse_us: float) -> float:
        """Set servo pulse width directly (for min/max calibration)."""
        target = self.clamp_pulse(pulse_us)
        # Directly set pulse width using the channel
        self.servo.channel.duty_cycle = int((target / 20000) * 65535)
        return target


def calibrate_minimum_pulse(stdscr, calibrator: ServoCalibrator) -> bool:
    """Interactive calibration for minimum pulse width."""
    servo = calibrator.servo

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
            title = f"Calibrate Minimum Pulse - {calibrator.servo_name.value}"
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
            calibrator.set_servo_pulse(current_pulse)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_pulse = calibrator.clamp_pulse(current_pulse + step)
            elif key == curses.KEY_DOWN:
                current_pulse = calibrator.clamp_pulse(current_pulse - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                calibrator.config_provider.set_servo_min_pulse(calibrator.servo_name, int(current_pulse))
                calibrator.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_maximum_pulse(stdscr, calibrator: ServoCalibrator) -> bool:
    """Interactive calibration for maximum pulse width."""
    servo = calibrator.servo

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
            title = f"Calibrate Maximum Pulse - {calibrator.servo_name.value}"
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
            calibrator.set_servo_pulse(current_pulse)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_pulse = calibrator.clamp_pulse(current_pulse + step)
            elif key == curses.KEY_DOWN:
                current_pulse = calibrator.clamp_pulse(current_pulse - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                calibrator.config_provider.set_servo_max_pulse(calibrator.servo_name, int(current_pulse))
                calibrator.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_rest_angle(stdscr, calibrator: ServoCalibrator) -> bool:
    """Interactive calibration for rest angle."""
    servo = calibrator.servo

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
            title = f"Calibrate Rest Angle - {calibrator.servo_name.value}"
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
            calibrator.set_servo_angle(current_angle)

            key = popup_win.getch()

            if key == curses.KEY_UP:
                current_angle = calibrator.clamp_angle(current_angle + step)
            elif key == curses.KEY_DOWN:
                current_angle = calibrator.clamp_angle(current_angle - step)
            elif key in (curses.KEY_ENTER, 10, 13):
                # Save to config
                calibrator.config_provider.set_servo_rest_angle(calibrator.servo_name, int(current_angle))
                calibrator.config_provider.save_config()
                return True
            elif key == 27:  # ESC
                return False
    finally:
        curses.endwin()


def calibrate_range(stdscr, calibrator: ServoCalibrator) -> bool:
    """Interactive calibration for range."""
    servo = calibrator.servo

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
            title = f"Calibrate Range - {calibrator.servo_name.value}"
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
                calibrator.config_provider.set_servo_range(calibrator.servo_name, int(current_range))
                calibrator.config_provider.save_config()
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

        # Initialize calibrator with the specific servo
        calibrator = ServoCalibrator(servo_enum)

        # Run the appropriate calibration mode
        def calibration_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            stdscr.bkgd(' ', curses.color_pair(THEME.BACKGROUND))

            if calibration_mode == CalibrationMode.MIN:
                return calibrate_minimum_pulse(stdscr, calibrator)
            elif calibration_mode == CalibrationMode.MAX:
                return calibrate_maximum_pulse(stdscr, calibrator)
            elif calibration_mode == CalibrationMode.REST:
                return calibrate_rest_angle(stdscr, calibrator)
            elif calibration_mode == CalibrationMode.RANGE:
                return calibrate_range(stdscr, calibrator)

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
