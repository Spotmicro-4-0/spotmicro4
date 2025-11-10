from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class StandState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering STAND state')

    def update(self) -> None:
        self._log.debug('Updating STAND state')

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug('Handling STAND state')

    def exit(self) -> None:
        self._log.debug('Exiting STAND state')
