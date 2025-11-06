import spotmicroai.constants as CONSTANTS
from spotmicroai.motion.command import Command
from spotmicroai.motion.filtering import BodyStateFilters
from spotmicroai.motion.models import BodyState
from spotmicroai.motion.state.base_state import BaseState
from spotmicroai.motion.state.idle_state import IdleState
from spotmicroai.runtime.motion_controller.motion_controller import MotionController


class TransitionIdleState(BaseState):
    """Transition from standing to idle/lying down position."""

    def __init__(self):
        super().__init__()
        # Initialize BodyState objects with default values
        self.start_body_state_: BodyState = BodyState()
        self.end_body_state_: BodyState = BodyState()
        self.body_state_filters_: BodyStateFilters = BodyStateFilters()

    def handle_input_commands(
        self,
        body_state: BodyState,
        command: Command,
        motion_controller: "MotionController",
        body_state_cmd: BodyState,
    ) -> None:
        """Handle input commands during transition to idle.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
            body_state_cmd: Command body state to modify
        """
        # Check if desired end state reached, if so, change to idle state
        if self.check_body_state_equality(body_state, self.end_body_state_, 0.001):
            self.change_state(motion_controller, IdleState())

        else:
            # Otherwise, run filters and assign output values to body state command
            self.run_filters(self.body_state_filters_)

            # Assign filter values to cmd
            self.assign_filter_values_to_body_state(self.body_state_filters_, body_state_cmd)

            # Send command
            motion_controller.set_servo_command_message_data()
            motion_controller.publish_servo_proportional_command()

    def init(self, body_state: BodyState, command: Command, motion_controller: "MotionController") -> None:
        """Initialize transition to idle state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
        """
        # Set initial state and end state
        # Get starting body state
        self.start_body_state_ = body_state

        # Create end state
        # Create end state feet positions, a lie down stance
        self.end_body_state_.legs_foot_positions = motion_controller.get_lie_down_stance()

        # End body state position and angles
        self.end_body_state_.euler_angles.phi = 0.0
        self.end_body_state_.euler_angles.theta = 0.0
        self.end_body_state_.euler_angles.psi = 0.0

        self.end_body_state_.xyz_positions.x = 0.0
        self.end_body_state_.xyz_positions.y = CONSTANTS.LIE_DOWN_HEIGHT
        self.end_body_state_.xyz_positions.z = 0.0

        # Initialize filters
        dt = CONSTANTS.DT
        tau = CONSTANTS.TRANSIT_TAU
        rl = CONSTANTS.TRANSIT_RL
        rl_ang = CONSTANTS.TRANSIT_ANGLE_RL

        self.init_body_state_filters(dt, tau, rl, rl_ang, body_state, self.body_state_filters_)

        # Set destination commands for all filters
        self.set_body_state_filter_commands(self.end_body_state_, self.body_state_filters_)

    def get_current_state_name(self) -> str:
        """Return current state name."""
        return "Transit Idle"
