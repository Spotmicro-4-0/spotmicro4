"""
This module defines the Keyframe class for representing foot positions at a point in time.
"""

from dataclasses import dataclass, field

from spotmicroai.runtime.motion_controller.models.coordinate import Coordinate
from spotmicroai.runtime.motion_controller.models.pose import Pose
from spotmicroai.runtime.motion_controller.models.servo_angles import ServoAngles


@dataclass
class Keyframe:
    """A class defining the positions of the 4 feet at a given point in time.

    Attributes:
        front_left: The position of the left front leg (FootCoordinate).
        front_right: The position of the right front leg (FootCoordinate).
        rear_left: The position of the left rear leg (FootCoordinate).
        rear_right: The position of the right rear leg (FootCoordinate).
    """

    front_left: Coordinate = field(default_factory=Coordinate)
    front_right: Coordinate = field(default_factory=Coordinate)
    rear_left: Coordinate = field(default_factory=Coordinate)
    rear_right: Coordinate = field(default_factory=Coordinate)

    def to_pose(self) -> Pose:
        """Convert the keyframe coordinates to servo angles for all four legs.

        Returns
        -------
        Pose
            A Pose object containing ServoAngles for each leg.
        """
        fl_foot, fl_leg, fl_shoulder = self.front_left.inverse_kinematics()
        fr_foot, fr_leg, fr_shoulder = self.front_right.inverse_kinematics()
        rl_foot, rl_leg, rl_shoulder = self.rear_left.inverse_kinematics()
        rr_foot, rr_leg, rr_shoulder = self.rear_right.inverse_kinematics()

        return Pose(
            front_left=ServoAngles(shoulder_angle=fl_shoulder, leg_angle=fl_leg, foot_angle=fl_foot),
            front_right=ServoAngles(shoulder_angle=fr_shoulder, leg_angle=fr_leg, foot_angle=fr_foot),
            rear_left=ServoAngles(shoulder_angle=rl_shoulder, leg_angle=rl_leg, foot_angle=rl_foot),
            rear_right=ServoAngles(shoulder_angle=rr_shoulder, leg_angle=rr_leg, foot_angle=rr_foot),
        )
