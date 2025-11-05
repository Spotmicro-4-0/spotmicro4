from typing import TYPE_CHECKING

import numpy as np

from ..inverse_kinematics.models._body_state import BodyState
from ..inverse_kinematics.models._euler_angles import EulerAngles
from ..inverse_kinematics.models._legs_foot_positions import LegsFootPositions
from ..inverse_kinematics.models._point import Point
from .base_state import SpotMicroState
from .command import Command

if TYPE_CHECKING:
    from .spot_micro_motion_cmd import SpotMicroMotionCmd, SpotMicroNodeConfig


class ContactFeet:
    """Tracks which feet are in swing phase."""

    def __init__(self):
        self.right_back_in_swing: bool = False
        self.right_front_in_swing: bool = False
        self.left_front_in_swing: bool = False
        self.left_back_in_swing: bool = False


class WalkState(SpotMicroState):
    """Walk state - robot is walking with gait control."""

    def __init__(self):
        super().__init__()
        self.contact_feet_states_: ContactFeet = ContactFeet()
        self.ticks_: int = 0
        self.phase_index_: int = 0
        self.subphase_ticks_: int = 0
        self.smnc_: "SpotMicroNodeConfig | None" = None
        self.cmd_state_: BodyState = BodyState(
            euler_angles=EulerAngles(phi=0.0, theta=0.0, psi=0.0),
            xyz_positions=Point(x=0.0, y=0.0, z=0.0),
            leg_feet_positions=LegsFootPositions(
                right_back=Point(x=0.0, y=0.0, z=0.0),
                right_front=Point(x=0.0, y=0.0, z=0.0),
                left_front=Point(x=0.0, y=0.0, z=0.0),
                left_back=Point(x=0.0, y=0.0, z=0.0),
            ),
        )

    def handle_input_commands(
        self,
        body_state: BodyState,
        smnc: "SpotMicroNodeConfig",
        cmd: Command,
        smmc: "SpotMicroMotionCmd",
        body_state_cmd: BodyState,
    ) -> None:
        """Handle input commands in walk state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
            body_state_cmd: Command body state to modify
        """
        # Debug output
        if smnc.debug_mode:
            print("In Spot Micro Walk State")

        # If stand command received, change to transition to stand state
        if cmd.stand_cmd:
            # Call parent class's change state method
            from .transition_stand_state import TransitionStandState

            self.change_state(smmc, TransitionStandState())

        else:
            # Update gait phasing data
            self.update_phase_data()

            # Step the gait controller
            body_state_cmd.leg_feet_positions = self.step_gait(body_state, cmd, smnc, smmc.get_neutral_stance())

            if smnc.num_phases == 8:
                # Step body shift controller, only for 8 phase gait
                body_state_cmd.xyz_positions = self.step_body_shift(body_state, cmd, smnc)

            # Set servo data and publish command
            smmc.set_servo_command_message_data()
            smmc.publish_servo_proportional_command()

            # Increment ticks
            self.ticks_ += 1

    def init(
        self, body_state: BodyState, smnc: "SpotMicroNodeConfig", cmd: Command, smmc: "SpotMicroMotionCmd"
    ) -> None:
        """Initialize walk state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
        """
        # Save off config struct for convenience
        self.smnc_ = smnc

        # Set default stance
        self.cmd_state_.leg_feet_positions = smmc.get_neutral_stance()

        # End body state position and angles
        self.cmd_state_.euler_angles.phi = 0.0
        self.cmd_state_.euler_angles.theta = 0.0
        self.cmd_state_.euler_angles.psi = 0.0

        self.cmd_state_.xyz_positions.x = 0.0
        self.cmd_state_.xyz_positions.y = smnc.default_stand_height
        self.cmd_state_.xyz_positions.z = 0.0

    def update_phase_data(self) -> None:
        """Update phase index, subphase ticks, and contact feet states."""
        phase_time = self.ticks_ % self.smnc_.phase_length
        phase_sum = 0

        # Update phase index and subphase ticks
        for i in range(self.smnc_.num_phases):
            phase_sum += self.smnc_.phase_ticks[i]
            if phase_time < phase_sum:
                self.phase_index_ = i
                self.subphase_ticks_ = phase_time - phase_sum + self.smnc_.phase_ticks[i]
                break

        # Update contact feet states
        if self.smnc_.rb_contact_phases[self.phase_index_] == 0:
            self.contact_feet_states_.right_back_in_swing = True
        else:
            self.contact_feet_states_.right_back_in_swing = False

        if self.smnc_.rf_contact_phases[self.phase_index_] == 0:
            self.contact_feet_states_.right_front_in_swing = True
        else:
            self.contact_feet_states_.right_front_in_swing = False

        if self.smnc_.lf_contact_phases[self.phase_index_] == 0:
            self.contact_feet_states_.left_front_in_swing = True
        else:
            self.contact_feet_states_.left_front_in_swing = False

        if self.smnc_.lb_contact_phases[self.phase_index_] == 0:
            self.contact_feet_states_.left_back_in_swing = True
        else:
            self.contact_feet_states_.left_back_in_swing = False

    def step_gait(
        self,
        body_state: BodyState,
        cmd: Command,
        smnc: "SpotMicroNodeConfig",
        default_stance_feet_pos: LegsFootPositions,
    ) -> LegsFootPositions:
        """Step the gait controller one timestep.

        Args:
            body_state: Current body state
            cmd: Input command
            smnc: Configuration parameters
            default_stance_feet_pos: Default neutral stance positions

        Returns:
            New feet positions
        """
        new_feet_pos = LegsFootPositions(
            right_back=Point(x=0.0, y=0.0, z=0.0),
            right_front=Point(x=0.0, y=0.0, z=0.0),
            left_front=Point(x=0.0, y=0.0, z=0.0),
            left_back=Point(x=0.0, y=0.0, z=0.0),
        )

        for i in range(4):
            if i == 0:  # right back
                contact_mode = self.contact_feet_states_.right_back_in_swing
                foot_pos = body_state.leg_feet_positions.right_back
                default_stance_foot_pos = default_stance_feet_pos.right_back

            elif i == 1:  # right front
                contact_mode = self.contact_feet_states_.right_front_in_swing
                foot_pos = body_state.leg_feet_positions.right_front
                default_stance_foot_pos = default_stance_feet_pos.right_front

            elif i == 2:  # left front
                contact_mode = self.contact_feet_states_.left_front_in_swing
                foot_pos = body_state.leg_feet_positions.left_front
                default_stance_foot_pos = default_stance_feet_pos.left_front

            else:  # left back
                contact_mode = self.contact_feet_states_.left_back_in_swing
                foot_pos = body_state.leg_feet_positions.left_back
                default_stance_foot_pos = default_stance_feet_pos.left_back

            if not contact_mode:  # Stance controller
                foot_pos = self.stance_controller(foot_pos, cmd, smnc)

            else:  # swing leg controller
                swing_proportion = float(self.subphase_ticks_) / float(smnc.swing_ticks)
                foot_pos = self.swing_leg_controller(foot_pos, cmd, smnc, swing_proportion, default_stance_foot_pos)

            if i == 0:  # right back
                new_feet_pos.right_back = foot_pos

            elif i == 1:  # right front
                new_feet_pos.right_front = foot_pos

            elif i == 2:  # left front
                new_feet_pos.left_front = foot_pos

            else:  # left back
                new_feet_pos.left_back = foot_pos

        # Return new feet positions
        return new_feet_pos

    def stance_controller(self, foot_pos: Point, cmd: Command, smnc: "SpotMicroNodeConfig") -> Point:
        """Returns new foot position incremented by stance controller.

        Args:
            foot_pos: Current foot position
            cmd: Input command
            smnc: Configuration parameters

        Returns:
            New foot position
        """
        # Declare return value
        new_foot_pos = Point(x=0.0, y=0.0, z=0.0)

        # Convenience variables
        dt = smnc.dt
        h_tau = smnc.foot_height_time_constant

        # Calculate position deltas due to speed and rotation commands
        # Create vector to hold current foot position
        foot_pos_vec = np.array([foot_pos.x, foot_pos.y, foot_pos.z])

        # Create delta position vector, which is the commanded velocity times the
        # timestep. Note that y speed command is really sideways velocity command, which
        # is in the z direction of robot coordinate system. Stance foot position hard
        # coded to 0 height here in second equation
        delta_pos = np.array([-cmd.x_speed_cmd * dt, (1.0 / h_tau) * (0.0 - foot_pos.y) * dt, -cmd.y_speed_cmd * dt])

        # Create rotation matrix for yaw rate
        theta = cmd.yaw_rate_cmd * dt
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        rot_delta = np.array([[cos_theta, 0, sin_theta], [0, 1, 0], [-sin_theta, 0, cos_theta]])

        # Move foot by rotation and linear translation deltas
        new_foot_pos_vec = (rot_delta @ foot_pos_vec) + delta_pos

        # Assign values to return structure
        new_foot_pos.x = new_foot_pos_vec[0]
        new_foot_pos.y = new_foot_pos_vec[1]
        new_foot_pos.z = new_foot_pos_vec[2]

        # Return value
        return new_foot_pos

    def swing_leg_controller(
        self,
        foot_pos: Point,
        cmd: Command,
        smnc: "SpotMicroNodeConfig",
        swing_proportion: float,
        default_stance_foot_pos: Point,
    ) -> Point:
        """Returns new foot position incremented by swing leg controller.

        Args:
            foot_pos: Current foot position
            cmd: Input command
            smnc: Configuration parameters
            swing_proportion: Proportion of swing phase completed (0.0 to 1.0)
            default_stance_foot_pos: Default stance position for this foot

        Returns:
            New foot position
        """
        # declare return value
        new_foot_pos = Point(x=0.0, y=0.0, z=0.0)

        # Convenience variables
        dt = smnc.dt
        alpha = smnc.alpha
        beta = smnc.beta
        stance_ticks = smnc.stance_ticks
        default_stance_foot_pos_vec = np.array(
            [default_stance_foot_pos.x, default_stance_foot_pos.y, default_stance_foot_pos.z]
        )

        # Calculate swing height based on triangular profile
        if swing_proportion < 0.5:
            swing_height = swing_proportion / 0.5 * smnc.z_clearance
        else:
            swing_height = smnc.z_clearance * (1.0 - (swing_proportion - 0.5) / 0.5)

        # Calculate position deltas due to speed and rotation commands
        # Create vector to hold current foot position
        foot_pos_vec = np.array([foot_pos.x, foot_pos.y, foot_pos.z])

        # Create delta position vector for touchdown location
        delta_pos = np.array(
            [alpha * stance_ticks * dt * cmd.x_speed_cmd, 0.0, alpha * stance_ticks * dt * cmd.y_speed_cmd]
        )

        # Create rotation matrix for yaw rate
        theta = beta * stance_ticks * dt * -cmd.yaw_rate_cmd
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        rot_delta = np.array([[cos_theta, 0, sin_theta], [0, 1, 0], [-sin_theta, 0, cos_theta]])

        # Calculate touchdown location
        touchdown_location = (rot_delta @ default_stance_foot_pos_vec) + delta_pos

        time_left = dt * smnc.swing_ticks * (1.0 - swing_proportion)

        delta_pos2 = ((touchdown_location - foot_pos_vec) / time_left) * dt

        new_foot_pos_vec = foot_pos_vec + delta_pos2
        new_foot_pos_vec[1] = swing_height

        # Assign values to return structure
        new_foot_pos.x = new_foot_pos_vec[0]
        new_foot_pos.y = new_foot_pos_vec[1]
        new_foot_pos.z = new_foot_pos_vec[2]

        # Return value
        return new_foot_pos

    def step_body_shift(self, body_state: BodyState, cmd: Command, smnc: "SpotMicroNodeConfig") -> Point:
        """Steps the body shift controller for balance during gait cycle.

        Args:
            body_state: Current body state
            cmd: Input command
            smnc: Configuration parameters

        Returns:
            New body position
        """
        # Convenience variables
        dt = smnc.dt

        shift_phase = smnc.body_shift_phases[self.phase_index_]
        shift_proportion = float(self.subphase_ticks_) / float(smnc.swing_ticks)
        time_left = dt * smnc.swing_ticks * (1.0 - shift_proportion)

        return_point = Point(x=0.0, y=smnc.default_stand_height, z=0.0)

        if shift_phase == 2:  # Hold front left shift pos
            return_point.x = smnc.fwd_body_balance_shift
            return_point.z = -smnc.side_body_balance_shift

        elif shift_phase == 4:  # Hold back left shift pos
            return_point.x = -smnc.back_body_balance_shift
            return_point.z = -smnc.side_body_balance_shift

        elif shift_phase == 6:  # Hold front right shift pos
            return_point.x = smnc.fwd_body_balance_shift
            return_point.z = smnc.side_body_balance_shift

        elif shift_phase == 8:  # Hold back right shift pos
            return_point.x = -smnc.back_body_balance_shift
            return_point.z = smnc.side_body_balance_shift

        else:
            # Shift body to front left
            if shift_phase == 1:
                end_x_pos = smnc.fwd_body_balance_shift
                end_z_pos = -smnc.side_body_balance_shift

            # Shift body to back left
            elif shift_phase == 3:
                end_x_pos = -smnc.back_body_balance_shift
                end_z_pos = -smnc.side_body_balance_shift

            # Shift body to front right
            elif shift_phase == 5:
                end_x_pos = smnc.fwd_body_balance_shift
                end_z_pos = smnc.side_body_balance_shift

            # Shift body to back right
            else:
                end_x_pos = -smnc.back_body_balance_shift
                end_z_pos = smnc.side_body_balance_shift

            delta_x = ((end_x_pos - body_state.xyz_positions.x) / time_left) * dt
            delta_z = ((end_z_pos - body_state.xyz_positions.z) / time_left) * dt

            return_point.x = body_state.xyz_positions.x + delta_x
            return_point.z = body_state.xyz_positions.z + delta_z

        return return_point

    def get_current_state_name(self) -> str:
        """Return current state name."""
        return "Walk"
