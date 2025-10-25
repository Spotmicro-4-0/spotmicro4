from enum import Enum


class ServoName(Enum):
    """Enum for all 12 servo names"""

    FRONT_SHOULDER_LEFT = 'front_shoulder_left'
    FRONT_LEG_LEFT = 'front_leg_left'
    FRONT_FOOT_LEFT = 'front_foot_left'
    FRONT_SHOULDER_RIGHT = 'front_shoulder_right'
    FRONT_LEG_RIGHT = 'front_leg_right'
    FRONT_FOOT_RIGHT = 'front_foot_right'
    REAR_SHOULDER_LEFT = 'rear_shoulder_left'
    REAR_LEG_LEFT = 'rear_leg_left'
    REAR_FOOT_LEFT = 'rear_foot_left'
    REAR_SHOULDER_RIGHT = 'rear_shoulder_right'
    REAR_LEG_RIGHT = 'rear_leg_right'
    REAR_FOOT_RIGHT = 'rear_foot_right'
