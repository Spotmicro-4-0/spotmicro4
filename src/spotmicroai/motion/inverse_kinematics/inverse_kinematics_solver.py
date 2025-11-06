from dataclasses import dataclass
from math import atan2, cos, pi, sin, sqrt
import numpy as np

from spotmicroai.configuration import ParametersProvider
from spotmicroai.motion.models import (
    AllRobotRelativeTransforms,
    BodyState,
    EulerAngles,
    JointAngles,
    LegsFootPositions,
    LegsJointAngles,
    Point,
)

from .homogeneous_transformations import (
    inverse,
    rotate_xyz,
    translate_xyz,
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

        parameters = ParametersProvider()
        self._l1 = parameters.hip_length
        self._l2 = parameters.upper_leg_length
        self._l3 = parameters.lower_leg_length

        self._body_width = parameters.body_width
        self._body_length = parameters.body_length

        # Pre-compute and cache leg coordinate transform
        self._leg_ht = self._compute_leg_ht()

    def set_foot_pos_global(self, foot_position_global: Point, ht_body: np.ndarray):
        """
        Transforms global foot position into the local leg frame and updates the angles.
        """
        # Compute combined transform from body to leg frame
        ht_body_to_leg = ht_body @ self._leg_ht

        # Build homogeneous vector for point
        foot_vector = np.array([[foot_position_global.x], [foot_position_global.y], [foot_position_global.z], [1.0]])

        # Transform global position to leg-local frame
        leg_inverse_ht = inverse(ht_body_to_leg)
        p4_ht_vec_leg = leg_inverse_ht @ foot_vector

        # Extract coordinates in leg frame
        x4 = float(p4_ht_vec_leg[0, 0])
        y4 = float(p4_ht_vec_leg[1, 0])
        z4 = float(p4_ht_vec_leg[2, 0])

        # Compute inverse kinematics
        self._solve_joint_angles(x4, y4, z4)

    def _solve_joint_angles(self, x4: float, y4: float, z4: float):
        """
        Compute joint angles using inverse kinematics.

        Args:
            x4, y4, z4: Target foot position in leg frame coordinates.
        """
        l1, l2, l3 = self._l1, self._l2, self._l3

        # --- Compute D (law of cosines term)
        d = (x4**2 + y4**2 + z4**2 - l1**2 - l2**2 - l3**2) / (2 * l2 * l3)

        # Clamp D to [-1, 1] for numerical safety
        d = max(min(d, 1.0), -1.0)
        theta3 = atan2(-sqrt(1 - d**2), d)

        # --- Hip pitch angle (ang2)
        protected_sqrt_val = max(x4**2 + y4**2 - l1**2, 0.0)

        theta2 = atan2(z4, sqrt(protected_sqrt_val)) - atan2(l3 * sin(theta3), l2 + l3 * cos(theta3))

        # --- Hip yaw angle (ang1)
        theta1 = atan2(y4, x4) + atan2(sqrt(protected_sqrt_val), -l1)

        self._theta1 = theta1
        self._theta2 = theta2
        self._theta3 = theta3

    # -----------------------------------------------------------------------
    # Forward Kinematics
    # -----------------------------------------------------------------------
    def get_foot_pos_global(self, ht_body: np.ndarray) -> Point:
        """
        Computes foot position in global coordinates using forward kinematics.
        """
        # Compute combined transform from body to leg frame
        ht_body_to_leg = ht_body @ self._leg_ht

        ht_leg_to_foot = (
            self.get_transform_0_to_1()
            @ self.get_transform_1_to_3()
            @ self.get_transform_3_to_4()
        )
        ht_body_to_foot = ht_body_to_leg @ ht_leg_to_foot

        # Foot position is last column (translation)
        x = ht_body_to_foot[0, 3]
        y = ht_body_to_foot[1, 3]
        z = ht_body_to_foot[2, 3]

        return Point(float(x), float(y), float(z))

    # -----------------------------------------------------------------------
    # Partial Transform Accessors (debugging)
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

        parameters = ParametersProvider()
        self._hip_length = parameters.hip_length
        self._upper_leg_length = parameters.upper_leg_length
        self._lower_leg_length = parameters.lower_leg_length
        self._body_width = parameters.body_width
        self._body_length = parameters.body_length

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

    def _set_leg_joint_angles(self, four_legs_joint_angs: LegsJointAngles):
        self._rear_right_leg.set_angles(
            four_legs_joint_angs.right_back.theta1,
            four_legs_joint_angs.right_back.theta2,
            four_legs_joint_angs.right_back.theta3,
        )
        self._front_right_leg.set_angles(
            four_legs_joint_angs.right_front.theta1,
            four_legs_joint_angs.right_front.theta2,
            four_legs_joint_angs.right_front.theta3,
        )
        self._front_left_leg.set_angles(
            four_legs_joint_angs.left_front.theta1,
            four_legs_joint_angs.left_front.theta2,
            four_legs_joint_angs.left_front.theta3,
        )
        self._rear_left_leg.set_angles(
            four_legs_joint_angs.left_back.theta1,
            four_legs_joint_angs.left_back.theta2,
            four_legs_joint_angs.left_back.theta3,
        )

    def _set_feet_pos_global_coordinates(self, four_legs_foot_pos: LegsFootPositions):
        ht_body = self._get_body_ht()

        self._rear_right_leg.set_foot_pos_global(four_legs_foot_pos.right_back, ht_body)
        self._front_right_leg.set_foot_pos_global(four_legs_foot_pos.right_front, ht_body)
        self._front_left_leg.set_foot_pos_global(four_legs_foot_pos.left_front, ht_body)
        self._rear_left_leg.set_foot_pos_global(four_legs_foot_pos.left_back, ht_body)

    def set_body_angles(self, phi: float, theta: float, psi: float):
        saved_foot_pos = self.get_legs_foot_pos()
        self._phi, self._theta, self._psi = phi, theta, psi
        self._set_feet_pos_global_coordinates(saved_foot_pos)

    def set_body_position(self, x: float, y: float, z: float):
        saved_foot_pos = self.get_legs_foot_pos()
        self._x, self._y, self._z = x, y, z
        self._set_feet_pos_global_coordinates(saved_foot_pos)

    def set_body_state(self, body_state: BodyState):
        self._x = body_state.xyz_positions.x
        self._y = body_state.xyz_positions.y
        self._z = body_state.xyz_positions.z
        self._phi = body_state.euler_angles.phi
        self._theta = body_state.euler_angles.theta
        self._psi = body_state.euler_angles.psi
        self._set_feet_pos_global_coordinates(body_state.leg_feet_positions)

    def get_legs_joint_angles(self) -> LegsJointAngles:
        return LegsJointAngles(
            right_back=JointAngles(
                self._rear_right_leg._theta1, self._rear_right_leg._theta2, self._rear_right_leg._theta3
            ),
            right_front=JointAngles(
                self._front_right_leg._theta1, self._front_right_leg._theta2, self._front_right_leg._theta3
            ),
            left_front=JointAngles(
                self._front_left_leg._theta1, self._front_left_leg._theta2, self._front_left_leg._theta3
            ),
            left_back=JointAngles(
                self._rear_left_leg._theta1, self._rear_left_leg._theta2, self._rear_left_leg._theta3
            ),
        )

    def get_legs_foot_pos(self) -> LegsFootPositions:
        ht_body = self._get_body_ht()

        return LegsFootPositions(
            right_back=self._rear_right_leg.get_foot_pos_global(ht_body),
            right_front=self._front_right_leg.get_foot_pos_global(ht_body),
            left_front=self._front_left_leg.get_foot_pos_global(ht_body),
            left_back=self._rear_left_leg.get_foot_pos_global(ht_body),
        )

    def get_body_state(self) -> BodyState:
        euler_angles = EulerAngles()
        euler_angles.phi = self._phi
        euler_angles.theta = self._theta
        euler_angles.psi = self._psi

        return BodyState(
            euler_angles=euler_angles,
            xyz_positions=Point(self._x, self._y, self._z),
            leg_feet_positions=self.get_legs_foot_pos(),
        )

    def get_robot_transforms(self) -> AllRobotRelativeTransforms:
        all_t = AllRobotRelativeTransforms()
        ht_body = self._get_body_ht()

        # Fill body and leg transforms
        all_t.body_center = ht_body
        all_t.center_to_right_back = self._rear_right_leg._leg_ht
        all_t.center_to_right_front = self._front_right_leg._leg_ht
        all_t.center_to_left_front = self._front_left_leg._leg_ht
        all_t.center_to_left_back = self._rear_left_leg._leg_ht

        all_t.right_back_leg.t01 = self._rear_right_leg.get_transform_0_to_1()
        all_t.right_back_leg.t13 = self._rear_right_leg.get_transform_1_to_3()
        all_t.right_back_leg.t34 = self._rear_right_leg.get_transform_3_to_4()

        all_t.right_front_leg.t01 = self._front_right_leg.get_transform_0_to_1()
        all_t.right_front_leg.t13 = self._front_right_leg.get_transform_1_to_3()
        all_t.right_front_leg.t34 = self._front_right_leg.get_transform_3_to_4()

        all_t.left_front_leg.t01 = self._front_left_leg.get_transform_0_to_1()
        all_t.left_front_leg.t13 = self._front_left_leg.get_transform_1_to_3()
        all_t.left_front_leg.t34 = self._front_left_leg.get_transform_3_to_4()

        all_t.left_back_leg.t01 = self._rear_left_leg.get_transform_0_to_1()
        all_t.left_back_leg.t13 = self._rear_left_leg.get_transform_1_to_3()
        all_t.left_back_leg.t34 = self._rear_left_leg.get_transform_3_to_4()

        return all_t
