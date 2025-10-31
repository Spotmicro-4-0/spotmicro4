#!/usr/bin/env python3
from __future__ import annotations

import curses
import sys

from spotmicroai.configuration._config_provider import ServoName
from spotmicroai.constants import POPUP_HEIGHT, POPUP_WIDTH
from spotmicroai.runtime.motion_controller.models.coordinate import Coordinate
from spotmicroai.servo import ServoFactory
from spotmicroai.ui import theme as THEME, ui_utils

# Mapping from corner names to servo tuples (shoulder, leg, foot)
CORNER_TO_SERVOS = {
    'front_left': (ServoName.FRONT_SHOULDER_LEFT, ServoName.FRONT_LEG_LEFT, ServoName.FRONT_FOOT_LEFT),
    'front_right': (ServoName.FRONT_SHOULDER_RIGHT, ServoName.FRONT_LEG_RIGHT, ServoName.FRONT_FOOT_RIGHT),
    'rear_left': (ServoName.REAR_SHOULDER_LEFT, ServoName.REAR_LEG_LEFT, ServoName.REAR_FOOT_LEFT),
    'rear_right': (ServoName.REAR_SHOULDER_RIGHT, ServoName.REAR_LEG_RIGHT, ServoName.REAR_FOOT_RIGHT),
}

# Parameter names for display
PARAM_NAMES = ['X', 'Y', 'Z']


class InverseKinematicsControl:
    """Interactive inverse kinematics control interface."""

    STEP_SIZE_MM = 5.0

    def __init__(self, stdscr, corner: str):
        self.stdscr = stdscr
        self.corner = corner
        self.formatted_corner_name = corner.replace('_', ' ').title()

        # Get servo instances for this corner
        shoulder_name, leg_name, foot_name = CORNER_TO_SERVOS[corner]
        self.shoulder_servo = ServoFactory.create(shoulder_name)
        self.leg_servo = ServoFactory.create(leg_name)
        self.foot_servo = ServoFactory.create(foot_name)

        # Initialize coordinate values (x, y, z)
        self.coordinate = Coordinate(x=0.0, y=150.0, z=0.0)

        # Track which parameter is selected (0=X, 1=Y, 2=Z)
        self.selected_param = 1  # Start with Y
        self.step_size = self.STEP_SIZE_MM
        self._last_applied_angles: tuple[int, int, int] | None = None

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

    def compute_angles(self):
        """Compute inverse kinematics for current coordinate."""
        phi, theta, omega = self.coordinate.inverse_kinematics()
        return phi, theta, omega

    def apply_angles(self, phi: int, theta: int, omega: int) -> None:
        """Apply computed angles to the servos in degrees."""
        # Note: These are example assignments; adjust based on your servo calibration
        self.shoulder_servo.angle = omega
        self.leg_servo.angle = theta
        self.foot_servo.angle = phi

    def _apply_if_changed(self, phi: float, theta: float, omega: float) -> None:
        """Apply new angles only when they change."""
        # Convert to ints for servo interface
        target = (int(round(phi)), int(round(theta)), int(round(omega)))
        if target != self._last_applied_angles:
            self.apply_angles(*target)
            self._last_applied_angles = target

    def run(self) -> bool:
        """Run inverse kinematics control UI loop."""
        popup = self.create_popup_window()
        try:
            while True:
                popup.erase()
                popup.box()

                # Title
                title = f"IK Control - {self.formatted_corner_name}"
                popup.addstr(1, (POPUP_WIDTH - len(title)) // 2, title, curses.A_BOLD)
                popup.hline(2, 1, curses.ACS_HLINE, POPUP_WIDTH - 2)

                # Current coordinate values
                popup.addstr(4, 3, "Coordinate Values (mm):", curses.A_BOLD)

                x_marker = " → " if self.selected_param == 0 else "   "
                y_marker = " → " if self.selected_param == 1 else "   "
                z_marker = " → " if self.selected_param == 2 else "   "

                popup.addstr(5, 3, f"{x_marker}X: {self.coordinate.x:7.1f}")
                popup.addstr(6, 3, f"{y_marker}Y: {self.coordinate.y:7.1f}")
                popup.addstr(7, 3, f"{z_marker}Z: {self.coordinate.z:7.1f}")

                # Compute and display angles
                phi, theta, omega = self.compute_angles()
                self._apply_if_changed(phi, theta, omega)

                popup.addstr(9, 3, "Computed Angles (degrees):", curses.A_BOLD)
                popup.addstr(10, 3, f"  Shoulder (Ω): {omega:7.1f}°")
                popup.addstr(11, 3, f"  Leg (Θ):      {theta:7.1f}°")
                popup.addstr(12, 3, f"  Foot (Φ):     {phi:7.1f}°")

                # Instructions
                popup.addstr(
                    14,
                    3,
                    f"↑/↓ select param | ←/→ adjust ±{self.step_size:.1f} mm",
                    curses.A_DIM,
                )
                popup.addstr(15, 3, "ESC to exit", curses.A_DIM)
                popup.refresh()

                # Key input
                key = popup.getch()
                if key == curses.KEY_UP:
                    self.selected_param = (self.selected_param - 1) % 3
                elif key == curses.KEY_DOWN:
                    self.selected_param = (self.selected_param + 1) % 3
                elif key == curses.KEY_LEFT:
                    self._adjust_selected_param(-self.step_size)
                elif key == curses.KEY_RIGHT:
                    self._adjust_selected_param(self.step_size)
                elif key == 27:  # ESC
                    return True

        finally:
            curses.endwin()

    def _adjust_selected_param(self, delta: float) -> None:
        """Adjust the selected parameter by the given delta."""
        if self.selected_param == 0:
            self.coordinate.x += delta
        elif self.selected_param == 1:
            self.coordinate.y += delta
        elif self.selected_param == 2:
            self.coordinate.z += delta


def main(corner: str) -> None:
    """CLI entry point for inverse kinematics control."""
    try:
        # Validate corner
        if corner not in CORNER_TO_SERVOS:
            print(f"Error: Invalid corner '{corner}'")
            print(f"Valid corners: {', '.join(CORNER_TO_SERVOS.keys())}")
            sys.exit(1)

        def control_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            # Make the entire background blue
            stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
            stdscr.clear()
            stdscr.refresh()
            return InverseKinematicsControl(stdscr, corner).run()

        result = curses.wrapper(control_wrapper)

        if result:
            print(f"\n✓ Inverse kinematics control completed for {corner}")
        else:
            print(f"\n✗ Inverse kinematics control cancelled for {corner}")

    except KeyboardInterrupt:
        print("\n✗ Inverse kinematics control interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during inverse kinematics control: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: inverse_kinematics_control.py <CORNER>")
        print("Valid corners: front_left, front_right, rear_left, rear_right")
        sys.exit(1)

    main(sys.argv[1])
