"""
Data models for the gait controller.

Contains dataclasses for configuration, commands, state, and internal gait computations.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

from spotmicroai.runtime.motion_controller.models.coordinate import Coordinate
from spotmicroai.runtime.motion_controller.models.keyframe import Keyframe
from spotmicroai.runtime.motion_controller.models.servo_angles import ServoAngles


@dataclass
class BodyState:
    coordinate: Coordinate
    angles: ServoAngles
    keyframe: Keyframe


@dataclass
class SpotMicroNodeConfig:
    """Subset of node configuration required for gait generation."""

    # Geometry
    hip_link_length: float
    body_width: float
    body_length: float
    default_stand_height: float
    stand_front_x_offset: float
    stand_back_x_offset: float
    lie_down_height: float
    lie_down_feet_x_offset: float

    # Control limits
    max_fwd_velocity: float
    max_side_velocity: float
    max_yaw_rate: float

    # Gait parameters
    z_clearance: float
    alpha: float
    beta: float
    num_phases: int
    rb_contact_phases: List[int]
    rf_contact_phases: List[int]
    lf_contact_phases: List[int]
    lb_contact_phases: List[int]
    overlap_time: float
    swing_time: float
    body_shift_phases: List[int]
    fwd_body_balance_shift: float
    back_body_balance_shift: float
    side_body_balance_shift: float
    foot_height_time_constant: float

    # Timing
    dt: float

    # Derived at runtime
    overlap_ticks: int = 0
    swing_ticks: int = 0
    stance_ticks: int = 0
    phase_ticks: Optional[List[int]] = None
    phase_length: int = 0

    def __post_init__(self) -> None:
        self.swing_ticks = max(1, round(self.swing_time / self.dt))
        self.overlap_ticks = max(0, round(self.overlap_time / self.dt))

        if self.num_phases == 8:
            # Each phase covers one leg swing or body shift
            self.stance_ticks = 7 * self.swing_ticks
            self.phase_ticks = [self.swing_ticks] * self.num_phases
            self.phase_length = self.num_phases * self.swing_ticks
        elif self.num_phases == 4:
            self.stance_ticks = 2 * self.overlap_ticks + self.swing_ticks
            self.phase_ticks = [
                self.overlap_ticks,
                self.swing_ticks,
                self.overlap_ticks,
                self.swing_ticks,
            ]
            self.phase_length = sum(self.phase_ticks)
        else:
            raise ValueError(f"Unsupported num_phases: {self.num_phases}")

    @classmethod
    def defaults(cls) -> "SpotMicroNodeConfig":
        """Populate config using the repository's default YAML values."""
        return cls(
            hip_link_length=0.055,
            body_width=0.078,
            body_length=0.186,
            default_stand_height=0.155,
            stand_front_x_offset=0.015,
            stand_back_x_offset=-0.0,
            lie_down_height=0.083,
            lie_down_feet_x_offset=0.065,
            max_fwd_velocity=0.4,
            max_side_velocity=0.4,
            max_yaw_rate=0.35,
            z_clearance=0.050,
            alpha=0.5,
            beta=0.5,
            num_phases=8,
            rb_contact_phases=[1, 0, 1, 1, 1, 1, 1, 1],
            rf_contact_phases=[1, 1, 1, 0, 1, 1, 1, 1],
            lf_contact_phases=[1, 1, 1, 1, 1, 1, 1, 0],
            lb_contact_phases=[1, 1, 1, 1, 1, 0, 1, 1],
            overlap_time=0.0,
            swing_time=0.36,
            body_shift_phases=[1, 2, 3, 4, 5, 6, 7, 8],
            fwd_body_balance_shift=0.035,
            back_body_balance_shift=0.005,
            side_body_balance_shift=0.015,
            foot_height_time_constant=0.02,
            dt=0.02,
        )


@dataclass
class Command:
    """Body velocity and attitude commands."""

    x_vel_cmd: float
    y_vel_cmd: float
    yaw_rate_cmd: float

    def clamped(self, cfg: SpotMicroNodeConfig) -> "Command":
        return Command(
            x_vel_cmd=max(-cfg.max_fwd_velocity, min(cfg.max_fwd_velocity, self.x_vel_cmd)),
            y_vel_cmd=max(-cfg.max_side_velocity, min(cfg.max_side_velocity, self.y_vel_cmd)),
            yaw_rate_cmd=max(-cfg.max_yaw_rate, min(cfg.max_yaw_rate, self.yaw_rate_cmd)),
        )


@dataclass
class ContactFeet:
    front_left_in_swing: bool
    front_right_in_swing: bool
    rear_left_in_swing: bool
    rear_right_in_swing: bool
