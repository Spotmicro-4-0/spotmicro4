from dataclasses import dataclass
from math import atan2, cos, pi, sin, sqrt
import numpy as np

from spotmicroai.configuration import ParametersProvider
from spotmicroai.motion.models import (
    BodyState,
    JointAngles,
    LegsFootPositions,
    LegsJointAngles,
    Point,
)

@dataclass
class InverseKinematicsLeg:
    """
    Produces identical joint angles and transforms, including is_leg_12 symmetry.
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
        self._leg_ht = self._compute_leg_ht()

    def solve_inverse_kinematics_body(self, foot_position_body: Point, body_ht: np.ndarray):
        """
        Solves inverse kinematics to reach the target foot position in body frame.
        Updates joint angles to achieve the desired foot position.
        """
        foot_position_leg = self._convert_body_to_leg_position(foot_position_body, body_ht)
        self._solve_joint_angles(foot_position_leg)

    def _convert_body_to_leg_position(self, foot_position_body: Point, body_ht: np.ndarray) -> Point:
        """
        Converts foot position from body frame to leg frame.

        Returns:
            Point with (x, y, z) coordinates in leg frame.
        """
        # Compute combined transform from body to leg frame
        body_to_leg_ht = body_ht @ self._leg_ht

        # Build homogeneous vector for point
        foot_vector = np.array([[foot_position_body.x], [foot_position_body.y], [foot_position_body.z], [1.0]])

        # Transform body-frame position to leg frame
        body_to_leg_inverse_ht = inverse(body_to_leg_ht)
        foot_position_leg = body_to_leg_inverse_ht @ foot_vector

        # Extract coordinates in leg frame
        x = float(foot_position_leg[0, 0])
        y = float(foot_position_leg[1, 0])
        z = float(foot_position_leg[2, 0])

        return Point(x, y, z)

    def _solve_joint_angles(self, foot_position_leg: Point):
        """
        Compute joint angles using inverse kinematics.

        Args:
            foot_position_leg: Target foot position in leg frame coordinates.
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

    # -----------------------------------------------------------------------
    # Forward Kinematics
    # -----------------------------------------------------------------------
    def get_foot_position_body(self, body_ht: np.ndarray) -> Point:
        """
        Computes foot position in body frame coordinates using forward kinematics.
        """
        # Compute combined transform from body to leg frame
        body_to_leg_ht = body_ht @ self._leg_ht

        leg_to_foot_ht = (
            self.get_transform_0_to_1()
            @ self.get_transform_1_to_3()
            @ self.get_transform_3_to_4()
        )
        ht_body_to_foot = body_to_leg_ht @ leg_to_foot_ht

        # Foot position is last column (translation)
        x = ht_body_to_foot[0, 3]
        y = ht_body_to_foot[1, 3]
        z = ht_body_to_foot[2, 3]

        return Point(float(x), float(y), float(z))

    # -----------------------------------------------------------------------
    # Partial Transform Accessors
    # -----------------------------------------------------------------------
    def get_transform_0_to_1(self) -> np.ndarray:
        """Returns the homogeneous transform from joint 0 to joint 1."""
        transform = rotate_xyz(0.0, 0.0, self._theta1)
        transform[0, 3] = -self._l1 * np.cos(self._theta1)
        transform[1, 3] = -self._l1 * np.sin(self._theta1)
        return transform

    def get_transform_1_to_3(self) -> np.ndarray:
        """
        Returns the combined transform from joint 1 to joint 3 (joint1_to_2 * joint2_to_3).
        """
        ht_1_to_2 = np.array([
            [ 0.0,  0.0, -1.0,  0.0],
            [-1.0,  0.0,  0.0,  0.0],
            [ 0.0,  1.0,  0.0,  0.0],
            [ 0.0,  0.0,  0.0,  1.0]
        ])

        transform = rotate_xyz(0.0, 0.0, self._theta2)
        transform[0, 3] = self._l2 * np.cos(self._theta2)
        transform[1, 3] = self._l2 * np.sin(self._theta2)

        return ht_1_to_2 @ transform

    def get_transform_3_to_4(self) -> np.ndarray:
        """Returns the homogeneous transform from joint 3 to joint 4 (foot)."""
        transform = rotate_xyz(0.0, 0.0, self._theta3)
        transform[0, 3] = self._l3 * np.cos(self._theta3)
        transform[1, 3] = self._l3 * np.sin(self._theta3)
        return transform

    def set_angles(self, theta1: float, theta2: float, theta3: float):
        """Set the joint angles of the leg."""
        self._theta1 = theta1
        self._theta2 = theta2
        self._theta3 = theta3

    def get_joint_angles(self) -> JointAngles:
        """Returns the current joint angles as a JointAngles object."""
        return JointAngles(self._theta1, self._theta2, self._theta3)

    def _compute_leg_ht(self) -> np.ndarray:
        """
        Compute homogeneous transform from body center to this leg's frame.
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
    def __init__(self, x: float, y: float, z: float):
        self._x = x
        self._y = y
        self._z = z

        self._phi = 0.0
        self._theta = 0.0
        self._psi = 0.0

        # Construct legs with correct is_leg_12 flags
        self._rear_right_leg = InverseKinematicsLeg(is_rear=True, is_left=False)
        self._front_right_leg = InverseKinematicsLeg(is_rear=False, is_left=False)
        self._front_left_leg = InverseKinematicsLeg(is_rear=False, is_left=True)
        self._rear_left_leg = InverseKinematicsLeg(is_rear=True, is_left=True)

    def _get_body_ht(self) -> np.ndarray:
        # Euler angle order is phi, psi, theta because the axes of the robot
        # are x pointing forward, y pointing up, z pointing right
        return translate_xyz(self._x, self._y, self._z) @ rotate_xyz(
            self._phi, self._psi, self._theta
        )

    def _set_feet_pos_body_coordinates(self, four_legs_foot_pos: LegsFootPositions):
        body_ht = self._get_body_ht()

        self._rear_right_leg.solve_inverse_kinematics_body(four_legs_foot_pos.right_back, body_ht)
        self._front_right_leg.solve_inverse_kinematics_body(four_legs_foot_pos.right_front, body_ht)
        self._front_left_leg.solve_inverse_kinematics_body(four_legs_foot_pos.left_front, body_ht)
        self._rear_left_leg.solve_inverse_kinematics_body(four_legs_foot_pos.left_back, body_ht)

    def update(self, body_state: BodyState):
        self._x = body_state.xyz_positions.x
        self._y = body_state.xyz_positions.y
        self._z = body_state.xyz_positions.z
        self._phi = body_state.euler_angles.phi
        self._theta = body_state.euler_angles.theta
        self._psi = body_state.euler_angles.psi
        self._set_feet_pos_body_coordinates(body_state.legs_foot_positions)

    def query(self) -> LegsJointAngles:
        return LegsJointAngles(
            rear_right=self._rear_right_leg.get_joint_angles(),
            front_right=self._front_right_leg.get_joint_angles(),
            front_left=self._front_left_leg.get_joint_angles(),
            rear_left=self._rear_left_leg.get_joint_angles(),
        )

    def get_legs_foot_pos(self) -> LegsFootPositions:
        body_ht = self._get_body_ht()

        return LegsFootPositions(
            right_back=self._rear_right_leg.get_foot_position_body(body_ht),
            right_front=self._front_right_leg.get_foot_position_body(body_ht),
            left_front=self._front_left_leg.get_foot_position_body(body_ht),
            left_back=self._rear_left_leg.get_foot_position_body(body_ht),
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
