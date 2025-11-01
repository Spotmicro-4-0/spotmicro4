"""Servo module with calibration support."""

from dataclasses import dataclass
from typing import Dict

from spotmicroai.hardware.servo._joint_type import JointType


@dataclass
class AngleLimits:
    """Defines the angle limits for a servo joint."""

    min_angle: int
    max_angle: int
    rest_angle: int


JOINT_ANGLE_LIMITS: Dict[JointType, AngleLimits] = {
    JointType.SHOULDER: AngleLimits(min_angle=60, max_angle=120, rest_angle=90),
    JointType.LEG: AngleLimits(min_angle=-20, max_angle=110, rest_angle=90),
    JointType.FOOT: AngleLimits(min_angle=17, max_angle=131, rest_angle=17),
}
