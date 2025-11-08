from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.runtime.motion_controller.models import ControllerEventKey
from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.services import ButtonManager
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class IdleState(BaseRobotState):

    def __init__(self):
        self._servo_service = ServoService()
        self._button_manager = ButtonManager()

    @property
    def frame_duration(self) -> float:
        """Idle state can use a slower frame rate since we're just waiting for input."""
        return 0.1  # 10 Hz instead of 50 Hz

    def enter(self) -> None:
        import time
        import sys

        self._log.debug('Entering IDLE state')

        deactivate_start = time.time()
        self._servo_service.deactivate_servos()
        deactivate_duration = (time.time() - deactivate_start) * 1000

        if deactivate_duration > 10:
            print(
                f"      [IdleState] deactivate_servos() took {deactivate_duration:.2f}ms",
                file=sys.stderr,
                flush=True,
            )

    def update(self) -> None:
        import time

        start_time = time.time()
        # Idle state does nothing in update
        duration = (time.time() - start_time) * 1000
        self._log.debug(f"IdleState.update took {duration:.2f}ms")

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        import time
        import sys

        start_time = time.time()

        edge_result = self._button_manager.check_edge(ControllerEventKey.START, event)
        check_duration = (time.time() - start_time) * 1000

        result = None
        if edge_result:
            result = RobotStateName.STAND
            print(
                f"    [IdleState] START button pressed, transitioning to STAND (took {check_duration:.2f}ms)",
                file=sys.stderr,
                flush=True,
            )

        # Only log if it's slow
        if check_duration > 20:
            print(
                f"    [IdleState] handle_event SLOW: {check_duration:.2f}ms, result={result}",
                file=sys.stderr,
                flush=True,
            )

        return result

    def exit(self) -> None:
        import time
        import sys

        self._log.debug('Exiting IDLE state')

        activate_start = time.time()
        self._servo_service.activate_servos()
        activate_duration = (time.time() - activate_start) * 1000

        if activate_duration > 10:
            print(
                f"      [IdleState] activate_servos() took {activate_duration:.2f}ms",
                file=sys.stderr,
                flush=True,
            )
