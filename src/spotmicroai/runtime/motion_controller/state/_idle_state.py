from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.runtime.motion_controller.models import ControllerEventKey
from spotmicroai.runtime.motion_controller.services import ButtonManager
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotState


class IdleState(BaseRobotState):

    def __init__(self):
        self._servo_service = ServoService()
        self._button_manager = ButtonManager()

    def enter(self) -> None:
        self._log.debug('Entering IDLE state')
        self._servo_service.deactivate_servos()

    def update(self) -> None:
        pass

    def handle_event(self, event: dict) -> RobotState | None:
        if self._button_manager.check_edge(ControllerEventKey.START, event):
            return RobotState.STAND
        return None

    def exit(self) -> None:
        self._log.debug('Exiting IDLE state')
        self._servo_service.activate_servos()
