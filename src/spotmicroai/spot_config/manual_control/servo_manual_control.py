#!/usr/bin/env python3
"""
Manual servo control for testing and motion verification.

Uses arrow keys to adjust the servo pulse in real time.
All safety limits (clamping, inversion) are enforced by the Servo class.
"""

import curses
import sys

from spotmicroai.configuration._config_provider import ServoName
from spotmicroai.constants import CALIBRATION_STEP_SIZE, POPUP_HEIGHT, POPUP_WIDTH
from spotmicroai.hardware.servo import ServoFactory
from spotmicroai.spot_config.ui import theme as THEME, ui_utils
import spotmicroai.labels as LABELS


class ServoManualControl:
    """Interactive manual servo control interface."""

    def __init__(self, stdscr, servo, servo_enum: ServoName):
        self.stdscr = stdscr
        self.servo = servo
        self.servo_enum = servo_enum
        self.formatted_servo_name = servo_enum.value.replace("_", " ").title()

    def get_popup_position(self):
        """Center the popup on screen."""
        h, w = self.stdscr.getmaxyx()
        start_y = max(1, (h - POPUP_HEIGHT) // 2)
        start_x = max(1, (w - POPUP_WIDTH) // 2)
        return start_y, start_x

    def create_popup_window(self):
        """Create a styled popup window."""
        start_y, start_x = self.get_popup_position()
        win = curses.newwin(POPUP_HEIGHT, POPUP_WIDTH, start_y, start_x)
        win.keypad(True)
        win.bkgd(" ", curses.color_pair(THEME.REGULAR_ROW))
        return win

    def run(self) -> bool:
        """Run manual control UI loop."""
        popup = self.create_popup_window()
        try:
            while True:
                popup.erase()
                popup.box()

                # Title
                title = LABELS.MANUAL_TITLE.format(self.formatted_servo_name)
                popup.addstr(1, (POPUP_WIDTH - len(title)) // 2, title, curses.A_BOLD)
                popup.hline(2, 1, curses.ACS_HLINE, POPUP_WIDTH - 2)

                # Calculate angles for display
                current_angle = round(self.servo.angle, 1)
                min_angle = round(self.servo.min_angle, 1)
                max_angle = round(self.servo.max_angle, 1)

                # Info
                popup.addstr(4, 3, LABELS.MANUAL_CURRENT_PULSE_WIDTH, curses.A_BOLD)
                popup.addstr(5, 3, f"  {self.servo.pulse} µs  ({current_angle}°)")

                popup.addstr(7, 3, LABELS.MANUAL_SERVO_RANGE)
                popup.addstr(
                    8,
                    3,
                    f"  Min: {self.servo.min_pulse} µs ({min_angle}°) | "
                    f"Max: {self.servo.max_pulse} µs ({max_angle}°)",
                )

                popup.addstr(10, 3, LABELS.MANUAL_REST_ANGLE)
                popup.addstr(11, 3, f"  {int(self.servo.rest_angle)}°")

                popup.addstr(
                    13,
                    3,
                    LABELS.MANUAL_ADJUST_INSTRUCTION.format(CALIBRATION_STEP_SIZE),
                    curses.A_DIM,
                )
                popup.addstr(14, 3, LABELS.MANUAL_EXIT_INSTRUCTION, curses.A_DIM)
                popup.refresh()

                # Key input
                key = popup.getch()
                if key == curses.KEY_UP:
                    step = CALIBRATION_STEP_SIZE if not self.servo.is_inverted else -CALIBRATION_STEP_SIZE
                    self.servo.pulse = self.servo.pulse + step
                elif key == curses.KEY_DOWN:
                    step = -CALIBRATION_STEP_SIZE if not self.servo.is_inverted else CALIBRATION_STEP_SIZE
                    self.servo.pulse = self.servo.pulse + step
                elif key == 27:  # ESC
                    return True

        finally:
            curses.endwin()


def main(servo_id: str) -> None:
    """CLI entry point for manual servo control."""
    try:
        try:
            servo_enum = ServoName(servo_id)
        except ValueError:
            print(LABELS.MANUAL_INVALID_SERVO_ID.format(servo_id))
            print(LABELS.MANUAL_VALID_SERVO_IDS.format(", ".join([s.value for s in ServoName])))
            sys.exit(1)

        servo = ServoFactory.create(servo_enum)

        def control_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            # Make the entire background blue
            stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
            stdscr.clear()
            stdscr.refresh()
            return ServoManualControl(stdscr, servo, servo_enum).run()

        result = curses.wrapper(control_wrapper)

        if result:
            print(LABELS.MANUAL_COMPLETED.format(servo_id))
        else:
            print(LABELS.MANUAL_CANCELLED.format(servo_id))

    except KeyboardInterrupt:
        print(LABELS.MANUAL_INTERRUPTED)
        sys.exit(1)
    except Exception as e:
        print(LABELS.MANUAL_ERROR.format(e))
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(LABELS.MANUAL_USAGE)
        sys.exit(1)

    main(sys.argv[1])
