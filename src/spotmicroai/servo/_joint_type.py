from enum import Enum


class JointType(Enum):
    """Different types of joints in the robot."""

    FOOT = "foot"
    LEG = "leg"
    SHOULDER = "shoulder"
