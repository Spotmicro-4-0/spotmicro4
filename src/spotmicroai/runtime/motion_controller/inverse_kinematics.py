from dataclasses import dataclass, field
from math import atan2, cos, pi, sin, sqrt
import numpy as np

from spotmicroai.configuration import ParametersProvider

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


@dataclass
class InverseKinematicsLeg:
    """
    Solves inverse kinematics for a single leg.
    """

    def __init__(self, is_rear: bool = False, is_left: bool = False):
        self._theta1 = 0.0
        self._theta2 = 0.0
        self._theta3 = 0.0

        self._is_rear = is_rear
        self._is_left = is_left

        _parameters = ParametersProvider()
        self._l1 = _parameters.hip_length
        self._l2 = _parameters.upper_leg_length
        self._l3 = _parameters.lower_leg_length

        self._body_width = _parameters.body_width
        self._body_length = _parameters.body_length

        # Pre-compute and cache leg coordinate transform
        self._leg_transform = self._get_leg_transform()

    def update_angles(self, foot_position: Position, body_transform: np.ndarray):
        """
        Solves inverse kinematics to reach the target foot position in global coordinates.
        Updates angles to achieve the desired position.
        """
        foot_position_leg = self._convert_position_from_body_to_leg(foot_position, body_transform)
        self._solve_joint_angles(foot_position_leg)

    def _convert_position_from_body_to_leg(self, foot_position: Position, body_transform: np.ndarray) -> Position:
        """
        Converts foot position from global to local coordinates.

        Returns:
            Position with (x, y, z) in local coordinates.
        """
        # Compute combined transform from global to local
        global_to_local_transform = body_transform @ self._leg_transform

        # Build homogeneous vector for point
        vector = np.array([[foot_position.x], [foot_position.y], [foot_position.z], [1.0]])

        # Transform global position to local
        global_to_local_inverse_transform = inverse(global_to_local_transform)
        foot_position_local = global_to_local_inverse_transform @ vector

        # Extract coordinates in local
        x = float(foot_position_local[0, 0])
        y = float(foot_position_local[1, 0])
        z = float(foot_position_local[2, 0])

        return Position(x, y, z)

    def _solve_joint_angles(self, foot_position_leg: Position):
        """
        Computes joint angles using inverse kinematics.

        Args:
            foot_position_leg: Target foot position in local coordinates.
        """
        l1, l2, l3 = self._l1, self._l2, self._l3
        x, y, z = foot_position_leg.x, foot_position_leg.y, foot_position_leg.z

        # --- Compute D (law of cosines term)
        d = (x**2 + y**2 + z**2 - l1**2 - l2**2 - l3**2) / (2 * l2 * l3)

        # Clamp D to [-1, 1] for numerical safety
        d = max(min(d, 1.0), -1.0)
        theta3 = atan2(-sqrt(1 - d**2), d)

        # --- Hip pitch angle (ang2)
        protected_sqrt_val = max(x**2 + y**2 - l1**2, 0.0)

        theta2 = atan2(z, sqrt(protected_sqrt_val)) - atan2(l3 * sin(theta3), l2 + l3 * cos(theta3))

        # --- Hip yaw angle (ang1)
        theta1 = atan2(y, x) + atan2(sqrt(protected_sqrt_val), -l1)

        self._theta1 = theta1
        self._theta2 = theta2
        self._theta3 = theta3

    def get_angles(self) -> LegAngles:
        """Returns the current joint angles."""
        return LegAngles(self._theta1, self._theta2, self._theta3)

    def _get_leg_transform(self) -> np.ndarray:
        """
        Computes homogeneous transform from global to local coordinates.
        Infers rotation and translation signs based on is_rear and is_left flags.
        """
        # Y rotation: left legs rotate -pi/2, right legs rotate pi/2
        y_rotation = pi / 2.0 * (-1 if self._is_left else 1)

        # X translation (front/rear): front legs at +length/2, rear legs at -length/2
        x_translation = self._body_length / 2.0 * (-1 if self._is_rear else 1)

        # Z translation (left/right): left legs at -width/2, right legs at +width/2
        z_translation = self._body_width / 2.0 * (-1 if self._is_left else 1)

        transform = rotate_xyz(0.0, y_rotation, 0.0)
        transform[0:3, 3] = np.array([x_translation, 0.0, z_translation])
        return transform


