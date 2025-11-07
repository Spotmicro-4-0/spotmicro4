"""
Telemetry Service Module for SpotMicroAI Motion Controller

This module provides the TelemetryService class for collecting telemetry data.
"""

from typing import Any, Dict, Optional


class TelemetryService:
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

        # Get state machine
        state_machine = getattr(mc, '_state_machine', None)

        telemetry = {
            # System status
            'current_state': state_machine.current_state.value if state_machine else 'unknown',
            'is_idle': state_machine.is_idle() if state_machine else True,
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
