from dataclasses import dataclass, field

@dataclass
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@dataclass
class JointAngles:
    """Joint angles (radians) for one leg."""

    theta1: float  # Hip yaw
    theta2: float  # Hip pitch
    theta3: float  # Knee pitch


@dataclass
class LegsFootPositions:
    right_back: Point = field(default_factory=Point)
    right_front: Point = field(default_factory=Point)
    left_front: Point = field(default_factory=Point)
    left_back: Point = field(default_factory=Point)


@dataclass
class LegsJointAngles:
    rear_right: JointAngles
    front_right: JointAngles
    front_left: JointAngles
    rear_left: JointAngles


@dataclass
class BodyState:
    phi: float = 0.0
    theta: float = 0.0
    psi: float = 0.0
    position: Point = field(default_factory=Point)
    legs_foot_positions: LegsFootPositions = field(default_factory=LegsFootPositions)
