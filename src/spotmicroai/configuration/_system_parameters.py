from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from typing import Dict, List

from spotmicroai.singleton import Singleton


@dataclass
class SystemParameters(metaclass=Singleton):
    """Configuration parameters for the robotic system."""

    # Robot dimensions
    hip_link_length: float
    upper_leg_link_length: float
    lower_leg_link_length: float
    body_width: float
    body_length: float

    # Stand and lie down parameters
    default_stand_height: float
    stand_front_x_offset: float
    stand_back_x_offset: float
    lie_down_height: float
    lie_down_feet_x_offset: float

    # Servo parameters
    num_servos: int
    servo_max_angle_deg: float

    # Control parameters
    dt: float
    transit_tau: float
    transit_rl: float
    transit_angle_rl: float

    # Velocity limits
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
    foot_height_time_constant: float
    body_shift_phases: List[int]
    fwd_body_balance_shift: float
    side_body_balance_shift: float
    back_body_balance_shift: float

    # Servo config (has default)
    servo_config: Dict[str, Dict[str, float]] = field(default_factory=dict)
    debug_mode: bool = False
    run_standalone: bool = False
    plot_mode: bool = False

    # Derived gait parameters (computed from above)
    overlap_ticks: int = 0
    swing_ticks: int = 0
    stance_ticks: int = 0
    phase_ticks: List[int] = field(default_factory=list)
    phase_length: int = 0

    # Odometry
    publish_odom: bool = False

    # Lidar position
    lidar_x_pos: float = 0.0
    lidar_y_pos: float = 0.0
    lidar_z_pos: float = 0.0
    lidar_yaw_angle: float = 0.0

    def __init__(self):
        """Initialize RemoteControllerBindings by loading from JSON file."""
        json_path: Path = Path.home() / 'spotmicroai' / 'configuration' / 'system_parameters.json'
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"System Parameters file not found: {json_path}")

        # Load from JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Set all attributes from loaded data
        for key, value in data.items():
            setattr(self, key, value)

        # Compute derived parameters
        self._calculate_additional_parameters()

    def _calculate_additional_parameters(self) -> None:
        """Compute derived gait timing parameters."""
        self.overlap_ticks = round(self.overlap_time / self.dt)
        self.swing_ticks = round(self.swing_time / self.dt)

        if self.num_phases == 8:
            # 8 Phase gait specific
            self.stance_ticks = 7 * self.swing_ticks
            self.phase_ticks = [self.swing_ticks] * 8
            self.phase_length = self.num_phases * self.swing_ticks
        else:
            # 4 phase gait specific
            self.stance_ticks = 2 * self.overlap_ticks + self.swing_ticks
            self.phase_ticks = [self.overlap_ticks, self.swing_ticks, self.overlap_ticks, self.swing_ticks]
            self.phase_length = 2 * self.swing_ticks + 2 * self.overlap_ticks
