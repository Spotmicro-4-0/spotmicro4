import spotmicroai.constants as CONSTANTS
from spotmicroai.motion.command import Command
from spotmicroai.motion.filtering import RateLimitedFirstOrderFilter, XyzFilters
from spotmicroai.motion.models import BodyState
from spotmicroai.motion.state.base_state import BaseState
from spotmicroai.motion.state.transition_idle_state import TransitionIdleState
from spotmicroai.motion.state.walk_state import WalkState
from spotmicroai.runtime.motion_controller.motion_controller import MotionController


class StandState(BaseState):
    """Stand state - robot is standing upright and can adjust body angles."""

    def __init__(self):
        super().__init__()
        self.cmd_state_: BodyState = BodyState()
        self.angle_cmd_filters_: XyzFilters = XyzFilters()

    def handle_input_commands(
        self,
        body_state: BodyState,
        command: Command,
        motion_controller: "MotionController",
        body_state_cmd: BodyState,
    ) -> None:
        """Handle input commands in stand state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
            body_state_cmd: Command body state to modify
        """
        if command.idle_cmd:
            self.change_state(motion_controller, TransitionIdleState())

        elif command.walk_cmd:
            self.change_state(motion_controller, WalkState())

        else:
            # Get command values
            self.cmd_state_.euler_angles.phi = command.phi_cmd
            self.cmd_state_.euler_angles.theta = command.theta_cmd
            self.cmd_state_.euler_angles.psi = command.psi_cmd

            # Set command to filters
            if self.angle_cmd_filters_.x:
                self.angle_cmd_filters_.x.set_command(self.cmd_state_.euler_angles.phi)
            if self.angle_cmd_filters_.y:
                self.angle_cmd_filters_.y.set_command(self.cmd_state_.euler_angles.theta)
            if self.angle_cmd_filters_.z:
                self.angle_cmd_filters_.z.set_command(self.cmd_state_.euler_angles.psi)

            # Run Filters and get command values
            if self.angle_cmd_filters_.x:
                body_state_cmd.euler_angles.phi = self.angle_cmd_filters_.x.run_timestep_and_get_output()
            if self.angle_cmd_filters_.y:
                body_state_cmd.euler_angles.theta = self.angle_cmd_filters_.y.run_timestep_and_get_output()
            if self.angle_cmd_filters_.z:
                body_state_cmd.euler_angles.psi = self.angle_cmd_filters_.z.run_timestep_and_get_output()

            body_state_cmd.xyz_positions = self.cmd_state_.xyz_positions

            body_state_cmd.legs_foot_positions = self.cmd_state_.legs_foot_positions

            # Set and publish command
            motion_controller.set_servo_command_message_data()
            motion_controller.publish_servo_proportional_command()

    def init(self, body_state: BodyState, command: Command, motion_controller: "MotionController") -> None:
        """Initialize stand state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
        """
        # Set default stance
        self.cmd_state_.legs_foot_positions = motion_controller.get_neutral_stance()

        # End body state position and angles
        self.cmd_state_.euler_angles.phi = 0.0
        self.cmd_state_.euler_angles.theta = 0.0
        self.cmd_state_.euler_angles.psi = 0.0

        self.cmd_state_.xyz_positions.x = 0.0
        self.cmd_state_.xyz_positions.y = CONSTANTS.DEFAULT_STAND_HEIGHT
        self.cmd_state_.xyz_positions.z = 0.0

        dt = CONSTANTS.DT
        tau = CONSTANTS.TRANSIT_TAU
        rate_limit = CONSTANTS.TRANSIT_ANGLE_RL

        self.angle_cmd_filters_.x = RateLimitedFirstOrderFilter(dt, tau, self.cmd_state_.euler_angles.phi, rate_limit)
        self.angle_cmd_filters_.y = RateLimitedFirstOrderFilter(dt, tau, self.cmd_state_.euler_angles.theta, rate_limit)
        self.angle_cmd_filters_.z = RateLimitedFirstOrderFilter(dt, tau, self.cmd_state_.euler_angles.psi, rate_limit)

    def get_current_state_name(self) -> str:
        """Return current state name."""
        return "Stand"
