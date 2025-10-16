"""
Telemetry Display Module for SpotMicroAI Motion Controller

This module provides a static terminal display that shows real-time robot state
information in a clean, non-scrolling format. All values are updated in place.
"""

from datetime import datetime
import os
import sys
from typing import Any, Dict, Optional


class TelemetryDisplay:
    """A static terminal display for robot telemetry data."""

    def __init__(self):
        self._is_windows = sys.platform.startswith('win')
        self._initialized = False
        self._line_count = 0

    def clear_screen(self):
        """Clear the terminal screen."""
        if self._is_windows:
            os.system('cls')
        else:
            os.system('clear')

    def initialize(self):
        """Initialize the display - clear screen and show header."""
        self.clear_screen()
        self._initialized = True

    def _move_cursor_home(self):
        """Move cursor to home position."""
        if self._is_windows:
            # Windows PowerShell ANSI escape codes
            print("\033[H", end='', flush=True)
        else:
            # Unix/Linux ANSI escape codes
            print("\033[H", end='', flush=True)

    def _format_value(self, value: Any, width: int = 10) -> str:
        """Format a value for display with fixed width."""
        if value is None:
            return "N/A".ljust(width)
        elif isinstance(value, float):
            return f"{value:>{width}.2f}"
        elif isinstance(value, bool):
            return ("YES" if value else "NO").ljust(width)
        else:
            return str(value).ljust(width)

    def _format_coordinate(self, coord: Any, width: int = 35) -> str:
        """Format a coordinate for display."""
        if coord is None:
            return "N/A".ljust(width)
        try:
            return f"X:{coord.x:>6.1f} Y:{coord.y:>6.1f} Z:{coord.z:>6.1f}".ljust(width)
        except Exception:
            return "ERROR".ljust(width)

    def update(self, telemetry_data: Dict[str, Any]):
        """Update the display with new telemetry data.

        Parameters
        ----------
        telemetry_data : Dict[str, Any]
            Dictionary containing all telemetry values to display.
        """
        if not self._initialized:
            self.initialize()

        # Move cursor to home position
        self._move_cursor_home()

        # Build the display output
        lines = []

        # Header
        lines.append("=" * 100)
        lines.append(" " * 30 + "SPOTMICRO AI - TELEMETRY DISPLAY")
        lines.append("=" * 100)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"Timestamp: {timestamp}")
        lines.append("")

        # System Status Section
        lines.append("+ SYSTEM STATUS " + "-" * 82 + "+")
        lines.append(
            f"| Activated: {self._format_value(telemetry_data.get('is_activated'), 15)} "
            f"Running: {self._format_value(telemetry_data.get('is_running'), 15)} "
            f"Frame Rate: {self._format_value(telemetry_data.get('frame_rate'), 10)} Hz |"
        )
        lines.append(
            f"| Loop Time: {self._format_value(telemetry_data.get('loop_time_ms'), 15)} ms "
            f"Idle Time: {self._format_value(telemetry_data.get('idle_time_ms'), 15)} ms " + " " * 20 + "|"
        )
        lines.append("+" + "-" * 98 + "+")
        lines.append("")

        # Motion Parameters Section
        lines.append("+ MOTION PARAMETERS " + "-" * 78 + "+")
        lines.append(
            f"| Forward Factor:  {self._format_value(telemetry_data.get('forward_factor'), 10)} "
            f"| Rotation Factor: {self._format_value(telemetry_data.get('rotation_factor'), 10)} |"
        )
        lines.append(
            f"| Lean Factor:     {self._format_value(telemetry_data.get('lean_factor'), 10)} "
            f"| Height Factor:   {self._format_value(telemetry_data.get('height_factor'), 10)} |"
        )
        lines.append(
            f"| Walking Speed:   {self._format_value(telemetry_data.get('walking_speed'), 10)} "
            f"| Cycle Index:     {self._format_value(telemetry_data.get('cycle_index'), 10)} |"
        )
        lines.append(
            f"| Cycle Ratio:     {self._format_value(telemetry_data.get('cycle_ratio'), 10)} "
            f"| Elapsed Time:    {self._format_value(telemetry_data.get('elapsed_time'), 10)} s  |"
        )
        lines.append("+" + "-" * 98 + "+")
        lines.append("")

        # Controller Events Section
        lines.append("+ CONTROLLER EVENTS " + "-" * 78 + "+")
        events = telemetry_data.get('controller_events', {})
        lines.append(
            f"| Left Stick:   X={self._format_value(events.get('lx', 0), 7)} Y={self._format_value(events.get('ly', 0), 7)} "
            f"| Right Stick:  X={self._format_value(events.get('rz', 0), 7)} Y={self._format_value(events.get('lz', 0), 7)} |"
        )
        lines.append(
            f"| D-Pad:        X={self._format_value(events.get('hat0x', 0), 7)} Y={self._format_value(events.get('hat0y', 0), 7)} "
            f"| Triggers:     L={self._format_value(events.get('brake', 0), 7)} R={self._format_value(events.get('gas', 0), 7)} |"
        )
        lines.append(
            f"| Buttons:      A={self._format_value(events.get('a', 0), 3)} B={self._format_value(events.get('b', 0), 3)} "
            f"X={self._format_value(events.get('x', 0), 3)} Y={self._format_value(events.get('y', 0), 3)} "
            f"START={self._format_value(events.get('start', 0), 3)} BACK={self._format_value(events.get('select', 0), 3)} "
            + " " * 15
            + "|"
        )
        lines.append("+" + "-" * 98 + "+")
        lines.append("")

        # Leg Coordinates Section - Current Positions
        lines.append("+ LEG COORDINATES (Current Target) " + "-" * 62 + "+")
        leg_positions = telemetry_data.get('leg_positions', {})
        lines.append(
            f"| Front Right:  {self._format_coordinate(leg_positions.get('front_right'))} "
            f"| Front Left:   {self._format_coordinate(leg_positions.get('front_left'))} |"
        )
        lines.append(
            f"| Rear Right:   {self._format_coordinate(leg_positions.get('rear_right'))} "
            f"| Rear Left:    {self._format_coordinate(leg_positions.get('rear_left'))} |"
        )
        lines.append("+" + "-" * 98 + "+")
        lines.append("")

        # Servo Angles Section - Front Legs
        lines.append("+ SERVO ANGLES (Staged) " + "-" * 74 + "+")
        servo_angles = telemetry_data.get('servo_angles', {})
        lines.append(
            "| FRONT LEGS:                                                                                          |"
        )
        lines.append(
            f"|   Right → Shoulder: {self._format_value(servo_angles.get('front_shoulder_right'), 7)}° "
            f"Leg: {self._format_value(servo_angles.get('front_leg_right'), 7)}° "
            f"Foot: {self._format_value(servo_angles.get('front_foot_right'), 7)}° " + " " * 17 + "|"
        )
        lines.append(
            f"|   Left  → Shoulder: {self._format_value(servo_angles.get('front_shoulder_left'), 7)}° "
            f"Leg: {self._format_value(servo_angles.get('front_leg_left'), 7)}° "
            f"Foot: {self._format_value(servo_angles.get('front_foot_left'), 7)}° " + " " * 17 + "|"
        )
        lines.append(
            "|                                                                                                      |"
        )
        lines.append(
            "| REAR LEGS:                                                                                           |"
        )
        lines.append(
            f"|   Right → Shoulder: {self._format_value(servo_angles.get('rear_shoulder_right'), 7)}° "
            f"Leg: {self._format_value(servo_angles.get('rear_leg_right'), 7)}° "
            f"Foot: {self._format_value(servo_angles.get('rear_foot_right'), 7)}° " + " " * 17 + "|"
        )
        lines.append(
            f"|   Left  → Shoulder: {self._format_value(servo_angles.get('rear_shoulder_left'), 7)}° "
            f"Leg: {self._format_value(servo_angles.get('rear_leg_left'), 7)}° "
            f"Foot: {self._format_value(servo_angles.get('rear_foot_left'), 7)}° " + " " * 17 + "|"
        )
        lines.append("+" + "-" * 98 + "+")
        lines.append("")

        # Footer
        lines.append("-" * 100)
        lines.append("Press START to disable servos | Press CTRL+C to exit")
        lines.append("-" * 100)

        # Print all lines (this will overwrite the previous display)
        output = "\n".join(lines)
        print(output, flush=True)


