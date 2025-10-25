from dataclasses import dataclass
from enum import Enum


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
