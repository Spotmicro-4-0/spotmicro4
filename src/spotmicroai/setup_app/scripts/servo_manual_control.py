#!/usr/bin/env python3
"""
Manual servo control for testing and motion verification.

Allows real-time servo movement using arrow keys to adjust pulse width.
Useful for verifying servo range and motion before full calibration.

Usage: servo_manual_control.py <SERVO_ID>
"""

import curses
import sys

from spotmicroai.configuration import ServoName
from spotmicroai.setup_app import theme as THEME, ui_utils
from spotmicroai.setup_app.scripts.servo_calibrator import ServoCalibrator


class ServoManualControl:
    """Interactive manual servo control interface."""

    POPUP_HEIGHT = 16
    POPUP_WIDTH = 75
    STEP_SIZE = 10  # microseconds per adjustment

    def __init__(self, stdscr, calibrator: ServoCalibrator):
        """Initialize manual control interface.

        Args:
            stdscr: curses window object
            calibrator: ServoCalibrator instance for servo control
        """
        self.stdscr = stdscr
        self.calibrator = calibrator
        # Start at the midpoint between min and max pulse
        self.current_pulse = (calibrator.servo.min_pulse + calibrator.servo.max_pulse) // 2

    def get_popup_position(self):
        """Calculate centered popup position."""
        h, w = self.stdscr.getmaxyx()
        start_y = max(1, (h - self.POPUP_HEIGHT) // 2)
        start_x = max(1, (w - self.POPUP_WIDTH) // 2)
        return start_y, start_x

    def create_popup_window(self):
        """Create and configure a popup window."""
        start_y, start_x = self.get_popup_position()
        popup_win = curses.newwin(self.POPUP_HEIGHT, self.POPUP_WIDTH, start_y, start_x)
        popup_win.keypad(True)
        popup_win.bkgd(" ", curses.color_pair(THEME.REGULAR_ROW))
        return popup_win

    def run(self) -> bool:
        """Run the manual control loop.

        Returns:
            True if completed successfully, False if cancelled.
        """
        popup_win = self.create_popup_window()

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                # Title
                title = f"Manual Servo Control - {self.calibrator.servo_name.value}"
                title_x = (self.POPUP_WIDTH - len(title)) // 2
                popup_win.addstr(1, title_x, title, curses.A_BOLD)

                # Separator
                popup_win.hline(2, 1, curses.ACS_HLINE, self.POPUP_WIDTH - 2)

                # Current status
                popup_win.addstr(4, 3, "Current Pulse Width:", curses.A_BOLD)
                popup_win.addstr(5, 3, f"  {self.current_pulse} µs")

                popup_win.addstr(7, 3, "Servo Range:")
                popup_win.addstr(
                    8,
                    3,
                    f"  Min: {self.calibrator.servo.min_pulse} µs | Max: {self.calibrator.servo.max_pulse} µs",
                )

                popup_win.addstr(10, 3, "Rest Angle:")
                popup_win.addstr(11, 3, f"  {self.calibrator.servo.rest_angle}°")

                # Instructions
                popup_win.addstr(13, 3, f"↑/↓ adjust ±{self.STEP_SIZE} µs", curses.A_DIM)
                popup_win.addstr(14, 3, "ESC to exit", curses.A_DIM)

                popup_win.refresh()

                # Move servo to current pulse
                self.calibrator.set_servo_pulse(self.current_pulse)

                key = popup_win.getch()

                if key == curses.KEY_UP:
                    self.current_pulse = self.calibrator.clamp_pulse(self.current_pulse + self.STEP_SIZE)
                elif key == curses.KEY_DOWN:
                    self.current_pulse = self.calibrator.clamp_pulse(self.current_pulse - self.STEP_SIZE)
                elif key == 27:  # ESC
                    return True

        finally:
            curses.endwin()


def main(servo_id: str) -> None:
    """Main entry point for servo manual control.

    Args:
        servo_id: The servo ID to control (e.g., 'front_foot_left')
    """
    try:
        # Validate servo ID
        try:
            servo_enum = ServoName(servo_id)
        except ValueError:
            print(f"Error: Invalid servo ID '{servo_id}'")
            print(f"Valid servo IDs: {', '.join([s.value for s in ServoName])}")
            sys.exit(1)

        # Initialize calibrator
        calibrator = ServoCalibrator(servo_enum)

        # Run manual control
        def control_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))

            control = ServoManualControl(stdscr, calibrator)
            return control.run()

        result = curses.wrapper(control_wrapper)

        if result:
            print(f"\n✓ Manual control completed for {servo_id}")
        else:
            print(f"\n✗ Manual control cancelled for {servo_id}")

    except KeyboardInterrupt:
        print("\n✗ Manual control interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during manual control: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: servo_manual_control.py <SERVO_ID>")
        sys.exit(1)

    servo_id_arg = sys.argv[1]
    main(servo_id_arg)
