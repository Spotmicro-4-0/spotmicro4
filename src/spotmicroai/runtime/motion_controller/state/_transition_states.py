from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotState


class TransitIdleState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_IDLE state')

    def update(self) -> None:
        pass

    def handle_event(self, event: ControllerEvent) -> RobotState | None:
        return None

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_IDLE state')


class TransitStandState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_STAND state')

    def update(self) -> None:
        pass

    def handle_event(self, event: ControllerEvent) -> RobotState | None:
        return None

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_STAND state')
