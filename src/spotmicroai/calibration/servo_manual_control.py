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
import spotmicroai.setup_app.labels as LABELS
from spotmicroai.calibration.servo_controller import ServoController


class ServoManualControl:
    """Interactive manual servo control interface."""

    POPUP_HEIGHT = 16
    POPUP_WIDTH = 75
    ANGLE_STEP_SIZE = 1  # degrees per adjustment

    def __init__(self, stdscr, servo_controller: ServoController):
        """Initialize manual control interface.

        Args:
            stdscr: curses window object
            servo_controller: ServoController instance for servo control
        """
        self.stdscr = stdscr
        self.servo_controller = servo_controller
        # Start at the midpoint between min and max pulse
        self.current_pulse = (servo_controller.servo.min_pulse + servo_controller.servo.max_pulse) // 2
        # Determine if servo is inverted
        servo_name = servo_controller.servo_name.value.lower()
        self.is_inverted = "shoulder" in servo_name

    def _format_servo_name(self) -> str:
        """Format servo name using shared UI utility."""
        return ui_utils.CursesUIHelper.format_servo_name(self.servo_controller.servo_name.value)

    def get_popup_position(self):
        """Calculate centered popup position."""
        h, w = self.stdscr.getmaxyx()
        start_y = max(1, (h - self.POPUP_HEIGHT) // 2)
        start_x = max(1, (w - self.POPUP_WIDTH) // 2)
        return start_y, start_x

    def get_servo_target_min_angle(self) -> float:
        """Get the target minimum angle for the current servo type."""
        if "shoulder" in self.servo_controller.servo_name.value.lower():
            return 60.0
        elif "leg" in self.servo_controller.servo_name.value.lower():
            return -20.0
        else:
            return 0.0

    def calculate_angle_from_pulse(self, pulse: int | float) -> float:
        """Calculate servo angle based on current pulse width and calibration.

        Args:
            pulse: Pulse width in microseconds

        Returns:
            Calculated angle in degrees based on current calibration
        """
        servo = self.servo_controller.servo
        pulse_range = servo.max_pulse - servo.min_pulse

        if pulse_range == 0:
            return servo.rest_angle

        target_min_angle = self.get_servo_target_min_angle()

        # Calculate angle proportionally across the range
        pulse_offset = pulse - servo.min_pulse

        if self.is_inverted:
            # For inverted servos (shoulder), the relationship is backwards
            # So we invert the pulse offset calculation
            angle_offset = ((servo.max_pulse - pulse) / pulse_range) * servo.range
        else:
            # For normal servos (leg), higher pulse = higher angle
            angle_offset = (pulse_offset / pulse_range) * servo.range

        # Add the minimum angle offset to get the actual angle
        angle = target_min_angle + angle_offset

        return angle

    def adjust_pulse_for_angle_change(self, angle_delta: float) -> None:
        """Adjust pulse width to achieve desired angle change.

        Args:
            angle_delta: Change in angle (positive = increase angle, negative = decrease angle)
        """
        servo = self.servo_controller.servo
        pulse_range = servo.max_pulse - servo.min_pulse

        if pulse_range == 0:
            return

        # Calculate pulse change needed for the angle change
        pulse_delta = (angle_delta / servo.range) * pulse_range

        if self.is_inverted:
            # For inverted servos, angle increase requires pulse decrease
            pulse_delta = -pulse_delta

        self.current_pulse = self.servo_controller.clamp_pulse(self.current_pulse + pulse_delta)

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
                title = LABELS.MANUAL_TITLE.format(self._format_servo_name())
                title_x = (self.POPUP_WIDTH - len(title)) // 2
                popup_win.addstr(1, title_x, title, curses.A_BOLD)

                # Separator
                popup_win.hline(2, 1, curses.ACS_HLINE, self.POPUP_WIDTH - 2)

                # Current status
                popup_win.addstr(4, 3, LABELS.MANUAL_CURRENT_PULSE_WIDTH, curses.A_BOLD)
                calculated_angle = self.calculate_angle_from_pulse(self.current_pulse)
                popup_win.addstr(5, 3, f"  {int(self.current_pulse)} µs ({int(calculated_angle)}°)")

                popup_win.addstr(7, 3, LABELS.MANUAL_SERVO_RANGE)
                popup_win.addstr(
                    8,
                    3,
                    f"  Min: {self.servo_controller.servo.min_pulse} µs | Max: {self.servo_controller.servo.max_pulse} µs",
                )

                popup_win.addstr(10, 3, LABELS.MANUAL_REST_ANGLE)
                # For shoulders, rest is always 90° (Point 1). For other servos, calculate from local angle
                if "shoulder" in self.servo_controller.servo_name.value.lower():
                    rest_angle_display = 90
                else:
                    rest_physical = self.servo_controller.servo.min_pulse + (
                        self.servo_controller.servo.rest_angle / self.servo_controller.servo.range
                    ) * (self.servo_controller.servo.max_pulse - self.servo_controller.servo.min_pulse)
                    rest_angle_display = self.calculate_angle_from_pulse(int(rest_physical))
                popup_win.addstr(11, 3, f"  {int(rest_angle_display)}°")

                # Instructions
                popup_win.addstr(13, 3, LABELS.MANUAL_ADJUST_INSTRUCTION.format(self.ANGLE_STEP_SIZE), curses.A_DIM)
                popup_win.addstr(14, 3, LABELS.MANUAL_EXIT_INSTRUCTION, curses.A_DIM)

                popup_win.refresh()

                # Move servo to current pulse
                self.servo_controller.set_servo_pulse(self.current_pulse)

                key = popup_win.getch()

                if key == curses.KEY_UP:
                    self.adjust_pulse_for_angle_change(self.ANGLE_STEP_SIZE)
                elif key == curses.KEY_DOWN:
                    self.adjust_pulse_for_angle_change(-self.ANGLE_STEP_SIZE)
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
            print(LABELS.MANUAL_INVALID_SERVO_ID.format(servo_id))
            print(LABELS.MANUAL_VALID_SERVO_IDS.format(', '.join([s.value for s in ServoName])))
            sys.exit(1)

        # Initialize servo_controller
        servo_controller = ServoController(servo_enum)

        # Run manual control
        def control_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            # stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))

            control = ServoManualControl(stdscr, servo_controller)
            return control.run()

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

    servo_id_arg = sys.argv[1]
    main(servo_id_arg)
