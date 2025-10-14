from dataclasses import dataclass

from spotmicroai.motion_controller.models.servo_angles import ServoAngles


@dataclass
class Pose:
    """A class that holds four ServoAngles for the robot's legs.

    Used to describe the angles for all servo motors in the robot.

    Attributes:
        rear_left: ServoAngles for the rear left leg.
        rear_right: ServoAngles for the rear right leg.
        front_left: ServoAngles for the front left leg.
        front_right: ServoAngles for the front right leg.
    """
    rear_left: ServoAngles
    rear_right: ServoAngles
    front_left: ServoAngles
    front_right: ServoAngles