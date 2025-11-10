import sys
import time
from spotmicroai.configuration._parameters_provider import ParametersProvider
from spotmicroai.logger import Logger
from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.motion_controller.inverse_kinematics import BodyState, InverseKinematicsSolver
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName
from spotmicroai.runtime.motion_controller.state._idle_state import IdleState
from spotmicroai.runtime.motion_controller.state._stand_state import StandState
from spotmicroai.runtime.motion_controller.state._walk_state import WalkState
from spotmicroai.runtime.motion_controller.state._transition_states import TransitIdleState, TransitStandState
from spotmicroai.runtime.motion_controller.state.command import Command

log = Logger().setup_logger('StateMachine')


class StateMachine:

    def __init__(self):
        self._states: dict[RobotStateName, BaseRobotState] = {
            RobotStateName.IDLE: IdleState(),
            RobotStateName.TRANSIT_IDLE: TransitIdleState(),
            RobotStateName.STAND: StandState(),
            RobotStateName.TRANSIT_STAND: TransitStandState(),
            RobotStateName.WALK: WalkState(),
        }

        self._current_state: RobotStateName = RobotStateName.IDLE
        self._states[self._current_state].enter()

        self._body_state = BodyState()
        self._inverse_kinematics_solver = InverseKinematicsSolver(0, 0.04, 0)
        self._command = Command()

        self._parameters_provider = ParametersProvider()

    @property
    def current_state(self) -> RobotStateName:
        return self._current_state

    def is_idle(self) -> bool:
        return self._current_state == RobotStateName.IDLE

    def get_frame_duration(self) -> float:
        """Get the frame duration for the current state."""
        return self._states[self._current_state].frame_duration

    def update(self) -> None:
        start_time = time.time()
        self._states[self._current_state].update()
        duration = (time.time() - start_time) * 1000
        log.debug(f"StateMachine.update took {duration:.2f}ms")

    def handle_event(self, event: ControllerEvent) -> None:
        start_time = time.time()

        handle_start = time.time()
        next_state = self._states[self._current_state].handle_event(event)
        handle_end = time.time()
        handle_duration = (handle_end - handle_start) * 1000

        # Only log if slow
        if handle_duration > 20:
            print(
                f"  [StateMachine] {self._current_state.value}.handle_event SLOW: {handle_duration:.2f}ms",
                file=sys.stderr,
                flush=True,
            )

        if next_state:
            old_state = self._current_state
            transition_start = time.time()
            self._transition_to(next_state)
            transition_end = time.time()
            transition_duration = (transition_end - transition_start) * 1000
            # Always log transitions
            print(
                f"  [StateMachine] transition {old_state.value} -> {next_state.value} took {transition_duration:.2f}ms",
                file=sys.stderr,
                flush=True,
            )

        total_duration = (time.time() - start_time) * 1000
        # Only log if slow
        if total_duration > 20:
            print(
                f"  [StateMachine] handle_event total: {total_duration:.2f}ms (state: {self._current_state.value})",
                file=sys.stderr,
                flush=True,
            )

    def _transition_to(self, new_state: RobotStateName) -> None:
        if new_state == self._current_state:
            return

        old_state = self._current_state
        # Always log transition start
        print(f"    [Transition] {old_state.value} -> {new_state.value}", file=sys.stderr, flush=True)

        exit_start = time.time()
        self._states[self._current_state].exit()
        exit_duration = (time.time() - exit_start) * 1000
        if exit_duration > 10:
            print(f"      [{old_state.value}] exit() SLOW: {exit_duration:.2f}ms", file=sys.stderr, flush=True)

        self._current_state = new_state

        enter_start = time.time()
        self._states[self._current_state].enter()
        enter_duration = (time.time() - enter_start) * 1000
        if enter_duration > 10:
            print(f"      [{new_state.value}] enter() SLOW: {enter_duration:.2f}ms", file=sys.stderr, flush=True)
