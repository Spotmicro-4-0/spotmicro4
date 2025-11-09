from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class TransitIdleState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_IDLE state')

    def update(self) -> None:
        import time

        start_time = time.time()
        # Transition state does nothing
        duration = (time.time() - start_time) * 1000
        self._log.debug(f"TransitIdleState.update took {duration:.2f}ms")

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        import time

        start_time = time.time()
        result = None  # Transition states don't handle events
        duration = (time.time() - start_time) * 1000
        self._log.debug(f"TransitIdleState.handle_event took {duration:.2f}ms")
        return result

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_IDLE state')


class TransitStandState(BaseRobotState):

    def enter(self) -> None:
        self._log.debug('Entering TRANSIT_STAND state')

    def update(self) -> None:
        import time

        start_time = time.time()
        # Transition state does nothing
        duration = (time.time() - start_time) * 1000
        self._log.debug(f"TransitStandState.update took {duration:.2f}ms")

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        import time

        start_time = time.time()
        result = None  # Transition states don't handle events
        duration = (time.time() - start_time) * 1000
        self._log.debug(f"TransitStandState.handle_event took {duration:.2f}ms")
        return result

    def exit(self) -> None:
        self._log.debug('Exiting TRANSIT_STAND state')
