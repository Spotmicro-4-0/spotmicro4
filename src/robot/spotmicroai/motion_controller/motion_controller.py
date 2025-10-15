import math
import queue
import signal
import sys
import time

import spotmicroai.utilities.queues as queues
from spotmicroai.motion_controller.models.pose import Pose
from spotmicroai.motion_controller.services.keyframe_service import \
    KeyframeService
from spotmicroai.motion_controller.services.pose_service import PoseService
from spotmicroai.motion_controller.services.servo_service import ServoService
from spotmicroai.motion_controller.wrappers.pca9685 import PCA9685Board
from spotmicroai.utilities.general import General
from spotmicroai.utilities.log import Logger

from .constants import FOOT_SERVO_OFFSET, INACTIVITY_TIME, LEG_SERVO_OFFSET
from .enums import ControllerEvent
from .wrappers.buzzer import Buzzer

log = Logger().setup_logger('Motion controller')


class MotionController:

    _pca9685_board: PCA9685Board
    _servo_service: ServoService
    _pose_service: PoseService
    _buzzer: Buzzer

    _is_activated = False
    _is_running = False
    _keyframe_service: KeyframeService

    def __init__(self, communication_queues):
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._pca9685_board = PCA9685Board()
            self._buzzer = Buzzer()
            self._pose_service = PoseService()
            self._keyframe_service = KeyframeService()

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._motion_queue = communication_queues[queues.MOTION_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]
            self._lcd_screen_queue.put(queues.MOTION_CONTROLLER + ' OK')

        except Exception as e:
            log.error('Motion controller initialization problem', e)
            self._lcd_screen_queue.put(queues.MOTION_CONTROLLER + ' NOK')
            try:
                if self._pca9685_board:
                    self._pca9685_board.deactivate()
            finally:
                sys.exit(1)

    def exit_gracefully(self, signum, frame):
        log.info("Graceful shutdown initiated...")

        # Move servos to neutral (rest) first
        self._servo_service.rest_position()
        time.sleep(0.3)

        try:
            self._pca9685_board.deactivate()
        except Exception as e:
            log.warning(f"Could not deactivate PCA9685 cleanly: {e}")

        self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
        self._is_activated = False
        log.info("Motion controller terminated safely.")
        sys.exit(0)

    def do_process_events_from_queues(self):

        # State Variables
        inactivity_counter = time.time()
        activate_debounce_time = 0
        walking_debounce_time = 0

        FRAME_RATE_HZ = 50
        FRAME_DURATION = 1.0 / FRAME_RATE_HZ

        event = {}
        prev_event = {}

        while True:
            frame_start = time.time()

            try:
                event = self._motion_queue.get(block=False)
            except queue.Empty:
                event = {}

            if ControllerEvent.START in event and event[ControllerEvent.START] == 1:
                if time.time() - activate_debounce_time < 1:
                    continue
                else:
                    activate_debounce_time = time.time()

                if self._is_activated:
                    self._buzzer.beep()
                    self._is_activated = False
                    self._servo_service.rest_position()
                    time.sleep(0.25)
                    self._pca9685_board.deactivate()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                else:
                    log.info('Press START/OPTIONS to re-enable the servos')
                    self._buzzer.beep()
                    self._is_activated = True
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ACTIVATE)
                    self._pca9685_board.activate()
                    self._servo_service = ServoService()
                    time.sleep(0.25)
                    self._servo_service.rest_position()
                    # Reset inactivity counter on activation so timer starts now
                    inactivity_counter = time.time()

            if not self._is_activated:
                time.sleep(0.1)
                continue

            if event == {}:
                # if there is no user input, check to see if it have been long enough to warn the user
                if (time.time() - inactivity_counter) >= INACTIVITY_TIME:
                    log.info(f'Inactivity lasted {INACTIVITY_TIME} seconds. Press start to reactivate')
                    log.info('Shutting down the servos.')
                    log.info('Press START/OPTIONS to enable the servos')

                    self._servo_service.rest_position()
                    time.sleep(0.1)
                    self._pca9685_board.deactivate()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    self._is_activated = False
                    self._is_running = False
                
                # throttle CPU when no input but still activated
                time.sleep(0.05)
                continue

            else:
                # If there activity, reset the timer
                inactivity_counter = time.time()

            try:
                if self._is_running:
                    # Update walking cycle and get current position
                    index, ratio = self._keyframe_service.update_walking_keyframes()

                    # Get interpolated leg positions and apply to servos
                    leg_positions = self._keyframe_service.get_interpolated_leg_positions(ratio)

                    # Front Right
                    foot_angle, leg_angle, shoulder_angle = leg_positions['front_right'].inverse_kinematics()
                    self.set_front_right_servos(foot_angle, leg_angle, shoulder_angle)

                    # Rear Left
                    foot_angle, leg_angle, shoulder_angle = leg_positions['rear_left'].inverse_kinematics()
                    self.set_rear_left_servos(foot_angle, leg_angle, shoulder_angle)

                    # Front Left
                    foot_angle, leg_angle, shoulder_angle = leg_positions['front_left'].inverse_kinematics()
                    self.set_front_left_servos(foot_angle, leg_angle, shoulder_angle)

                    # Rear Right
                    foot_angle, leg_angle, shoulder_angle = leg_positions['rear_right'].inverse_kinematics()
                    self.set_rear_right_servos(foot_angle, leg_angle, shoulder_angle)

                if event[ControllerEvent.A]:
                    self._is_running = False
                    self._servo_service.rest_position()

                # Handle cases when robot is running
                if self._is_running:
                    # Right Trigger
                    # if self.check_event(ControllerEvent.RIGHT_TRIGGER, event, prev_event):
                    #     self._current_gait_type = 0
                    # Left Trigger
                    # if self.check_event(ControllerEvent.LEFT_TRIGGER, event, prev_event):
                    #     self._current_gait_type = 0

                    if self.check_event(ControllerEvent.Y, event, prev_event):
                        pass

                    if self.check_event(ControllerEvent.B, event, prev_event):
                        pass

                    if self.check_event(ControllerEvent.X, event, prev_event):
                        pass

                    # D-Pad Left/Right
                    if self.check_event(ControllerEvent.DPAD_HORIZONTAL, event, prev_event):
                        pass
                    # D-Pad Up/Down
                    if self.check_event(ControllerEvent.DPAD_VERTICAL, event, prev_event):
                        if event[ControllerEvent.DPAD_VERTICAL] > 0:
                            self._keyframe_service.adjust_walking_speed(-1)
                        else:
                            self._keyframe_service.adjust_walking_speed(1)

                    # Left Thumbstick Up/Down
                    if event[ControllerEvent.LEFT_STICK_Y]:
                        self._keyframe_service.set_forward_factor(event[ControllerEvent.LEFT_STICK_Y])

                    # Left Thumbstick Left/Right
                    if event[ControllerEvent.LEFT_STICK_X]:
                        self._keyframe_service.set_rotation_factor(event[ControllerEvent.LEFT_STICK_X])

                    # Left Thumbstick Click
                    if event[ControllerEvent.LEFT_STICK_CLICK]:
                        self._keyframe_service.reset_movement()

                    # Right Thumbstick Up/Down
                    if event[ControllerEvent.RIGHT_STICK_Y]:
                        self._keyframe_service.set_lean(event[ControllerEvent.RIGHT_STICK_Y])
                    # Right Thumbstick Left/Right
                    if event[ControllerEvent.RIGHT_STICK_X]:
                        self._keyframe_service.set_height_offset(event[ControllerEvent.RIGHT_STICK_X])
                        # self.set_lean(event[ControllerEvent.RIGHT_STICK_X])
                    # Right Thumbstick Click
                    if event[ControllerEvent.RIGHT_STICK_CLICK]:
                        self._keyframe_service.reset_body_adjustments()
                else:
                    # Right Bumper
                    if self.check_event(ControllerEvent.RIGHT_BUMPER, event, prev_event):
                        # Next Pose
                        time.sleep(0.5)
                        self.handle_pose(self._pose_service.next())
                    # Left Bumper
                    if self.check_event(ControllerEvent.LEFT_BUMPER, event, prev_event):
                        # Prev Pose
                        time.sleep(1)
                        self.handle_pose(self._pose_service.previous())

                    if event[ControllerEvent.DPAD_VERTICAL]:
                        self.body_move_pitch(event[ControllerEvent.DPAD_VERTICAL])

                    if event[ControllerEvent.DPAD_HORIZONTAL]:
                        self.body_move_roll(event[ControllerEvent.DPAD_HORIZONTAL])

                    if event[ControllerEvent.LEFT_STICK_Y]:
                        self.body_move_pitch_analog(event[ControllerEvent.LEFT_STICK_Y])

                    if event[ControllerEvent.LEFT_STICK_X]:
                        self.body_move_roll_analog(event[ControllerEvent.LEFT_STICK_X])

                    if event[ControllerEvent.RIGHT_STICK_Y]:
                        self.body_move_yaw_analog(event[ControllerEvent.RIGHT_STICK_Y])

                    if event[ControllerEvent.RIGHT_STICK_X]:
                        self.body_move_height_analog(event[ControllerEvent.RIGHT_STICK_X])

                    # if event[ControllerEvent.Y]:
                    #     self.standing_position()

                    # if event[ControllerEvent.B]:
                    #     self.handle_instinct(self._instincts['pushUp'])

                    # if event[ControllerEvent.X]:
                    #     self.handle_instinct(self._instincts['sit'])

                    # if event[ControllerEvent.Y]:
                    #     self.handle_instinct(self._instincts['sleep'])

                if event[ControllerEvent.BACK] == 1:
                    if time.time() - walking_debounce_time < 1:
                        continue
                    else:
                        walking_debounce_time = time.time()

                    self._is_running = not self._is_running
                    if self._is_running:
                        # Reset walking state when starting to walk
                        self._keyframe_service.reset_walking_state()
                    time.sleep(0.5)

                self._servo_service.commit()

                prev_event = event
            finally:
                # continue
                pass
            elapsed_time = time.time() - frame_start

            if elapsed_time < FRAME_DURATION:
                time.sleep(FRAME_DURATION - elapsed_time)

    def check_event(self, key, event, prev_event):
        return key in event and event[key] != 0 and key in prev_event and prev_event[key] == 0

    def handle_pose(self, pose: Pose):
        self._servo_service.rear_shoulder_left_angle = pose.rear_left.shoulder_angle
        self._servo_service.rear_leg_left_angle = pose.rear_left.leg_angle
        self._servo_service.rear_foot_left_angle = pose.rear_left.foot_angle

        self._servo_service.rear_shoulder_right_angle = pose.rear_right.shoulder_angle
        self._servo_service.rear_leg_right_angle = pose.rear_right.leg_angle
        self._servo_service.rear_foot_right_angle = pose.rear_right.foot_angle

        self._servo_service.front_shoulder_left_angle = pose.front_left.shoulder_angle
        self._servo_service.front_leg_left_angle = pose.front_left.leg_angle
        self._servo_service.front_foot_left_angle = pose.front_left.foot_angle

        self._servo_service.front_shoulder_right_angle = pose.front_right.shoulder_angle
        self._servo_service.front_leg_right_angle = pose.front_right.leg_angle
        self._servo_service.front_foot_right_angle = pose.front_right.foot_angle

    def set_front_right_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the front right leg.

        Parameters
        ----------
        foot : float
            Servo angle for foot in degrees.
        leg : float
            Servo angle for leg in degrees.
        shoulder : float
            Servo angle for shoulder in degrees.
        """
        self._servo_service.front_shoulder_right_angle = shoulder_angle
        self._servo_service.front_leg_right_angle = max(180 - (leg_angle + LEG_SERVO_OFFSET), 0)
        self._servo_service.front_foot_right_angle = 180 - max(foot_angle - FOOT_SERVO_OFFSET, 0)

    def set_front_left_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the front left leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._servo_service.front_shoulder_left_angle = 180 - shoulder_angle
        self._servo_service.front_leg_left_angle = min(leg_angle + LEG_SERVO_OFFSET, 180)
        self._servo_service.front_foot_left_angle = max(foot_angle - FOOT_SERVO_OFFSET, 0)

    def set_rear_right_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the back right leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._servo_service.rear_shoulder_right_angle = 180 - shoulder_angle
        self._servo_service.rear_leg_right_angle = max(180 - (leg_angle + LEG_SERVO_OFFSET), 0)
        self._servo_service.rear_foot_right_angle = 180 - max(foot_angle - FOOT_SERVO_OFFSET, 0)

    def set_rear_left_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the back left leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self._servo_service.rear_shoulder_left_angle = shoulder_angle
        self._servo_service.rear_leg_left_angle = min(leg_angle + LEG_SERVO_OFFSET, 180)
        self._servo_service.rear_foot_left_angle = max(foot_angle - FOOT_SERVO_OFFSET, 0)

    def body_move_pitch(self, raw_value: float):

        leg_increment = 10
        foot_increment = 15

        if raw_value < 0:
            self._servo_service.rear_leg_left_angle -= leg_increment
            self._servo_service.rear_foot_left_angle += foot_increment
            self._servo_service.rear_leg_right_angle += leg_increment
            self._servo_service.rear_foot_right_angle -= foot_increment
            self._servo_service.front_leg_left_angle -= leg_increment
            self._servo_service.front_foot_left_angle += foot_increment
            self._servo_service.front_leg_right_angle += leg_increment
            self._servo_service.front_foot_right_angle -= foot_increment

        elif raw_value > 0:
            self._servo_service.rear_leg_left_angle += leg_increment
            self._servo_service.rear_foot_left_angle -= foot_increment
            self._servo_service.rear_leg_right_angle -= leg_increment
            self._servo_service.rear_foot_right_angle += foot_increment
            self._servo_service.front_leg_left_angle += leg_increment
            self._servo_service.front_foot_left_angle -= foot_increment
            self._servo_service.front_leg_right_angle -= leg_increment
            self._servo_service.front_foot_right_angle += foot_increment

        else:
            self._servo_service.rest_position()

    def body_move_roll(self, raw_value: float):

        range = 1

        if raw_value < 0:
            self._servo_service.rear_shoulder_left_angle = max(self._servo_service.rear_shoulder_left_angle - range, 0)
            self._servo_service.rear_shoulder_right_angle = max(
                self._servo_service.rear_shoulder_right_angle - range, 0
            )
            self._servo_service.front_shoulder_left_angle = min(
                self._servo_service.front_shoulder_left_angle + range, 180
            )
            self._servo_service.front_shoulder_right_angle = min(
                self._servo_service.front_shoulder_right_angle + range, 180
            )

        elif raw_value > 0:
            self._servo_service.rear_shoulder_left_angle = min(
                self._servo_service.rear_shoulder_left_angle + range, 180
            )
            self._servo_service.rear_shoulder_right_angle = min(
                self._servo_service.rear_shoulder_right_angle + range, 180
            )
            self._servo_service.front_shoulder_left_angle = max(
                self._servo_service.front_shoulder_left_angle - range, 0
            )
            self._servo_service.front_shoulder_right_angle = max(
                self._servo_service.front_shoulder_right_angle - range, 0
            )

        else:
            self._servo_service.rest_position()

    def standing_position(self):

        variation_leg = 30
        variation_foot = 50

        self._servo_service.rear_shoulder_left_angle += 10
        self._servo_service.rear_leg_left_angle -= variation_leg
        self._servo_service.rear_foot_left_angle += variation_foot

        self._servo_service.rear_shoulder_right_angle -= 10
        self._servo_service.rear_leg_right_angle += variation_leg
        self._servo_service.rear_foot_right_angle -= variation_foot

        time.sleep(0.05)

        self._servo_service.front_shoulder_left_angle -= 10
        self._servo_service.front_leg_left_angle -= variation_leg - 5
        self._servo_service.front_foot_left_angle += variation_foot - 5

        self._servo_service.front_shoulder_right_angle += 10
        self._servo_service.front_leg_right_angle += variation_leg + 5
        self._servo_service.front_foot_right_angle -= variation_foot + 5

    # def body_move_position_right(self):

    #     move = 20

    #     variation_leg = 50
    #     variation_feet = 70

    #     self.servos_configurations.rear_left.shoulder.rest_angle = self.servos_configurations.rear_left.shoulder.rest_angle + 10 + move
    #     self.servos_configurations.rear_left.leg.rest_angle = self.servos_configurations.rear_left.leg.rest_angle - variation_leg
    #     self.servos_configurations.rear_left.foot.rest_angle = self.servos_configurations.rear_left.foot.rest_angle + variation_feet

    #     self.servos_configurations.rear_right.shoulder.rest_angle = self.servos_configurations.rear_right.shoulder.rest_angle - 10 + move
    #     self.servos_configurations.rear_right.leg.rest_angle = self.servos_configurations.rear_right.leg.rest_angle + variation_leg
    #     self.servos_configurations.rear_right.foot.rest_angle = self.servos_configurations.rear_right.foot.rest_angle - variation_feet

    #     time.sleep(0.05)

    #     self.servos_configurations.front_left.shoulder.rest_angle = self.servos_configurations.front_left.shoulder.rest_angle - 10 - move
    #     self.servos_configurations.front_left.leg.rest_angle = self.servos_configurations.front_left.leg.rest_angle - variation_leg + 5
    #     self.servos_configurations.front_left.foot.rest_angle = self.servos_configurations.front_left.foot.rest_angle + variation_feet - 5

    #     self.servos_configurations.front_right.shoulder.rest_angle = self.servos_configurations.front_right.shoulder.rest_angle + 10 - move
    #     self.servos_configurations.front_right.leg.rest_angle = self.servos_configurations.front_right.leg.rest_angle + variation_leg - 5
    #     self.servos_configurations.front_right.foot.rest_angle = self.servos_configurations.front_right.foot.rest_angle - variation_feet + 5

    # def body_move_position_left(self):

    #     move = 20

    #     variation_leg = 50
    #     variation_feet = 70

    #     self.servos_configurations.rear_left.shoulder.rest_angle = self.servos_configurations.rear_left.shoulder.rest_angle + 10 - move
    #     self.servos_configurations.rear_left.leg.rest_angle = self.servos_configurations.rear_left.leg.rest_angle - variation_leg
    #     self.servos_configurations.rear_left.foot.rest_angle = self.servos_configurations.rear_left.foot.rest_angle + variation_feet

    #     self.servos_configurations.rear_right.shoulder.rest_angle = self.servos_configurations.rear_right.shoulder.rest_angle - 10 - move
    #     self.servos_configurations.rear_right.leg.rest_angle = self.servos_configurations.rear_right.leg.rest_angle + variation_leg
    #     self.servos_configurations.rear_right.foot.rest_angle = self.servos_configurations.rear_right.foot.rest_angle - variation_feet

    #     time.sleep(0.05)

    #     self.servos_configurations.front_left.shoulder.rest_angle = self.servos_configurations.front_left.shoulder.rest_angle - 10 + move
    #     self.servos_configurations.front_left.leg.rest_angle = self.servos_configurations.front_left.leg.rest_angle - variation_leg + 5
    #     self.servos_configurations.front_left.foot.rest_angle = self.servos_configurations.front_left.foot.rest_angle + variation_feet - 5

    #     self.servos_configurations.front_right.shoulder.rest_angle = self.servos_configurations.front_right.shoulder.rest_angle + 10 + move
    #     self.servos_configurations.front_right.leg.rest_angle = self.servos_configurations.front_right.leg.rest_angle + variation_leg - 5
    #     self.servos_configurations.front_right.foot.rest_angle = self.servos_configurations.front_right.foot.rest_angle - variation_feet + 5

    #############################################
    # Left thumbstick controls
    #############################################

    def body_move_pitch_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_leg_left_angle = int(General().maprange((5, -5), (180, 180), raw_value))
        self._servo_service.rear_foot_left_angle = int(General().maprange((5, -5), (10, 50), raw_value))
        self._servo_service.rear_leg_right_angle = int(General().maprange((5, -5), (0, 0), raw_value))
        self._servo_service.rear_foot_right_angle = int(General().maprange((5, -5), (170, 130), raw_value))

        self._servo_service.front_leg_left_angle = int(General().maprange((-5, 5), (160, 180), raw_value))
        self._servo_service.front_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.front_leg_right_angle = int(General().maprange((-5, 5), (20, 0), raw_value))
        self._servo_service.front_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_roll_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))

        self._servo_service.front_shoulder_left_angle = int(General().maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.front_shoulder_right_angle = int(General().maprange((-5, 5), (145, 35), raw_value))

    def body_move_height_analog(self, raw_value):

        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_leg_left_angle = int(General().maprange((5, -5), (160, 180), raw_value))
        self._servo_service.rear_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.rear_leg_right_angle = int(General().maprange((5, -5), (20, 0), raw_value))
        self._servo_service.rear_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

        self._servo_service.front_leg_left_angle = int(General().maprange((5, -5), (160, 180), raw_value))
        self._servo_service.front_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.front_leg_right_angle = int(General().maprange((5, -5), (20, 0), raw_value))
        self._servo_service.front_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_yaw_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))

        self._servo_service.front_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servo_service.front_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))
