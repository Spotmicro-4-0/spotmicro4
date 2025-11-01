#!/usr/bin/env python3
"""
Diagnostics wizard for SpotMicroAI servo symmetry testing.

Interactive guided diagnostics to test all servos by sweeping them through
their range of motion to verify symmetry and proper operation.

Organized by joint type (shoulders, legs, feet), each servo group is tested
with slow sweeps from rest to min, min to max, and max to rest.

Usage: diagnostics.py
"""

import curses
import sys
import time
from typing import Dict, List, Tuple

from spotmicroai.configuration._config_provider import ConfigProvider, ServoName
from spotmicroai.constants import (
    POPUP_HEIGHT,
    POPUP_WIDTH,
    SWEEP_RATE_DEG_PER_FRAME,
    FRAME_DURATION,
)
from spotmicroai.hardware.servo import JointType
from spotmicroai.hardware.servo._servo import Servo
from spotmicroai.hardware.servo._servo_factory import ServoFactory
from spotmicroai.spot_config.ui import theme as THEME, ui_utils
import spotmicroai.labels as LABELS


class DiagnosticsWizard:
    """Interactive wizard for servo diagnostics and symmetry testing."""

    def __init__(self, stdscr):
        """Initialize diagnostics wizard.

        Args:
            stdscr: The curses window object
        """
        self.stdscr = stdscr
        self.config_provider = ConfigProvider()
        self.servos: Dict[ServoName, Servo] = {}
        self.servo_groups: Dict[JointType, List[ServoName]] = {}
        self.popup_start_y = 0
        self.popup_start_x = 0

    def _load_all_servos(self) -> None:
        """Load all 12 servos and group by joint type."""
        for servo_name in ServoName:
            try:
                servo = ServoFactory.create(servo_name)
                self.servos[servo_name] = servo

                joint_type = JointType.from_servo_name(servo_name)
                if joint_type not in self.servo_groups:
                    self.servo_groups[joint_type] = []
                self.servo_groups[joint_type].append(servo_name)
            except Exception as e:
                print(LABELS.DIAG_SERVO_ERROR.format(servo_name.value, e))
                raise

    def get_popup_position(self) -> Tuple[int, int]:
        """Calculate centered popup position."""
        h, w = self.stdscr.getmaxyx()
        start_y = max(1, (h - POPUP_HEIGHT) // 2)
        start_x = max(1, (w - POPUP_WIDTH) // 2)
        return start_y, start_x

    def create_popup_window(self) -> curses.window:
        """Create and configure a popup window."""
        self.popup_start_y, self.popup_start_x = self.get_popup_position()

        h, w = self.stdscr.getmaxyx()
        ui_utils.CursesUIHelper.draw_shadow(
            self.stdscr, self.popup_start_y, self.popup_start_x, POPUP_WIDTH, POPUP_HEIGHT, h, w
        )

        popup_win = curses.newwin(POPUP_HEIGHT, POPUP_WIDTH, self.popup_start_y, self.popup_start_x)
        popup_win.keypad(True)
        popup_win.bkgd(" ", curses.color_pair(THEME.REGULAR_ROW))
        return popup_win

    def refresh_popup_shadow(self) -> None:
        """Redraw the shadow after refreshing the popup window."""
        h, w = self.stdscr.getmaxyx()
        ui_utils.CursesUIHelper.draw_shadow(
            self.stdscr, self.popup_start_y, self.popup_start_x, POPUP_WIDTH, POPUP_HEIGHT, h, w
        )
        self.stdscr.refresh()

    def show_introduction(self) -> bool:
        """Show introduction screen with diagnostics instructions."""
        popup_win = self.create_popup_window()

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                # Title
                title = LABELS.DIAG_TITLE
                title_x = max(1, (POPUP_WIDTH - len(title)) // 2)
                self._safe_addstr(popup_win, 1, title_x, title, curses.A_BOLD)

                try:
                    popup_win.hline(2, 1, curses.ACS_HLINE, POPUP_WIDTH - 2)
                except curses.error:
                    pass

                # Instructions
                instructions = [
                    LABELS.DIAG_INSTRUCTION,
                    "",
                    LABELS.DIAG_INTRO_LINE_1,
                    LABELS.DIAG_INTRO_LINE_2,
                    LABELS.DIAG_INTRO_LINE_3,
                    "",
                    LABELS.DIAG_INTRO_LINE_5,
                    LABELS.DIAG_INTRO_LINE_6,
                    LABELS.DIAG_INTRO_LINE_7,
                    LABELS.DIAG_INTRO_LINE_8,
                ]

                for i, line in enumerate(instructions):
                    self._safe_addstr(popup_win, 4 + i, 2, line)

                self._safe_addstr(popup_win, 13, 2, LABELS.DIAG_ENTER_BEGIN, curses.A_DIM)
                self._safe_addstr(popup_win, 14, 2, LABELS.DIAG_PRESS_ESC_CANCEL, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                key = popup_win.getch()
                if key in (curses.KEY_ENTER, 10, 13):
                    return True
                elif key == 27:  # ESC
                    return False

        finally:
            curses.endwin()

    def _safe_addstr(self, win: curses.window, y: int, x: int, text: str, attr=0) -> None:
        """Safely add a string to the window, truncating if necessary."""
        try:
            h, w = win.getmaxyx()
            if y < 0 or y >= h or x < 0 or x >= w:
                return
            # Truncate text to fit within window width
            max_len = w - x - 1
            if max_len > 0:
                win.addstr(y, x, text[:max_len], attr)
        except curses.error:
            pass

    def sweep_servos(self, servo_names: List[ServoName], start_angle: float, end_angle: float) -> bool:
        """Sweep a group of servos from start_angle to end_angle.

        Args:
            servo_names: List of ServoName enums to sweep
            start_angle: Starting angle in degrees
            end_angle: Ending angle in degrees

        Returns:
            True if completed successfully, False if cancelled
        """
        popup_win = self.create_popup_window()

        try:
            # Clamp angles to valid ranges
            valid_start = start_angle
            valid_end = end_angle

            angle_diff = abs(valid_end - valid_start)
            if angle_diff == 0:
                return True

            direction = 1 if valid_end > valid_start else -1
            current_angle = valid_start
            start_time = time.time()
            progress_pct = 0.0

            while True:
                popup_win.erase()
                popup_win.box()

                # Title
                title = LABELS.DIAG_TITLE
                title_x = max(1, (POPUP_WIDTH - len(title)) // 2)
                self._safe_addstr(popup_win, 1, title_x, title, curses.A_BOLD)

                try:
                    popup_win.hline(2, 1, curses.ACS_HLINE, POPUP_WIDTH - 2)
                except curses.error:
                    pass

                # Show which servos are being tested
                servo_names_str = ", ".join(
                    [s.value.replace(LABELS.UNDERSCORE_CHAR, LABELS.SPACE_CHAR).title() for s in servo_names]
                )
                label_text = LABELS.DIAG_JOINT_TYPE_LABEL.format(servo_names_str[:50])
                self._safe_addstr(popup_win, 4, 2, label_text)

                progress_text = LABELS.DIAG_SWEEP_PROGRESS.format(valid_start, valid_end, progress_pct)
                self._safe_addstr(popup_win, 6, 2, progress_text)

                # Show current angles
                self._safe_addstr(popup_win, 8, 2, LABELS.DIAG_CURRENT_ANGLES)
                row = 9
                for servo_name in servo_names:
                    if row < 13:  # Limit to 4 servos displayed
                        servo = self.servos[servo_name]
                        display_name = servo_name.value.replace(LABELS.UNDERSCORE_CHAR, LABELS.SPACE_CHAR).title()
                        angle_text = LABELS.DIAG_SERVO_ANGLE_DISPLAY.format(display_name, current_angle)
                        self._safe_addstr(popup_win, row, 3, angle_text)
                        row += 1

                self._safe_addstr(popup_win, 13, 2, LABELS.DIAG_PRESS_ENTER_NEXT, curses.A_DIM)
                self._safe_addstr(popup_win, 14, 2, LABELS.DIAG_PRESS_ESC_CANCEL, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                # Check for user input (non-blocking)
                popup_win.nodelay(True)
                key = popup_win.getch()
                popup_win.nodelay(False)

                if key == 27:  # ESC - cancel
                    return False

                # Calculate next angle based on sweep rate and time
                elapsed = time.time() - start_time
                total_steps = int(angle_diff / SWEEP_RATE_DEG_PER_FRAME) + 1
                step = min(int(elapsed / FRAME_DURATION), total_steps)
                current_angle = int(valid_start + direction * step * SWEEP_RATE_DEG_PER_FRAME)

                # Clamp to end angle
                if direction > 0:
                    current_angle = min(current_angle, valid_end)
                else:
                    current_angle = max(current_angle, valid_end)

                # Command all servos to this angle
                for servo_name in servo_names:
                    servo = self.servos[servo_name]
                    servo.angle = int(current_angle)

                # Check if we've reached the end
                reached_end = (direction > 0 and current_angle >= valid_end) or (
                    direction < 0 and current_angle <= valid_end
                )

                # Update progress percentage based on actual angle position (ensure it reaches 100% at end)
                if reached_end:
                    progress_pct = 100.0
                else:
                    if direction > 0:
                        progress_pct = ((current_angle - valid_start) / angle_diff) * 100 if angle_diff > 0 else 100
                    else:
                        progress_pct = ((valid_start - current_angle) / angle_diff) * 100 if angle_diff > 0 else 100

                if reached_end:
                    # Wait for user to press enter
                    while True:
                        key = popup_win.getch()
                        if key in (curses.KEY_ENTER, 10, 13):
                            return True
                        elif key == 27:
                            return False

                time.sleep(FRAME_DURATION)

        finally:
            curses.endwin()

    def test_joint_type(self, joint_type: JointType) -> bool:
        """Test all servos of a given joint type.

        Sequence:
        1. Move to rest position
        2. Sweep from rest to min
        3. Sweep from min to max
        4. Sweep from max to rest

        Args:
            joint_type: The JointType to test

        Returns:
            True if completed, False if cancelled
        """
        if joint_type not in self.servo_groups:
            return True

        servo_names = self.servo_groups[joint_type]
        if not servo_names:
            return True

        # Get angle limits for this joint type
        first_servo = self.servos[servo_names[0]]
        rest_angle = first_servo.rest_angle
        min_angle = first_servo.min_angle
        max_angle = first_servo.max_angle

        # Step 1: Move to rest position
        for servo_name in servo_names:
            self.servos[servo_name].angle = rest_angle

        # Step 2: Rest to Min
        if not self.sweep_servos(servo_names, rest_angle, min_angle):
            return False

        # Step 3: Min to Max
        if not self.sweep_servos(servo_names, min_angle, max_angle):
            return False

        # Step 4: Max to Rest
        if not self.sweep_servos(servo_names, max_angle, rest_angle):
            return False

        return True

    def show_completion(self) -> None:
        """Show completion screen."""
        popup_win = self.create_popup_window()

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                title = LABELS.DIAG_TEST_COMPLETE
                title_x = max(1, (POPUP_WIDTH - len(title)) // 2)
                self._safe_addstr(popup_win, 1, title_x, title, curses.A_BOLD)

                try:
                    popup_win.hline(2, 1, curses.ACS_HLINE, POPUP_WIDTH - 2)
                except curses.error:
                    pass

                self._safe_addstr(popup_win, 5, 2, LABELS.DIAG_SUMMARY)
                self._safe_addstr(popup_win, 7, 2, LABELS.DIAG_SUCCESS_ALL_SERVOS)
                self._safe_addstr(popup_win, 8, 2, LABELS.DIAG_SUCCESS_NO_ERRORS)

                self._safe_addstr(popup_win, 13, 2, LABELS.DIAG_PRESS_ENTER_FINISH, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                key = popup_win.getch()
                if key in (curses.KEY_ENTER, 10, 13):
                    return

        finally:
            curses.endwin()

    def run(self) -> bool:
        """Run the complete diagnostics wizard.

        Returns:
            True if completed successfully, False if cancelled
        """
        try:
            self._load_all_servos()

            if not self.show_introduction():
                return False

            # Test each joint type in order
            joint_type_order = [JointType.SHOULDER, JointType.LEG, JointType.FOOT]
            for joint_type in joint_type_order:
                if not self.test_joint_type(joint_type):
                    return False

            self.show_completion()
            return True

        except Exception as e:
            print(LABELS.DIAG_ERROR_GENERAL.format(e))
            return False


def main() -> None:
    """Main entry point for diagnostics."""
    try:

        def diagnostics_wrapper(stdscr):
            curses.curs_set(0)
            curses.start_color()
            curses.use_default_colors()
            ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
            stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
            stdscr.refresh()

            wizard = DiagnosticsWizard(stdscr)
            return wizard.run()

        result = curses.wrapper(diagnostics_wrapper)

        if result:
            print("\n✓ Diagnostics completed successfully")
        else:
            print(LABELS.DIAG_INTERRUPTED)

    except KeyboardInterrupt:
        print(LABELS.DIAG_INTERRUPTED)
        sys.exit(1)
    except Exception as e:
        print(LABELS.DIAG_ERROR_GENERAL.format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
