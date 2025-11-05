# spot_micro_kinematics.py
import numpy as np

from .models import (
    AllRobotRelativeTransforms,
    BodyState,
    EulerAngles,
    JointAngles,
    LegsFootPositions,
    LegsJointAngles,
    LinkLengths,
    Point,
    SpotmicroConfig,
)
from .spotmicro_leg import SpotmicroLeg
from .utils import (
    homogeneous_rotation_xyz,
    homogeneous_translation_xyz,
    ht_leg_left_back,
    ht_leg_left_front,
    ht_leg_right_back,
    ht_leg_right_front,
)


class SpotmicroKinematics:
    def __init__(self, x: float, y: float, z: float, config: SpotmicroConfig):
        self.x = x
        self.y = y
        self.z = z
        self.config = config

        self.phi = 0.0
        self.theta = 0.0
        self.psi = 0.0

        joint_angles_temp = JointAngles(0.0, 0.0, 0.0)
        link_lengths_temp = LinkLengths(
            config.hip_link_length,
            config.upper_leg_link_length,
            config.lower_leg_link_length,
        )

        # Construct legs with correct is_leg_12 flags
        self.right_back_leg = SpotmicroLeg(joint_angles_temp, link_lengths_temp, True)
        self.right_front_leg = SpotmicroLeg(joint_angles_temp, link_lengths_temp, True)
        self.left_front_leg = SpotmicroLeg(joint_angles_temp, link_lengths_temp, False)
        self.left_back_leg = SpotmicroLeg(joint_angles_temp, link_lengths_temp, False)

    def get_body_ht(self) -> np.ndarray:
        # Euler angle order is phi, psi, theta because the axes of the robot
        # are x pointing forward, y pointing up, z pointing right
        return homogeneous_translation_xyz(self.x, self.y, self.z) @ homogeneous_rotation_xyz(
            self.phi, self.psi, self.theta
        )

    def set_leg_joint_angles(self, four_legs_joint_angs: LegsJointAngles):
        self.right_back_leg.set_angles(four_legs_joint_angs.right_back)
        self.right_front_leg.set_angles(four_legs_joint_angs.right_front)
        self.left_front_leg.set_angles(four_legs_joint_angs.left_front)
        self.left_back_leg.set_angles(four_legs_joint_angs.left_back)

    def set_feet_pos_global_coordinates(self, four_legs_foot_pos: LegsFootPositions):
        ht_body = self.get_body_ht()

        # Compute start transforms for each leg
        ht_rb = ht_body @ ht_leg_right_back(self.config.body_length, self.config.body_width)
        ht_rf = ht_body @ ht_leg_right_front(self.config.body_length, self.config.body_width)
        ht_lf = ht_body @ ht_leg_left_front(self.config.body_length, self.config.body_width)
        ht_lb = ht_body @ ht_leg_left_back(self.config.body_length, self.config.body_width)

        self.right_back_leg.set_foot_pos_global(four_legs_foot_pos.right_back, ht_rb)
        self.right_front_leg.set_foot_pos_global(four_legs_foot_pos.right_front, ht_rf)
        self.left_front_leg.set_foot_pos_global(four_legs_foot_pos.left_front, ht_lf)
        self.left_back_leg.set_foot_pos_global(four_legs_foot_pos.left_back, ht_lb)

    def set_body_angles(self, phi: float, theta: float, psi: float):
        saved_foot_pos = self.get_legs_foot_pos()
        self.phi, self.theta, self.psi = phi, theta, psi
        self.set_feet_pos_global_coordinates(saved_foot_pos)

    def set_body_position(self, x: float, y: float, z: float):
        saved_foot_pos = self.get_legs_foot_pos()
        self.x, self.y, self.z = x, y, z
        self.set_feet_pos_global_coordinates(saved_foot_pos)

    def set_body_state(self, body_state: BodyState):
        self.x = body_state.xyz_positions.x
        self.y = body_state.xyz_positions.y
        self.z = body_state.xyz_positions.z
        self.phi = body_state.euler_angles.phi
        self.theta = body_state.euler_angles.theta
        self.psi = body_state.euler_angles.psi
        self.set_feet_pos_global_coordinates(body_state.leg_feet_positions)

    def get_legs_joint_angles(self) -> LegsJointAngles:
        return LegsJointAngles(
            right_back=self.right_back_leg.joint_angles,
            right_front=self.right_front_leg.joint_angles,
            left_front=self.left_front_leg.joint_angles,
            left_back=self.left_back_leg.joint_angles,
        )

    def get_legs_foot_pos(self) -> LegsFootPositions:
        ht_body = self.get_body_ht()

        ht_rb = ht_body @ ht_leg_right_back(self.config.body_length, self.config.body_width)
        ht_rf = ht_body @ ht_leg_right_front(self.config.body_length, self.config.body_width)
        ht_lf = ht_body @ ht_leg_left_front(self.config.body_length, self.config.body_width)
        ht_lb = ht_body @ ht_leg_left_back(self.config.body_length, self.config.body_width)

        return LegsFootPositions(
            right_back=self.right_back_leg.get_foot_pos_global(ht_rb),
            right_front=self.right_front_leg.get_foot_pos_global(ht_rf),
            left_front=self.left_front_leg.get_foot_pos_global(ht_lf),
            left_back=self.left_back_leg.get_foot_pos_global(ht_lb),
        )

    def get_body_state(self) -> BodyState:
        return BodyState(
            euler_angles=EulerAngles(self.phi, self.theta, self.psi),
            xyz_positions=Point(self.x, self.y, self.z),
            leg_feet_positions=self.get_legs_foot_pos(),
        )

    def get_robot_transforms(self) -> AllRobotRelativeTransforms:
        all_t = AllRobotRelativeTransforms()
        ht_body = self.get_body_ht()

        # Fill body and leg transforms
        all_t.body_center = ht_body
        all_t.center_to_right_back = ht_leg_right_back(self.config.body_length, self.config.body_width)
        all_t.center_to_right_front = ht_leg_right_front(self.config.body_length, self.config.body_width)
        all_t.center_to_left_front = ht_leg_left_front(self.config.body_length, self.config.body_width)
        all_t.center_to_left_back = ht_leg_left_back(self.config.body_length, self.config.body_width)

        all_t.right_back_leg.t01 = self.right_back_leg.get_transform_0_to_1()
        all_t.right_back_leg.t13 = self.right_back_leg.get_transform_1_to_3()
        all_t.right_back_leg.t34 = self.right_back_leg.get_transform_3_to_4()

        all_t.right_front_leg.t01 = self.right_front_leg.get_transform_0_to_1()
        all_t.right_front_leg.t13 = self.right_front_leg.get_transform_1_to_3()
        all_t.right_front_leg.t34 = self.right_front_leg.get_transform_3_to_4()

        all_t.left_front_leg.t01 = self.left_front_leg.get_transform_0_to_1()
        all_t.left_front_leg.t13 = self.left_front_leg.get_transform_1_to_3()
        all_t.left_front_leg.t34 = self.left_front_leg.get_transform_3_to_4()

        all_t.left_back_leg.t01 = self.left_back_leg.get_transform_0_to_1()
        all_t.left_back_leg.t13 = self.left_back_leg.get_transform_1_to_3()
        all_t.left_back_leg.t34 = self.left_back_leg.get_transform_3_to_4()

        return all_t
