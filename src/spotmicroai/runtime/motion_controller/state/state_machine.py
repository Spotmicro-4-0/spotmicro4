from spotmicroai.logger import Logger
from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName
from spotmicroai.runtime.motion_controller.state._idle_state import IdleState
from spotmicroai.runtime.motion_controller.state._stand_state import StandState
from spotmicroai.runtime.motion_controller.state._walk_state import WalkState
from spotmicroai.runtime.motion_controller.state._transition_states import TransitIdleState, TransitStandState

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

    @property
    def current_state(self) -> RobotStateName:
        return self._current_state

    def is_idle(self) -> bool:
        return self._current_state == RobotStateName.IDLE

    def update(self) -> None:
        self._states[self._current_state].update()

    def handle_event(self, event: ControllerEvent) -> None:
        next_state = self._states[self._current_state].handle_event(event)
        if next_state:
            self._transition_to(next_state)

    def _transition_to(self, new_state: RobotStateName) -> None:
        if new_state == self._current_state:
            return

        log.debug(f'Transitioning from {self._current_state} to {new_state}')
        self._states[self._current_state].exit()
        self._current_state = new_state
        self._states[self._current_state].enter()