class TelemetryCollector:
    """Collects telemetry data from motion controller components."""

    def __init__(self, motion_controller):
        """Initialize with reference to motion controller.

        Parameters
        ----------
        motion_controller : MotionController
            The motion controller instance to collect data from.
        """
        self._motion_controller = motion_controller

    def collect(
        self,
        event: Dict,
        loop_time_ms: float,
        idle_time_ms: float,
        cycle_index: Optional[int] = None,
        cycle_ratio: Optional[float] = None,
        leg_positions: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Collect current telemetry data from all sources.

        Parameters
        ----------
        event : Dict
            Current controller event data.
        loop_time_ms : float
            Time taken for the current loop iteration in milliseconds.
        idle_time_ms : float
            Idle/sleep time in the current loop in milliseconds.
        cycle_index : Optional[int]
            Current walking cycle index.
        cycle_ratio : Optional[float]
            Current walking cycle interpolation ratio.
        leg_positions : Optional[Dict]
            Current interpolated leg positions.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing all collected telemetry data.
        """
        mc = self._motion_controller

        # Collect keyframe service data
        kf_service = getattr(mc, '_keyframe_service', None)

        # Collect servo service data
        servo_service = getattr(mc, '_servo_service', None)

        telemetry = {
            # System status
            'is_activated': mc.is_activated,
            'is_running': mc.is_running,
            'frame_rate': 50.0,  # Fixed at 50Hz
            'loop_time_ms': loop_time_ms,
            'idle_time_ms': idle_time_ms,
            # Motion parameters from keyframe service
            'forward_factor': kf_service.forward_factor if kf_service else None,
            'rotation_factor': kf_service.rotation_factor if kf_service else None,
            'lean_factor': kf_service.lean_factor if kf_service else None,
            'height_factor': kf_service.height_factor if kf_service else None,
            'walking_speed': kf_service.walking_speed if kf_service else None,
            'elapsed_time': kf_service.elapsed if kf_service else None,
            'cycle_index': cycle_index,
            'cycle_ratio': cycle_ratio,
            # Controller events
            'controller_events': event if event else {},
            # Leg positions (coordinates)
            'leg_positions': leg_positions if leg_positions else {},
            # Servo angles
            'servo_angles': {},
        }

        # Collect servo angles if servo service is available
        if servo_service:
            try:
                telemetry['servo_angles'] = {
                    'front_shoulder_right': servo_service.front_shoulder_right_angle,
                    'front_leg_right': servo_service.front_leg_right_angle,
                    'front_foot_right': servo_service.front_foot_right_angle,
                    'front_shoulder_left': servo_service.front_shoulder_left_angle,
                    'front_leg_left': servo_service.front_leg_left_angle,
                    'front_foot_left': servo_service.front_foot_left_angle,
                    'rear_shoulder_right': servo_service.rear_shoulder_right_angle,
                    'rear_leg_right': servo_service.rear_leg_right_angle,
                    'rear_foot_right': servo_service.rear_foot_right_angle,
                    'rear_shoulder_left': servo_service.rear_shoulder_left_angle,
                    'rear_leg_left': servo_service.rear_leg_left_angle,
                    'rear_foot_left': servo_service.rear_foot_left_angle,
                }
            except AttributeError:
                # Servo service not fully initialized yet
                pass

        return telemetry
