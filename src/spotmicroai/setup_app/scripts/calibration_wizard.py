#!/usr/bin/env python3
"""
Calibration wizard for SpotMicroAI servo joints.

Interactive guided calibration for different joint types (foot, leg, shoulder).
Walks the user through physical calibration points and calculates servo parameters.

Usage: calibration_wizard.py <SERVO_ID>
       calibration_wizard.py all (to calibrate all servos sequentially)
"""

import curses
import sys
from dataclasses import dataclass
from enum import Enum
from typing import cast, Tuple

from spotmicroai.configuration import ServoName
from spotmicroai.constants import CALIBRATION_SPECS
from spotmicroai.setup_app import theme as THEME, ui_utils
import spotmicroai.setup_app.labels as LABELS
from spotmicroai.setup_app.scripts.servo_calibrator import ServoCalibrator


class JointType(Enum):
    """Different types of joints in the robot."""

    FOOT = "foot"
    LEG = "leg"
    SHOULDER = "shoulder"


@dataclass
class CalibrationPoint:
    """Represents a calibration point with angle and pulse width."""

    description: str
    physical_angle: float  # The actual angle in degrees IRL
    pulse_width: int | None = None  # Captured pulse width in microseconds


@dataclass
class JointCalibrationSpec:
    """Specification for calibrating a specific joint type."""

    joint_type: JointType
    points: list[CalibrationPoint]
    target_min_angle: float
    target_max_angle: float
    rest_angle: float


def get_joint_type_from_servo_name(servo_name: ServoName) -> JointType:
    """Determine joint type from servo name."""
    name_str = servo_name.value.lower()
    if "foot" in name_str:
        return JointType.FOOT
    elif "leg" in name_str:
        return JointType.LEG
    elif "shoulder" in name_str:
        return JointType.SHOULDER
    raise ValueError(LABELS.WIZARD_JOINT_TYPE_ERROR.format(servo_name))


def get_calibration_spec(joint_type: JointType) -> JointCalibrationSpec:
    """Get calibration specification for a joint type from constants."""
    spec_data = CALIBRATION_SPECS[joint_type.value]

    points = [
        CalibrationPoint(
            description=point["description"],
            physical_angle=point["physical_angle"],
        )
        for point in spec_data["points"]
    ]

    return JointCalibrationSpec(
        joint_type=joint_type,
        points=points,
        target_min_angle=spec_data["target_min_angle"],
        target_max_angle=spec_data["target_max_angle"],
        rest_angle=spec_data["rest_angle"],
    )


