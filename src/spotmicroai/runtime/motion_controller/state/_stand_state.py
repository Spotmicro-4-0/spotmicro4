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

        self._log.debug(
            f"StandState: event.start={event.start}, event.back={event.back}, event.left_bumper={event.left_bumper}, event.right_bumper={event.right_bumper}"
        )

        if self._button_manager.check_edge(ControllerEventKey.START, event):
            self._log.debug("StandState: START pressed, transitioning to IDLE")
            return RobotStateName.IDLE

        if self._button_manager.check_edge(ControllerEventKey.BACK, event):
            self._log.debug("StandState: BACK pressed, transitioning to WALK")
            return RobotStateName.WALK

        if self._button_manager.check_edge(ControllerEventKey.RIGHT_BUMPER, event):
            self._log.debug("StandState: RIGHT_BUMPER pressed, next pose")
            next_pose = self._pose_service.next()
            self._servo_service.set_pose(next_pose)

        if self._button_manager.check_edge(ControllerEventKey.LEFT_BUMPER, event):
            self._log.debug("StandState: LEFT_BUMPER pressed, previous pose")
            prev_pose = self._pose_service.previous()
            self._servo_service.set_pose(prev_pose)

        if event.dpad_vertical:
            self._body_move_pitch(event.dpad_vertical)

        if event.dpad_horizontal:
            self._body_move_roll(event.dpad_horizontal)

        if event.left_stick_y:
            self._body_move_pitch_analog(event.left_stick_y)

        if event.left_stick_x:
            self._body_move_roll_analog(event.left_stick_x)

        if event.right_stick_y:
            self._body_move_yaw_analog(event.right_stick_y)

        if event.right_stick_x:
            self._body_move_height_analog(event.right_stick_x)

        if event.a:
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

        self._servo_service.rear_leg_left += leg_increment
        self._servo_service.rear_foot_left -= foot_increment
        self._servo_service.rear_leg_right -= leg_increment
        self._servo_service.rear_foot_right += foot_increment
        self._servo_service.front_leg_left += leg_increment
        self._servo_service.front_foot_left -= foot_increment
        self._servo_service.front_leg_right -= leg_increment
        self._servo_service.front_foot_right += foot_increment

    def _body_move_roll(self, raw_value: float):
        increment = 1

        if raw_value < 0:
            self._servo_service.rear_shoulder_left = max(self._servo_service.rear_shoulder_left - increment, 0)
            self._servo_service.rear_shoulder_right = max(self._servo_service.rear_shoulder_right - increment, 0)
            self._servo_service.front_shoulder_left = min(self._servo_service.front_shoulder_left + increment, 180)
            self._servo_service.front_shoulder_right = min(self._servo_service.front_shoulder_right + increment, 180)

        elif raw_value > 0:
            self._servo_service.rear_shoulder_left = min(self._servo_service.rear_shoulder_left + increment, 180)
            self._servo_service.rear_shoulder_right = min(self._servo_service.rear_shoulder_right + increment, 180)
            self._servo_service.front_shoulder_left = max(self._servo_service.front_shoulder_left - increment, 0)
            self._servo_service.front_shoulder_right = max(self._servo_service.front_shoulder_right - increment, 0)

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

        self._servo_service.front_leg_left += leg_delta
        self._servo_service.front_foot_left += foot_delta

        self._servo_service.front_leg_right += leg_delta
        self._servo_service.front_foot_right += foot_delta

        self._servo_service.rear_leg_left += leg_delta
        self._servo_service.rear_foot_left += foot_delta

        self._servo_service.rear_leg_right += leg_delta
        self._servo_service.rear_foot_right += foot_delta

    def _body_move_roll_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.front_shoulder_left = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left = int(self.maprange((-5, 5), (145, 35), raw_value))

        self._servo_service.front_shoulder_right = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right = int(self.maprange((-5, 5), (35, 145), raw_value))

    def _body_move_yaw_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.front_shoulder_left = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right = int(self.maprange((-5, 5), (35, 145), raw_value))

        self._servo_service.front_shoulder_right = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left = int(self.maprange((-5, 5), (145, 35), raw_value))

    def _body_move_height_analog(self, raw_value: float):
        raw_value = math.floor(raw_value * 10 / 2)

        for name in ["front_leg_left", "rear_leg_left", "front_leg_right", "rear_leg_right"]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (180, 20), raw_value)))

        for name in [
            "front_foot_left",
            "rear_foot_left",
            "front_foot_right",
            "rear_foot_right",
        ]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (130, 170), raw_value)))

    def maprange(self, from_range: tuple, to_range: tuple, value: float) -> float:
        (from_start, from_end), (to_start, to_end) = from_range, to_range
        return to_start + ((value - from_start) * (to_end - to_start) / (from_end - from_start))
