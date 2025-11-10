from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class IdleState(BaseRobotState):

    def __init__(self):
        pass

    @property
    def frame_duration(self) -> float:
        """Idle state can use a slower frame rate since we're just waiting for input."""
        return 0.1  # 10 Hz instead of 50 Hz

    def enter(self) -> None:
        self._log.debug('Entering IDLE state')

    def update(self) -> None:
        self._log.debug('Updating IDLE state')

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug('Handling IDLE state')

    def exit(self) -> None:
        self._log.debug('Exiting IDLE state')
