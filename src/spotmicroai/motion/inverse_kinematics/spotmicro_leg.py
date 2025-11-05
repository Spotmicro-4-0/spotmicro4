# spot_micro_leg.py
from dataclasses import dataclass

import numpy as np

from .models import JointAngles, LinkLengths, Point
from .utils import (
    apply_inverse_kinematics,
    homogeneous_inverse,
    homogeneous_transform_joint0_to_1,
    homogeneous_transform_joint0_to_4,
    homogeneous_transform_joint1_to_2,
    homogeneous_transform_joint2_to_3,
    homogeneous_transform_joint3_to_4,
)


@dataclass
class SpotmicroLeg:
    """
    Produces identical joint angles and transforms, including is_leg_12 symmetry.
    """

    joint_angles: JointAngles
    link_lengths: LinkLengths
    is_leg_12: bool

    def __init__(self, joint_angles: JointAngles, link_lengths: LinkLengths, is_leg_12: bool):
        self.joint_angles = joint_angles
        self.link_lengths = link_lengths
        self.is_leg_12 = is_leg_12

    def set_foot_pos_global(self, foot_pos_global: Point, ht_leg_start: np.ndarray):
        """
        Equivalent to SpotMicroLeg::setFootPosGlobalCoordinates().
        Transforms global foot position into the local leg frame, runs ikine(),
        and updates joint_angles.
        """

        # Build homogeneous vector for point
        p4_ht_vec = np.array([[foot_pos_global.x], [foot_pos_global.y], [foot_pos_global.z], [1.0]])

        # Transform global position to leg-local frame
        ht_leg_inv = homogeneous_inverse(ht_leg_start)
        p4_ht_vec_leg = ht_leg_inv @ p4_ht_vec

        # Extract coordinates in leg frame
        p4_local = Point(
            x=float(p4_ht_vec_leg[0, 0]),
            y=float(p4_ht_vec_leg[1, 0]),
            z=float(p4_ht_vec_leg[2, 0]),
        )

        # Run inverse kinematics with identical is_leg_12 flag
        self.joint_angles = apply_inverse_kinematics(p4_local, self.link_lengths, self.is_leg_12)

    # -----------------------------------------------------------------------
    # Forward Kinematics
    # -----------------------------------------------------------------------
    def get_foot_pos_global(self, ht_leg_start: np.ndarray) -> Point:
        """
        Equivalent to SpotMicroLeg::getFootPosGlobalCoordinates().
        Uses ht_leg_start * ht0To4(joint_angles, link_lengths)
        """

        ht_leg_to_foot = homogeneous_transform_joint0_to_4(self.joint_angles, self.link_lengths)
        ht_body_to_foot = ht_leg_start @ ht_leg_to_foot

        # Foot position is last column (translation)
        x = ht_body_to_foot[0, 3]
        y = ht_body_to_foot[1, 3]
        z = ht_body_to_foot[2, 3]

        return Point(float(x), float(y), float(z))

    # -----------------------------------------------------------------------
    # Partial Transform Accessors (debugging)
    # -----------------------------------------------------------------------
    def get_transform_0_to_1(self) -> np.ndarray:
        """Equivalent to SpotMicroLeg::getTransform0To1()."""
        return homogeneous_transform_joint0_to_1(self.joint_angles.th1, self.link_lengths.l1)

    def get_transform_1_to_3(self) -> np.ndarray:
        """
        Equivalent to SpotMicroLeg::getTransform1To3().
        Returns the combined transform from joint 1 to joint 3 (ht1To2 * ht2To3).
        """
        return (homogeneous_transform_joint1_to_2() @ 
                homogeneous_transform_joint2_to_3(self.joint_angles.th2, self.link_lengths.l2))

    def get_transform_3_to_4(self) -> np.ndarray:
        """Equivalent to SpotMicroLeg::getTransform3To4()."""
        return homogeneous_transform_joint3_to_4(self.joint_angles.th3, self.link_lengths.l3)

    def set_angles(self, joint_angles: JointAngles):
        """Set the joint angles of the leg."""
        self.joint_angles = joint_angles
