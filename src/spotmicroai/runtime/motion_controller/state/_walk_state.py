from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.runtime.motion_controller.models import ControllerEventKey
from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.services import ButtonManager, KeyframeService
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotState


class WalkState(BaseRobotState):

    def __init__(self):
        self._servo_service = ServoService()
        self._keyframe_service = KeyframeService()
        self._button_manager = ButtonManager()

    def enter(self) -> None:
        self._log.debug('Entering WALK state')
        self._keyframe_service.reset_walking_state()

    def update(self) -> None:
        keyframe = self._keyframe_service.update_keyframes()
        pose = keyframe.to_pose()

        self._servo_service.set_front_right_servos(
            pose.front_right.foot_angle, pose.front_right.leg_angle, pose.front_right.shoulder_angle
        )

        self._servo_service.set_rear_left_servos(
            pose.rear_left.foot_angle, pose.rear_left.leg_angle, pose.rear_left.shoulder_angle
        )

        self._servo_service.set_front_left_servos(
            pose.front_left.foot_angle, pose.front_left.leg_angle, pose.front_left.shoulder_angle
        )

        self._servo_service.set_rear_right_servos(
            pose.rear_right.foot_angle, pose.rear_right.leg_angle, pose.rear_right.shoulder_angle
        )

    def handle_event(self, event: ControllerEvent) -> RobotState | None:
        if not event:
            return None

        if self._button_manager.check_edge(ControllerEventKey.START, event):
            return RobotState.IDLE

        if self._button_manager.check_edge(ControllerEventKey.BACK, event):
            return RobotState.STAND

        if self._button_manager.check_edge(ControllerEventKey.DPAD_VERTICAL, event):
            if event.dpad_vertical > 0:
                self._keyframe_service.adjust_walking_speed(-1)
            else:
                self._keyframe_service.adjust_walking_speed(1)

        if event.get(ControllerEventKey.LEFT_STICK_Y):
            self._keyframe_service.set_forward_factor(event.left_stick_y)

        if event.get(ControllerEventKey.LEFT_STICK_X):
            self._keyframe_service.set_rotation_factor(event.left_stick_x)

        if event.get(ControllerEventKey.LEFT_STICK_CLICK):
            self._keyframe_service.reset_movement()

        if event.get(ControllerEventKey.RIGHT_STICK_Y):
            self._keyframe_service.set_lean(event.right_stick_y)

        if event.get(ControllerEventKey.RIGHT_STICK_X):
            self._keyframe_service.set_height_offset(event.right_stick_x)

        if event.get(ControllerEventKey.RIGHT_STICK_CLICK):
            self._keyframe_service.reset_body_adjustments()

        if event.get(ControllerEventKey.A):
            self._servo_service.rest_position()

        return None

    def exit(self) -> None:
        self._log.debug('Exiting WALK state')
