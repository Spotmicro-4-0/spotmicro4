import math
from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.runtime.motion_controller.models import ControllerEventKey
from spotmicroai.runtime.motion_controller.models import ControllerEvent
from spotmicroai.runtime.motion_controller.services import ButtonManager, PoseService
from spotmicroai.runtime.motion_controller.state._base_state import BaseRobotState, RobotStateName


class StandState(BaseRobotState):

    def __init__(self):
        self._servo_service = ServoService()
        self._pose_service = PoseService()
        self._button_manager = ButtonManager()
        self._prev_pitch_input: float | None = None
        self._prev_pitch_analog: float | None = None

    def enter(self) -> None:
        self._log.debug('Entering STAND state')

    def update(self) -> None:
        pass

    def handle_event(self, event: ControllerEvent) -> RobotStateName | None:
        if not event:
            return None

        if self._button_manager.check_edge(ControllerEventKey.START, event):
            return RobotStateName.IDLE

        if self._button_manager.check_edge(ControllerEventKey.BACK, event):
            return RobotStateName.WALK

        if self._button_manager.check_edge(ControllerEventKey.RIGHT_BUMPER, event):
            next_pose = self._pose_service.next()
            self._servo_service.set_pose(next_pose)

        if self._button_manager.check_edge(ControllerEventKey.LEFT_BUMPER, event):
            prev_pose = self._pose_service.previous()
            self._servo_service.set_pose(prev_pose)

        if event.get(ControllerEventKey.DPAD_VERTICAL):
            self._body_move_pitch(event.dpad_vertical)

        if event.get(ControllerEventKey.DPAD_HORIZONTAL):
            self._body_move_roll(event.dpad_horizontal)

        if event.get(ControllerEventKey.LEFT_STICK_Y):
            self._body_move_pitch_analog(event.left_stick_y)

        if event.get(ControllerEventKey.LEFT_STICK_X):
            self._body_move_roll_analog(event.left_stick_x)

        if event.get(ControllerEventKey.RIGHT_STICK_Y):
            self._body_move_yaw_analog(event.right_stick_y)

        if event.get(ControllerEventKey.RIGHT_STICK_X):
            self._body_move_height_analog(event.right_stick_x)

        if event.get(ControllerEventKey.A):
            self._servo_service.rest_position()

        return None

    def exit(self) -> None:
        self._log.debug('Exiting STAND state')

    def _body_move_pitch(self, raw_value: float):
        prev = self._prev_pitch_input
        if prev is None:
            self._prev_pitch_input = raw_value
            return

        alpha = 0.1
        smoothed_value = prev + alpha * (raw_value - prev)
        self._prev_pitch_input = smoothed_value

        if abs(smoothed_value) < 0.05:
            return

        scaled = math.copysign(abs(smoothed_value) ** 1.5, smoothed_value)

        leg_increment = 10 * scaled
        foot_increment = 15 * scaled

        self._servo_service.rear_leg_left_angle += leg_increment
        self._servo_service.rear_foot_left_angle -= foot_increment
        self._servo_service.rear_leg_right_angle -= leg_increment
        self._servo_service.rear_foot_right_angle += foot_increment
        self._servo_service.front_leg_left_angle += leg_increment
        self._servo_service.front_foot_left_angle -= foot_increment
        self._servo_service.front_leg_right_angle -= leg_increment
        self._servo_service.front_foot_right_angle += foot_increment

    def _body_move_roll(self, raw_value: float):
        increment = 1

        if raw_value < 0:
            self._servo_service.rear_shoulder_left_angle = max(
                self._servo_service.rear_shoulder_left_angle - increment, 0
            )
            self._servo_service.rear_shoulder_right_angle = max(
                self._servo_service.rear_shoulder_right_angle - increment, 0
            )
            self._servo_service.front_shoulder_left_angle = min(
                self._servo_service.front_shoulder_left_angle + increment, 180
            )
            self._servo_service.front_shoulder_right_angle = min(
                self._servo_service.front_shoulder_right_angle + increment, 180
            )

        elif raw_value > 0:
            self._servo_service.rear_shoulder_left_angle = min(
                self._servo_service.rear_shoulder_left_angle + increment, 180
            )
            self._servo_service.rear_shoulder_right_angle = min(
                self._servo_service.rear_shoulder_right_angle + increment, 180
            )
            self._servo_service.front_shoulder_left_angle = max(
                self._servo_service.front_shoulder_left_angle - increment, 0
            )
            self._servo_service.front_shoulder_right_angle = max(
                self._servo_service.front_shoulder_right_angle - increment, 0
            )

        else:
            self._servo_service.rest_position()

    def _body_move_pitch_analog(self, raw_value: float):
        INPUT_SCALE = 3.5
        RESPONSE_CURVE = 1.4
        ALPHA = 0.1

        ANGLE_RANGES = {
            "leg": (-10, 10),
            "foot": (-5, 5),
        }

        prev = self._prev_pitch_analog
        if prev is None:
            self._prev_pitch_analog = raw_value
            return

        smoothed_value = prev + ALPHA * (raw_value - prev)
        self._prev_pitch_analog = smoothed_value

        curved = math.copysign(abs(smoothed_value) ** RESPONSE_CURVE, smoothed_value)

        mapped_input = curved * INPUT_SCALE

        leg_delta = self.maprange((-INPUT_SCALE, INPUT_SCALE), ANGLE_RANGES["leg"], mapped_input)
        foot_delta = self.maprange((-INPUT_SCALE, INPUT_SCALE), ANGLE_RANGES["foot"], mapped_input)

        self._servo_service.front_leg_left_angle += leg_delta
        self._servo_service.front_foot_left_angle += foot_delta

        self._servo_service.front_leg_right_angle += leg_delta
        self._servo_service.front_foot_right_angle += foot_delta

        self._servo_service.rear_leg_left_angle += leg_delta
        self._servo_service.rear_foot_left_angle += foot_delta

        self._servo_service.rear_leg_right_angle += leg_delta
        self._servo_service.rear_foot_right_angle += foot_delta

    def _body_move_roll_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.front_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))

        self._servo_service.front_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))

    def _body_move_yaw_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.front_shoulder_left_angle = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))

        self._servo_service.front_shoulder_right_angle = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))

    def _body_move_height_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        for name in ["front_leg_left_angle", "rear_leg_left_angle", "front_leg_right_angle", "rear_leg_right_angle"]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (180, 20), raw_value)))

        for name in [
            "front_foot_left_angle",
            "rear_foot_left_angle",
            "front_foot_right_angle",
            "rear_foot_right_angle",
        ]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (130, 170), raw_value)))

    def maprange(self, from_range: tuple, to_range: tuple, value: float) -> float:
        (from_start, from_end), (to_start, to_end) = from_range, to_range
        return to_start + ((value - from_start) * (to_end - to_start) / (from_end - from_start))
