"""
Telemetry Data Model for Motion Controller

This module defines strongly-typed telemetry data structures.
"""

from dataclasses import dataclass

from spotmicroai.runtime.controller_event import ControllerEvent


@dataclass
class LegPosition:
    """3D position of a leg."""
    x: float
    y: float
    z: float


@dataclass
class LegPositions:
    """Positions of all four legs."""
    front_right: LegPosition | None = None
    front_left: LegPosition | None = None
    rear_right: LegPosition | None = None
    rear_left: LegPosition | None = None


@dataclass
class ServoAngles:
    """Current angles of all servos."""
    front_shoulder_right: float | None = None
    front_leg_right: float | None = None
    front_foot_right: float | None = None
    front_shoulder_left: float | None = None
    front_leg_left: float | None = None
    front_foot_left: float | None = None
    rear_shoulder_right: float | None = None
    rear_leg_right: float | None = None
    rear_foot_right: float | None = None
    rear_shoulder_left: float | None = None
    rear_leg_left: float | None = None
    rear_foot_left: float | None = None


@dataclass
class TelemetryData:
    """Complete telemetry snapshot from the motion controller."""

    # System status
    is_activated: bool
    is_running: bool
    frame_rate: float
    loop_time_ms: float
    idle_time_ms: float

    # Motion parameters
    forward_factor: float | None = None
    rotation_factor: float | None = None
    lean_factor: float | None = None
    height_factor: float | None = None
    walking_speed: float | None = None
    elapsed_time: float | None = None
    cycle_index: int | None = None
    cycle_ratio: float | None = None

    # Controller input
    controller_event: ControllerEvent | None = None

    # Leg positions
    leg_positions: LegPositions | None = None

    # Servo angles
    servo_angles: ServoAngles | None = None
