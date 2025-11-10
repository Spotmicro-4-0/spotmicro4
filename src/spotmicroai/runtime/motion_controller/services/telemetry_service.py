"""
Telemetry Service Module for SpotMicroAI Motion Controller

This module provides the TelemetryService class for collecting telemetry data.
"""

import queue
from typing import Dict
from spotmicroai import labels
from spotmicroai.logger import Logger
from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.messaging import MessageBus
from spotmicroai.runtime.motion_controller.models.telemetry_data import (
    LegPosition,
    LegPositions,
    ServoAngles,
    TelemetryData,
)
from spotmicroai.singleton import Singleton
import spotmicroai.constants as constants

log = Logger().setup_logger('Telemetry Service')


class TelemetryService(metaclass=Singleton):
    """Collects telemetry data from motion controller components."""

    def __init__(self, motion_controller):
        """Initialize with reference to motion controller.

        Parameters
        ----------
        motion_controller : MotionController
            The motion controller instance to collect data from.
        """
        self._motion_controller = motion_controller
        self._message_bus = MessageBus()
        self._telemetry_topic = self._message_bus._telemetry
        self._update_counter = 0

    def publish(
        self,
        event: ControllerEvent | None,
        loop_time_ms: float,
        idle_time_ms: float,
        cycle_index: int | None = None,
        cycle_ratio: float | None = None,
        leg_positions: Dict | None = None,
    ) -> None:
        """Collect and publish telemetry data from all sources.

        Parameters
        ----------
        event : ControllerEvent
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
        """
        self._update_counter = (self._update_counter + 1) % constants.TELEMETRY_UPDATE_INTERVAL
        if self._update_counter != 0:
            return

        if self._telemetry_topic is None:
            return

        try:
            queue_stats = self._message_bus.get_queue_stats()

            telemetry_data = self._collect(
                event=event,
                loop_time_ms=loop_time_ms,
                idle_time_ms=idle_time_ms,
                cycle_index=cycle_index,
                cycle_ratio=cycle_ratio,
                leg_positions=leg_positions,
                queue_stats=queue_stats,
            )

            try:
                self._telemetry_topic.put(telemetry_data, block=False)
            except queue.Full:
                log.debug(labels.MOTION_TELEMETRY_QUEUE_FULL)
        except Exception as e:
            log.warning(labels.MOTION_TELEMETRY_ERROR.format(e))

    def _collect(
        self,
        event: ControllerEvent | None,
        loop_time_ms: float,
        idle_time_ms: float,
        cycle_index: int | None = None,
        cycle_ratio: float | None = None,
        leg_positions: dict | None = None,
        queue_stats: Dict[str, int] | None = None,
    ) -> TelemetryData:
        """Collect current telemetry data from all sources.

        Parameters
        ----------
        event : ControllerEvent | None
            Current controller event data.
        loop_time_ms : float
            Time taken for the current loop iteration in milliseconds.
        idle_time_ms : float
            Idle/sleep time in the current loop in milliseconds.
        cycle_index : int | None
            Current walking cycle index.
        cycle_ratio : float | None
            Current walking cycle interpolation ratio.
        leg_positions : dict | None
            Current interpolated leg positions.

        Returns
        -------
        TelemetryData
            Strongly-typed telemetry data snapshot.
        """
        mc = self._motion_controller

        # Collect keyframe service data
        kf_service = getattr(mc, '_keyframe_service', None)

        # Collect servo service data
        servo_service = getattr(mc, '_servo_service', None)

        # Build servo angles
        servo_angles = None
        if servo_service:
            try:
                servo_angles = ServoAngles(
                    front_shoulder_right=servo_service.front_shoulder_right_angle,
                    front_leg_right=servo_service.front_leg_right_angle,
                    front_foot_right=servo_service.front_foot_right_angle,
                    front_shoulder_left=servo_service.front_shoulder_left_angle,
                    front_leg_left=servo_service.front_leg_left_angle,
                    front_foot_left=servo_service.front_foot_left_angle,
                    rear_shoulder_right=servo_service.rear_shoulder_right_angle,
                    rear_leg_right=servo_service.rear_leg_right_angle,
                    rear_foot_right=servo_service.rear_foot_right_angle,
                    rear_shoulder_left=servo_service.rear_shoulder_left_angle,
                    rear_leg_left=servo_service.rear_leg_left_angle,
                    rear_foot_left=servo_service.rear_foot_left_angle,
                )
            except AttributeError:
                # Servo service not fully initialized yet
                pass

        # Build leg positions (convert dict to LegPositions if present)
        leg_positions_obj = None
        if leg_positions:
            try:
                leg_positions_obj = LegPositions(
                    front_right=self._dict_to_leg_position(leg_positions.get('front_right')),
                    front_left=self._dict_to_leg_position(leg_positions.get('front_left')),
                    rear_right=self._dict_to_leg_position(leg_positions.get('rear_right')),
                    rear_left=self._dict_to_leg_position(leg_positions.get('rear_left')),
                )
            except (KeyError, AttributeError, TypeError):
                pass

        return TelemetryData(
            is_activated=mc._is_activated,
            is_running=mc._is_running,
            frame_rate=50.0,
            loop_time_ms=loop_time_ms,
            idle_time_ms=idle_time_ms,
            queue_stats=queue_stats or {},
            forward_factor=kf_service.forward_factor if kf_service else None,
            rotation_factor=kf_service.rotation_factor if kf_service else None,
            lean_factor=kf_service.lean_factor if kf_service else None,
            height_factor=kf_service.height_factor if kf_service else None,
            walking_speed=kf_service.walking_speed if kf_service else None,
            elapsed_time=kf_service.elapsed if kf_service else None,
            cycle_index=cycle_index,
            cycle_ratio=cycle_ratio,
            controller_event=event,
            leg_positions=leg_positions_obj,
            servo_angles=servo_angles,
        )

    @staticmethod
    def _dict_to_leg_position(data) -> LegPosition | None:
        """Convert dict/tuple/object to LegPosition."""
        if data is None:
            return None

        if isinstance(data, dict):
            return LegPosition(x=data.get('x', 0.0), y=data.get('y', 0.0), z=data.get('z', 0.0))

        if hasattr(data, 'x') and hasattr(data, 'y') and hasattr(data, 'z'):
            return LegPosition(x=data.x, y=data.y, z=data.z)

        if isinstance(data, (tuple, list)) and len(data) >= 3:
            return LegPosition(x=data[0], y=data[1], z=data[2])

        return None
