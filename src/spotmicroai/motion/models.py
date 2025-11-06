from dataclasses import dataclass, field


@dataclass
class Position:
    """A coordinate in 3D space."""

    x: float = 0.0  # Forward/Backward
    y: float = 0.0  # Upward/Downward
    z: float = 0.0  # Right/Left


@dataclass
class FeetPositions:
    """Positions for all four feet."""

    front_left: Position = field(default_factory=Position)
    front_right: Position = field(default_factory=Position)
    rear_left: Position = field(default_factory=Position)
    rear_right: Position = field(default_factory=Position)


@dataclass
class LegAngles:
    """Angles in radians for one leg."""

    theta1: float  # Hip yaw
    theta2: float  # Hip pitch
    theta3: float  # Knee pitch


@dataclass
class LegAnglesSet:
    """Joint angles for all four legs."""

    front_left: LegAngles
    front_right: LegAngles
    rear_left: LegAngles
    rear_right: LegAngles


@dataclass
class BodyState:
    """State of the robot body including position, orientation, and foot placements."""

    omega: float = 0.0  # ω (roll) – rotation about the body X-axis
    phi: float = 0.0  # φ (yaw) – rotation about the body Y-axis
    psi: float = 0.0  # ψ (pitch) – rotation about the body Z-axis
    body_position: Position = field(default_factory=Position)
    # These are the positions of every foot expressed in global coordinates
    feet_positions: FeetPositions = field(default_factory=FeetPositions)
