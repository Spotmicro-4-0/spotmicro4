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
        self._log.debug('Entering IDLE state')
        self._servo_service.deactivate_servos()

    def update(self) -> None:
        pass

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        self._log.debug(f"IdleState: Checking START button, event.start={event.start}")
        if self._button_manager.check_edge(ControllerEventKey.START, event):
            self._log.debug("IdleState: START button pressed, transitioning to STAND")
            return RobotStateName.STAND
        return None

    def exit(self) -> None:
        self._log.debug('Exiting IDLE state')
        self._servo_service.activate_servos()
