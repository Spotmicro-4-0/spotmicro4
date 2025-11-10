import time
from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class TransitIdleState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_IDLE state')

    def update(self) -> None:
        self._log.debug('Updating TRANSIT_IDLE state')

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug('Handling TRANSIT_IDLE state')

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_IDLE state')


class TransitStandState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_STAND state')

    def update(self) -> None:
        self._log.debug('Updating TRANSIT_STAND state')

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug('Handling TRANSIT_STAND state')

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_STAND state')
