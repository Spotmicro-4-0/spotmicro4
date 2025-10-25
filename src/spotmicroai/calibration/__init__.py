from dataclasses import dataclass

from spotmicroai.servo import JointType


@dataclass
class CalibrationPoint:
    """Represents a calibration point with angle and pulse width."""

    description: str
    physical_angle: int  # The actual angle in degrees IRL
    pulse_width: int | None = None  # Captured pulse width in microseconds


@dataclass
class JointCalibrationSpec:
    """Specification for calibrating a specific joint type."""

    joint_type: JointType
    points: list[CalibrationPoint]
    target_min_angle: int
    target_max_angle: int
    rest_angle: int
