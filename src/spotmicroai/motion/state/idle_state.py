from spotmicroai.motion.command import Command
from spotmicroai.motion.models import BodyState
from spotmicroai.motion.state.base_state import BaseState
from spotmicroai.motion.state.transition_stand_state import TransitionStandState
from spotmicroai.runtime.motion_controller.motion_controller import MotionController


class IdleState(BaseState):
    """Idle state - robot is sitting/lying down."""

    def handle_input_commands(
        self,
        body_state: BodyState,
        command: Command,
        motion_controller: "MotionController",
        body_state_cmd: BodyState,
    ) -> None:
        """Handle input commands in idle state.

        Args:
            body_state: Current body state
            smnc: Configuration parameters
            cmd: Input command
            smmc: Motion command controller
            body_state_cmd: Command body state to modify
        """
        # Check if stand command issued, if so, transition to stand state
        if command.stand_cmd:
            self.change_state(motion_controller, TransitionStandState())
        else:
            # Otherwise, just command idle servo commands
            motion_controller.publish_zero_servo_absolute_command()

    def init(self, body_state: BodyState, command: Command, motion_controller: "MotionController") -> None:
        """Initialize idle state."""

    def get_current_state_name(self) -> str:
        """Return current state name."""
        return "Idle"
