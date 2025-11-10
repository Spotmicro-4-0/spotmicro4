from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class WalkState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering WALKING state')

    def update(self) -> None:
        self._log.debug('Updating WALKING state')

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug('Handling WALKING state')

    def exit(self) -> None:
        self._log.debug('Exiting WALKING state')
