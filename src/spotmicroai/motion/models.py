from dataclasses import dataclass, field

import numpy as np


class EulerAngles:
    phi: float = 0.0
    theta: float = 0.0
    psi: float = 0.0


@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class LegsFootPositions:
    right_back: Point = field(default_factory=Point)
    right_front: Point = field(default_factory=Point)
    left_front: Point = field(default_factory=Point)
    left_back: Point = field(default_factory=Point)


@dataclass
class BodyState:
    euler_angles: EulerAngles = field(default_factory=EulerAngles)
    xyz_positions: Point = field(default_factory=Point)
    leg_feet_positions: LegsFootPositions = field(default_factory=LegsFootPositions)


@dataclass
class JointAngles:
    """Joint angles (radians) for one leg."""

    theta1: float  # Hip yaw
    theta2: float  # Hip pitch
    theta3: float  # Knee pitch


@dataclass
class LegsJointAngles:
    right_back: JointAngles
    right_front: JointAngles
    left_front: JointAngles
    left_back: JointAngles


@dataclass
class LegRelativeTransforms:
    """Transforms from body frame to each leg’s base frame."""

    leg_right_back: np.ndarray
    leg_right_front: np.ndarray
    leg_left_front: np.ndarray
    leg_left_back: np.ndarray


@dataclass
class LegTransforms:
    """Joint-to-joint transforms for one leg."""

    t01: np.ndarray = field(default_factory=lambda: np.eye(4))
    t13: np.ndarray = field(default_factory=lambda: np.eye(4))
    t34: np.ndarray = field(default_factory=lambda: np.eye(4))


@dataclass
class AllRobotRelativeTransforms:
    """All transforms for full kinematic visualization."""

    body_center: np.ndarray = field(default_factory=lambda: np.eye(4))
    center_to_right_back: np.ndarray = field(default_factory=lambda: np.eye(4))
    center_to_right_front: np.ndarray = field(default_factory=lambda: np.eye(4))
    center_to_left_front: np.ndarray = field(default_factory=lambda: np.eye(4))
    center_to_left_back: np.ndarray = field(default_factory=lambda: np.eye(4))

    right_back_leg: LegTransforms = field(default_factory=LegTransforms)
    right_front_leg: LegTransforms = field(default_factory=LegTransforms)
    left_front_leg: LegTransforms = field(default_factory=LegTransforms)
    left_back_leg: LegTransforms = field(default_factory=LegTransforms)