class InverseKinematicsSolver:
    """Solves inverse kinematics for all four legs of the robot."""

    def __init__(self, x: float, y: float, z: float):
        """
        Initialize the IK solver with initial body position.

        Args:
            x: X position of the body.
            y: Y position of the body.
            z: Z position of the body.
        """
        self._x = x
        self._y = y
        self._z = z

        self._omega = 0.0
        self._phi = 0.0
        self._psi = 0.0

        self.feet_positions = FeetPositions()

        self._rear_right_leg = InverseKinematicsLeg(is_rear=True, is_left=False)
        self._front_right_leg = InverseKinematicsLeg(is_rear=False, is_left=False)
        self._front_left_leg = InverseKinematicsLeg(is_rear=False, is_left=True)
        self._rear_left_leg = InverseKinematicsLeg(is_rear=True, is_left=True)

    def _get_body_transform(self) -> np.ndarray:
        """Computes the homogeneous transform for the body position and orientation."""
        return translate_xyz(self._x, self._y, self._z) @ rotate_xyz(self._omega, self._phi, self._psi)

    def _update_leg_angles(self, feet_positions: FeetPositions):
        """Updates the joint angles for each leg."""
        body_transform = self._get_body_transform()

        self._front_left_leg.update_angles(feet_positions.front_left, body_transform)
        self._front_right_leg.update_angles(feet_positions.front_right, body_transform)
        self._rear_left_leg.update_angles(feet_positions.rear_left, body_transform)
        self._rear_right_leg.update_angles(feet_positions.rear_right, body_transform)

    def update(self, body_state: BodyState):
        """
        Updates the solver with new body state and solves for leg angles.

        Args:
            body_state: Desired body state including position, orientation, and feet positions in global coordinates.
        """
        self._x = body_state.body_position.x
        self._y = body_state.body_position.y
        self._z = body_state.body_position.z

        self._omega = body_state.omega
        self._phi = body_state.phi
        self._psi = body_state.psi

        self.feet_positions = body_state.feet_positions
        self._update_leg_angles(body_state.feet_positions)

    def query(self) -> LegAnglesSet:
        """
        Gets the current joint angles for all legs.

        Returns:
            LegAnglesSet containing the joint angles for each leg.
        """
        return LegAnglesSet(
            front_left=self._front_left_leg.get_angles(),
            front_right=self._front_right_leg.get_angles(),
            rear_left=self._rear_left_leg.get_angles(),
            rear_right=self._rear_right_leg.get_angles(),
        )


# ---------------------------------------------------------------------------
# Homogeneous transform helpers
# ---------------------------------------------------------------------------
def _rotate_x(theta: float) -> np.ndarray:
    """Rotation about X-axis."""
    return np.array(
        [
            [1, 0, 0, 0],
            [0, cos(theta), -sin(theta), 0],
            [0, sin(theta), cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _rotate_y(theta: float) -> np.ndarray:
    """Rotation about Y-axis."""
    return np.array(
        [
            [cos(theta), 0, sin(theta), 0],
            [0, 1, 0, 0],
            [-sin(theta), 0, cos(theta), 0],
            [0, 0, 0, 1],
        ]
    )


def _rotate_z(theta: float) -> np.ndarray:
    """Rotation about Z-axis."""
    return np.array(
        [
            [cos(theta), -sin(theta), 0, 0],
            [sin(theta), cos(theta), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1],
        ]
    )


def rotate_xyz(x_ang: float, y_ang: float, z_ang: float) -> np.ndarray:
    """
    Combines rotations about X, Y, and Z axes sequentially.
    Returns a 4x4 homogeneous transformation matrix.

    Each rotation is post-multiplied (applied on the right).
    """
    # Build identity, then apply rotations in order X, Y, Z
    result = np.eye(4)
    result = result @ _rotate_x(x_ang)
    result = result @ _rotate_y(y_ang)
    result = result @ _rotate_z(z_ang)
    return result


def translate_xyz(x: float, y: float, z: float) -> np.ndarray:
    """
    Creates a homogeneous transformation matrix for translation.
    Translates by the given x, y, z offsets.
    """
    return np.array(
        [
            [1, 0, 0, x],
            [0, 1, 0, y],
            [0, 0, 1, z],
            [0, 0, 0, 1],
        ]
    )


def inverse(transform: np.ndarray) -> np.ndarray:
    """
    Computes the inverse of a homogeneous transformation matrix.
    Transposes the rotation matrix and adjusts the translation vector accordingly.
    """
    rotation_matrix = transform[0:3, 0:3]
    translation_vector = transform[0:3, 3]
    inverse_transform = np.eye(4)
    inverse_transform[0:3, 0:3] = rotation_matrix.T
    inverse_transform[0:3, 3] = -rotation_matrix.T @ translation_vector
    return inverse_transform