class CalibrationWizard:
    """Interactive wizard for step-by-step servo calibration."""

    POPUP_HEIGHT = 16
    POPUP_WIDTH = 75
    STEP_SIZE = 10  # microseconds or degrees

    def __init__(self, stdscr, calibrator: ServoCalibrator, spec: JointCalibrationSpec):
        """Initialize wizard with calibrator and spec."""
        self.stdscr = stdscr
        self.calibrator = calibrator
        self.spec = spec
        self.current_pulse = calibrator.servo.min_pulse
        self.captured_points: list[CalibrationPoint] = []
        self.popup_start_y = 0
        self.popup_start_x = 0

    def get_popup_position(self) -> Tuple[int, int]:
        """Calculate centered popup position."""
        h, w = self.stdscr.getmaxyx()
        start_y = max(1, (h - self.POPUP_HEIGHT) // 2)
        start_x = max(1, (w - self.POPUP_WIDTH) // 2)
        return start_y, start_x

    def _format_servo_name(self) -> str:
        """Format servo name using shared UI utility."""
        return ui_utils.CursesUIHelper.format_servo_name(self.calibrator.servo_name.value)

    def create_popup_window(self) -> curses.window:
        """Create and configure a popup window."""
        self.popup_start_y, self.popup_start_x = self.get_popup_position()

        # Draw shadow effect
        h, w = self.stdscr.getmaxyx()
        ui_utils.CursesUIHelper.draw_shadow(
            self.stdscr, self.popup_start_y, self.popup_start_x, self.POPUP_WIDTH, self.POPUP_HEIGHT, h, w
        )

        popup_win = curses.newwin(self.POPUP_HEIGHT, self.POPUP_WIDTH, self.popup_start_y, self.popup_start_x)
        popup_win.keypad(True)
        popup_win.bkgd(" ", curses.color_pair(THEME.REGULAR_ROW))
        return popup_win

    def refresh_popup_shadow(self) -> None:
        """Redraw the shadow after refreshing the popup window."""
        h, w = self.stdscr.getmaxyx()
        ui_utils.CursesUIHelper.draw_shadow(
            self.stdscr, self.popup_start_y, self.popup_start_x, self.POPUP_WIDTH, self.POPUP_HEIGHT, h, w
        )
        self.stdscr.refresh()

    def show_introduction(self) -> bool:
        """Show introduction screen with calibration instructions."""
        popup_win = self.create_popup_window()

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                # Title
                title = LABELS.WIZARD_TITLE.format(self._format_servo_name())
                title_x = (self.POPUP_WIDTH - len(title)) // 2
                popup_win.addstr(1, title_x, title, curses.A_BOLD)

                # Separator
                popup_win.hline(2, 1, curses.ACS_HLINE, self.POPUP_WIDTH - 2)

                # Instructions
                instructions = [
                    LABELS.WIZARD_JOINT_TYPE_LINE.format(self.spec.joint_type.value.upper()),
                    "",
                    LABELS.WIZARD_INSTRUCTION_1,
                    LABELS.WIZARD_INSTRUCTION_2,
                    LABELS.WIZARD_INSTRUCTION_3,
                    "",
                    LABELS.WIZARD_INSTRUCTION_4,
                    LABELS.WIZARD_INSTRUCTION_5,
                    "",
                ]

                for i, line in enumerate(instructions):
                    popup_win.addstr(4 + i, 3, line)

                popup_win.addstr(13, 3, LABELS.WIZARD_PRESS_ENTER_BEGIN, curses.A_DIM)
                popup_win.addstr(14, 3, LABELS.WIZARD_PRESS_ESC_CANCEL, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                key = popup_win.getch()
                if key in (curses.KEY_ENTER, 10, 13):
                    return True
                elif key == 27:  # ESC
                    return False

        finally:
            curses.endwin()

    def capture_calibration_point(self, point_index: int, point: CalibrationPoint) -> bool:
        """Guide user to capture a single calibration point."""
        popup_win = self.create_popup_window()
        # Start at the midpoint between min and max pulse
        current_pulse = (self.calibrator.servo.min_pulse + self.calibrator.servo.max_pulse) // 2

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                # Title
                title = LABELS.WIZARD_POINT_TITLE.format(point_index + 1, len(self.spec.points))
                title_x = (self.POPUP_WIDTH - len(title)) // 2
                popup_win.addstr(1, title_x, title, curses.A_BOLD)

                popup_win.hline(2, 1, curses.ACS_HLINE, self.POPUP_WIDTH - 2)

                # Description
                popup_win.addstr(4, 3, point.description)
                popup_win.addstr(5, 3, LABELS.WIZARD_EXPECTED_ANGLE.format(point.physical_angle))

                # Current values
                popup_win.addstr(7, 3, LABELS.WIZARD_CURRENT_PULSE.format(current_pulse))

                # Display Min Pulse: show only if point 1 has been captured
                if len(self.captured_points) > 0:
                    min_pulse_str = f"{self.captured_points[0].pulse_width} µs"
                else:
                    min_pulse_str = LABELS.WIZARD_DASH
                popup_win.addstr(8, 3, LABELS.WIZARD_MIN_PULSE_LABEL.format(min_pulse_str))

                # Display Max Pulse: show only if point 2 has been captured
                if len(self.captured_points) > 1:
                    max_pulse_str = f"{self.captured_points[1].pulse_width} µs"
                else:
                    max_pulse_str = LABELS.WIZARD_DASH
                popup_win.addstr(9, 3, LABELS.WIZARD_MAX_PULSE_LABEL.format(max_pulse_str))

                # Instructions
                popup_win.addstr(
                    11,
                    3,
                    LABELS.WIZARD_ADJUST_INSTRUCTION.format(self.STEP_SIZE),
                    curses.A_DIM,
                )
                popup_win.addstr(12, 3, LABELS.WIZARD_ENTER_CONFIRM_ESC_CANCEL, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                # Move servo to current pulse
                self.calibrator.set_servo_pulse(current_pulse)

                key = popup_win.getch()

                if key == curses.KEY_UP:
                    current_pulse = self.calibrator.clamp_pulse(current_pulse + self.STEP_SIZE)
                elif key == curses.KEY_DOWN:
                    current_pulse = self.calibrator.clamp_pulse(current_pulse - self.STEP_SIZE)
                elif key in (curses.KEY_ENTER, 10, 13):
                    # Capture this point
                    point.pulse_width = current_pulse
                    self.captured_points.append(point)
                    return True
                elif key == 27:  # ESC
                    return False

        finally:
            curses.endwin()

    def show_confirmation(self) -> bool:
        """Show confirmation screen with calculated values."""
        if len(self.captured_points) != len(self.spec.points):
            return False

        popup_win = self.create_popup_window()

        try:
            while True:
                popup_win.erase()
                popup_win.box()

                title = LABELS.WIZARD_SUMMARY_TITLE
                title_x = (self.POPUP_WIDTH - len(title)) // 2
                popup_win.addstr(1, title_x, title, curses.A_BOLD)

                popup_win.hline(2, 1, curses.ACS_HLINE, self.POPUP_WIDTH - 2)

                # Show captured values
                row = 4
                for i, point in enumerate(self.captured_points):
                    popup_win.addstr(
                        row,
                        3,
                        LABELS.WIZARD_POINT_SUMMARY.format(i + 1, point.pulse_width, point.physical_angle),
                    )
                    row += 1

                popup_win.addstr(row, 3, "")
                row += 1
                popup_win.addstr(
                    row,
                    3,
                    LABELS.WIZARD_TARGET_RANGE.format(self.spec.target_min_angle, self.spec.target_max_angle),
                )
                row += 1
                popup_win.addstr(row, 3, LABELS.WIZARD_REST_ANGLE.format(self.spec.rest_angle))

                popup_win.addstr(13, 3, LABELS.WIZARD_ENTER_SAVE_ESC_CANCEL, curses.A_DIM)

                popup_win.refresh()
                self.refresh_popup_shadow()

                key = popup_win.getch()
                if key in (curses.KEY_ENTER, 10, 13):
                    return True
                elif key == 27:  # ESC
                    return False

        finally:
            curses.endwin()

    def calculate_and_save_parameters(self) -> None:
        """Calculate servo parameters from captured points and save.

        For shoulder and leg servos, this uses the captured points to infer
        min and max pulses based on the target range through linear extrapolation.
        """
        if len(self.captured_points) < 2:
            raise ValueError(LABELS.WIZARD_NEED_TWO_POINTS)

        point1 = self.captured_points[0]
        point2 = self.captured_points[1]

        # Validate that pulse widths were captured
        assert point1.pulse_width is not None, LABELS.WIZARD_PULSE_NOT_CAPTURED_1
        assert point2.pulse_width is not None, LABELS.WIZARD_PULSE_NOT_CAPTURED_2

        # For shoulder and leg servos, use captured points to infer full range
        if self.spec.joint_type in (JointType.SHOULDER, JointType.LEG):
            # Map the captured angles to their pulse widths
            angle1 = point1.physical_angle
            angle2 = point2.physical_angle
            pulse1 = cast(int, point1.pulse_width)
            pulse2 = cast(int, point2.pulse_width)

            # Calculate pulse per degree
            angle_diff = angle2 - angle1
            pulse_diff = pulse2 - pulse1
            pulse_per_degree = pulse_diff / angle_diff if angle_diff != 0 else 0

            # Infer min and max pulses using linear extrapolation
            min_pulse = int(pulse1 + (self.spec.target_min_angle - angle1) * pulse_per_degree)
            max_pulse = int(pulse1 + (self.spec.target_max_angle - angle1) * pulse_per_degree)

            # Ensure min and max are in correct order
            if min_pulse > max_pulse:
                min_pulse, max_pulse = max_pulse, min_pulse
        else:
            # For foot servos, use the original logic
            if point1.pulse_width > point2.pulse_width:
                point1, point2 = point2, point1

            min_pulse: int = cast(int, point1.pulse_width)
            max_pulse: int = cast(int, point2.pulse_width)

        # Calculate the target range
        target_range = self.spec.target_max_angle - self.spec.target_min_angle
        calculated_range = int(target_range)

        # Save to configuration
        self.calibrator.config_provider.set_servo_min_pulse(self.calibrator.servo_name, min_pulse)
        self.calibrator.config_provider.set_servo_max_pulse(self.calibrator.servo_name, max_pulse)
        self.calibrator.config_provider.set_servo_range(self.calibrator.servo_name, calculated_range)
        self.calibrator.config_provider.set_servo_rest_angle(self.calibrator.servo_name, int(self.spec.rest_angle))
        self.calibrator.config_provider.save_config()

        # Reload servo configuration with new calibrated values
        servo_config = self.calibrator.config_provider.get_servo(self.calibrator.servo_name)
        self.calibrator.servo.min_pulse = servo_config.min_pulse
        self.calibrator.servo.max_pulse = servo_config.max_pulse
        self.calibrator.servo.rest_angle = servo_config.rest_angle

        # Move servo to home/rest position after calibration is saved
        self.calibrator.set_servo_angle(int(self.spec.rest_angle))

    def run(self) -> bool:
        """Run the complete calibration wizard."""
        try:
            if not self.show_introduction():
                return False

            for i, point in enumerate(self.spec.points):
                if not self.capture_calibration_point(i, point):
                    return False

            if not self.show_confirmation():
                return False

            self.calculate_and_save_parameters()
            return True

        except Exception as e:
            print(LABELS.WIZARD_ERROR_CALIBRATION.format(e))
            return False


def main(servo_id: str) -> None:
    """Main entry point for calibration wizard.

    Args:
        servo_id: The servo ID to calibrate, or "all" to calibrate all servos
    """
    try:
        # Handle "all" case
        if servo_id.lower() == "all":
            servo_ids = [s.value for s in ServoName]
            successful = []
            failed = []

            for sid in servo_ids:
                try:
                    _calibrate_single_servo(sid)
                    successful.append(sid)
                except Exception as e:
                    print(LABELS.WIZARD_ERROR_CALIBRATING.format(sid, e))
                    failed.append(sid)

            print(LABELS.WIZARD_SEPARATOR)
            print(LABELS.WIZARD_SUCCESS_COUNT.format(len(successful)))
            print(LABELS.WIZARD_FAILED_COUNT.format(len(failed)))
            if failed:
                print(LABELS.WIZARD_FAILED_SERVOS.format(', '.join(failed)))
            return

        # Single servo calibration
        _calibrate_single_servo(servo_id)

    except KeyboardInterrupt:
        print(LABELS.WIZARD_INTERRUPTED)
        sys.exit(1)
    except Exception as e:
        print(LABELS.WIZARD_ERROR_GENERAL.format(e))
        sys.exit(1)


def _calibrate_single_servo(servo_id: str) -> None:
    """Calibrate a single servo.

    Args:
        servo_id: The servo ID to calibrate

    Raises:
        ValueError: If servo_id is invalid
    """
    # Validate servo ID
    try:
        servo_enum = ServoName(servo_id)
    except ValueError:
        print(LABELS.WIZARD_INVALID_SERVO_ID.format(servo_id))
        print(LABELS.WIZARD_VALID_SERVO_IDS.format(', '.join([s.value for s in ServoName])))
        raise

    # Get joint type and calibration spec
    joint_type = get_joint_type_from_servo_name(servo_enum)
    spec = get_calibration_spec(joint_type)

    # Initialize calibrator
    calibrator = ServoCalibrator(servo_enum)

    # Run wizard
    def wizard_wrapper(stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        ui_utils.CursesUIHelper.init_colors(THEME.DEFAULT_THEME)
        stdscr.bkgd(" ", curses.color_pair(THEME.BACKGROUND))
        stdscr.refresh()

        wizard = CalibrationWizard(stdscr, calibrator, spec)
        return wizard.run()

    result = curses.wrapper(wizard_wrapper)

    if result:
        print(LABELS.WIZARD_SUCCESS_SINGLE.format(servo_id))
    else:
        print(LABELS.WIZARD_CANCELLED.format(servo_id))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(LABELS.WIZARD_USAGE)
        sys.exit(1)

    servo_id_arg = sys.argv[1]
    main(servo_id_arg)
