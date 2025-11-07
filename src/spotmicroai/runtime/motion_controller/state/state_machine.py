from spotmicroai.logger import Logger
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotState
from spotmicroai.runtime.motion_controller.state._idle_state import IdleState
from spotmicroai.runtime.motion_controller.state._stand_state import StandState
from spotmicroai.runtime.motion_controller.state._walk_state import WalkState
from spotmicroai.runtime.motion_controller.state._transition_states import TransitIdleState, TransitStandState

log = Logger().setup_logger('StateMachine')


class StateMachine:

    def __init__(self):
        self._states: dict[RobotState, BaseRobotState] = {
            RobotState.IDLE: IdleState(),
            RobotState.TRANSIT_IDLE: TransitIdleState(),
            RobotState.STAND: StandState(),
            RobotState.TRANSIT_STAND: TransitStandState(),
            RobotState.WALK: WalkState(),
        }

        self._current_state: RobotState = RobotState.IDLE
        self._states[self._current_state].enter()

    @property
    def current_state(self) -> RobotState:
        return self._current_state

    def is_idle(self) -> bool:
        return self._current_state == RobotState.IDLE

    def update(self) -> None:
        self._states[self._current_state].update()

    def handle_event(self, event: dict) -> None:
        next_state = self._states[self._current_state].handle_event(event)
        if next_state:
            self._transition_to(next_state)

    def _transition_to(self, new_state: RobotState) -> None:
        if new_state == self._current_state:
            return

        log.debug(f'Transitioning from {self._current_state} to {new_state}')
        self._states[self._current_state].exit()
        self._current_state = new_state
        self._states[self._current_state].enter()
