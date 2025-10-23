import math
import queue
import signal
import sys
import time

from spotmicroai import DEFAULT_SLEEP, FRAME_DURATION, INACTIVITY_TIME, TELEMETRY_UPDATE_INTERVAL
from spotmicroai.drivers.buzzer import Buzzer
from spotmicroai.drivers.pca9685 import PCA9685
from spotmicroai.logger import Logger
from spotmicroai.runtime.motion_controller.enums import ControllerEvent
from spotmicroai.runtime.motion_controller.services.button_manager import ButtonManager
from spotmicroai.runtime.motion_controller.services.keyframe_service import KeyframeService
from spotmicroai.runtime.motion_controller.services.pose_service import PoseService
from spotmicroai.runtime.motion_controller.services.servo_service import ServoService
from spotmicroai.runtime.motion_controller.services.telemetry_service import TelemetryService
from spotmicroai.runtime.motion_controller.telemetry_display import TelemetryDisplay
import spotmicroai.runtime.queues as queues

log = Logger().setup_logger('Motion controller')


class MotionController:
    """
    Controls the motion of the SpotMicro robot, handling servo movements, pose adjustments,
    and responding to controller inputs for walking, standing, and other actions.
    """

    _pca9685_board: PCA9685
    _servo_service: ServoService
    _pose_service: PoseService
    _buzzer: Buzzer
    _button_manager: ButtonManager

    _is_activated = False
    _is_running = False
    _keyframe_service: KeyframeService
    _telemetry_display: TelemetryDisplay
    _telemetry_service: TelemetryService

    def __init__(self, communication_queues):
        """
        Initializes the MotionController with necessary services and queues.

        Args:
            communication_queues (dict): Dictionary of queues for inter-controller communication.
        """
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._pca9685_board = PCA9685()
            self._buzzer = Buzzer()
            self._pose_service = PoseService()
            self._keyframe_service = KeyframeService()
            self._button_manager = ButtonManager()

            # # Register buttons that need debouncing
            # START button - toggle activation on/off (1 second debounce)
            # self._button_manager.register_button(ControllerEvent.START, on_press=self._handle_start_button_toggle)
            # BACK button - toggle walking mode on/off (1 second debounce)
            # self._button_manager.register_button(ControllerEvent.BACK, debounce_time=1.0)

            # Initialize telemetry system
            self._telemetry_display = TelemetryDisplay()
            self._telemetry_service = TelemetryService(self)

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._motion_queue = communication_queues[queues.MOTION_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]
            self._lcd_screen_queue.put(queues.MOTION_CONTROLLER + ' OK')

            time.sleep(DEFAULT_SLEEP)
            self._buzzer.beep()

        except Exception as e:
            log.error('Motion controller initialization problem', e)
            self._lcd_screen_queue.put(queues.MOTION_CONTROLLER + ' NOK')
            try:
                if self._pca9685_board:
                    self._pca9685_board.deactivate_board()
            finally:
                sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        """
        Handles graceful shutdown on signal reception, moving servos to rest and deactivating hardware.
        """
        log.info("Graceful shutdown initiated...")

        # Move servos to neutral (rest) first
        self._servo_service.rest_position()
        time.sleep(0.3)

        try:
            self._pca9685_board.deactivate_board()
        except Exception as e:
            log.warning(f"Could not deactivate PCA9685 cleanly: {e}")

        self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
        self._is_activated = False
        log.info("Motion controller terminated safely.")
        sys.exit(0)

    def do_process_events_from_queues(self):
        """
        Main event processing loop that handles controller inputs, updates servo positions,
        manages activation states, and updates telemetry.
        """

        # State Variables
        inactivity_counter = time.time()

        event = {}

        # Telemetry variables
        cycle_index = None
        cycle_ratio = None
        leg_positions = None
        telemetry_update_counter = 0

        # Initialize telemetry display
        log.info("Initializing telemetry display...")
        self._telemetry_display.initialize()
        time.sleep(DEFAULT_SLEEP)  # Give time for display to initialize

        while True:
            frame_start = time.time()

            try:
                event = self._motion_queue.get(block=False)
            except queue.Empty:
                event = {}

            # Handle START button with debouncing
            if self._button_manager.check_edge(ControllerEvent.START, event):
                inactivity_counter = self._handle_start_button_toggle(inactivity_counter)

            if not self._is_activated:
                time.sleep(0.1)
                continue

            if event == {}:
                # if there is no user input, check to see if it have been long enough to warn the user
                if (time.time() - inactivity_counter) >= INACTIVITY_TIME:
                    log.info(f'Inactivity lasted {INACTIVITY_TIME} seconds. Press start to reactivate')
                    log.info('Shutting down the servos.')
                    log.info('Press START/OPTIONS to enable the servos')
                    self._deactivate()

                # throttle CPU when no input but still activated
                time.sleep(0.05)
                continue

            else:
                # If there activity, reset the timer
                inactivity_counter = time.time()

            try:
                if self._is_running:
                    # Update walking cycle and get current position
                    self._update_servo_angles()
                else:
                    # When not running, clear the telemetry values
                    cycle_index = None
                    cycle_ratio = None
                    leg_positions = None

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

                    if self._button_manager.check_edge(ControllerEvent.Y, event):
                        pass

                    if self._button_manager.check_edge(ControllerEvent.B, event):
                        pass

                    if self._button_manager.check_edge(ControllerEvent.X, event):
                        pass

                    # D-Pad Left/Right
                    if self._button_manager.check_edge(ControllerEvent.DPAD_HORIZONTAL, event):
                        pass
                    # D-Pad Up/Down
                    if self._button_manager.check_edge(ControllerEvent.DPAD_VERTICAL, event):
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
                    if self._button_manager.check_edge(ControllerEvent.RIGHT_BUMPER, event):
                        # Next Pose
                        time.sleep(0.5)
                        next_pose = self._pose_service.next()
                        self._servo_service.set_pose(next_pose)
                    # Left Bumper
                    if self._button_manager.check_edge(ControllerEvent.LEFT_BUMPER, event):
                        # Prev Pose
                        time.sleep(0.5)
                        prev_pose = self._pose_service.previous()
                        self._servo_service.set_pose(prev_pose)

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

                # Handle BACK button (walking toggle) with debouncing
                if self._button_manager.check_edge(ControllerEvent.BACK, event):
                    self._is_running = not self._is_running
                    if self._is_running:
                        # Reset walking state when starting to walk
                        self._keyframe_service.reset_walking_state()
                    time.sleep(0.5)

                self._servo_service.commit()

            finally:
                # continue
                pass

            # Calculate timing metrics
            elapsed_time = time.time() - frame_start
            idle_time = max(FRAME_DURATION - elapsed_time, 0)
            loop_time_ms = elapsed_time * 1000
            idle_time_ms = idle_time * 1000

            # Update telemetry display periodically (not every frame to reduce overhead)
            telemetry_update_counter += 1
            if telemetry_update_counter >= TELEMETRY_UPDATE_INTERVAL:
                telemetry_update_counter = 0
                try:
                    telemetry_data = self._telemetry_service.collect(
                        event=event,
                        loop_time_ms=loop_time_ms,
                        idle_time_ms=idle_time_ms,
                        cycle_index=cycle_index,
                        cycle_ratio=cycle_ratio,
                        leg_positions=leg_positions,
                    )
                    self._telemetry_display.update(telemetry_data)
                except Exception as e:
                    # Don't let telemetry errors crash the robot
                    log.warning(f"Telemetry display error: {e}")

            if elapsed_time < FRAME_DURATION:
                time.sleep(FRAME_DURATION - elapsed_time)

    def _update_servo_angles(self):
        """
        Updates the servo angles based on the current keyframe in the walking cycle.
        """

        # Update walking cycle and get current position
        keyframe = self._keyframe_service.update_keyframes()
        pose = keyframe.to_pose()

        # Front Right
        self._servo_service.set_front_right_servos(
            pose.front_right.foot_angle, pose.front_right.leg_angle, pose.front_right.shoulder_angle
        )

        # Rear Left
        self._servo_service.set_rear_left_servos(
            pose.rear_left.foot_angle, pose.rear_left.leg_angle, pose.rear_left.shoulder_angle
        )

        # Front Left
        self._servo_service.set_front_left_servos(
            pose.front_left.foot_angle, pose.front_left.leg_angle, pose.front_left.shoulder_angle
        )

        # Rear Right
        self._servo_service.set_rear_right_servos(
            pose.rear_right.foot_angle, pose.rear_right.leg_angle, pose.rear_right.shoulder_angle
        )

    def body_move_pitch(self, raw_value: float):
        """
        Adjusts the robot's body pitch based on input value.

        Args:
            raw_value (float): The raw input value for pitch adjustment.
        """

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
        """
        Adjusts the robot's body roll based on input value.

        Args:
            raw_value (float): The raw input value for roll adjustment.
        """

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

    def standing_position(self):
        """
        Sets the robot to a standing position by adjusting servo angles.
        """

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
        """
        Adjusts the robot's body pitch using analog input values.

        Args:
            raw_value: The raw analog input value for pitch adjustment.
        """
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_leg_left_angle = int(self.maprange((5, -5), (180, 180), raw_value))
        self._servo_service.rear_foot_left_angle = int(self.maprange((5, -5), (10, 50), raw_value))
        self._servo_service.rear_leg_right_angle = int(self.maprange((5, -5), (0, 0), raw_value))
        self._servo_service.rear_foot_right_angle = int(self.maprange((5, -5), (170, 130), raw_value))

        self._servo_service.front_leg_left_angle = int(self.maprange((-5, 5), (160, 180), raw_value))
        self._servo_service.front_foot_left_angle = int(self.maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.front_leg_right_angle = int(self.maprange((-5, 5), (20, 0), raw_value))
        self._servo_service.front_foot_right_angle = int(self.maprange((-5, 5), (170, 130), raw_value))

    def body_move_roll_analog(self, raw_value):
        """
        Adjusts the robot's body roll using analog input values.

        Args:
            raw_value: The raw analog input value for roll adjustment.
        """
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_shoulder_left_angle = int(self.maprange((5, -5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((5, -5), (145, 35), raw_value))

        self._servo_service.front_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.front_shoulder_right_angle = int(self.maprange((-5, 5), (145, 35), raw_value))

    def body_move_height_analog(self, raw_value):
        """
        Adjusts the robot's body height using analog input values.

        Args:
            raw_value: The raw analog input value for height adjustment.
        """

        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_leg_left_angle = int(self.maprange((5, -5), (160, 180), raw_value))
        self._servo_service.rear_foot_left_angle = int(self.maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.rear_leg_right_angle = int(self.maprange((5, -5), (20, 0), raw_value))
        self._servo_service.rear_foot_right_angle = int(self.maprange((-5, 5), (170, 130), raw_value))

        self._servo_service.front_leg_left_angle = int(self.maprange((5, -5), (160, 180), raw_value))
        self._servo_service.front_foot_left_angle = int(self.maprange((-5, 5), (10, 50), raw_value))
        self._servo_service.front_leg_right_angle = int(self.maprange((5, -5), (20, 0), raw_value))
        self._servo_service.front_foot_right_angle = int(self.maprange((-5, 5), (170, 130), raw_value))

    def body_move_yaw_analog(self, raw_value):
        """
        Adjusts the robot's body yaw using analog input values.

        Args:
            raw_value: The raw analog input value for yaw adjustment.
        """
        raw_value = math.floor(raw_value * 10 / 2)

        self._servo_service.rear_shoulder_left_angle = int(self.maprange((5, -5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((5, -5), (145, 35), raw_value))

        self._servo_service.front_shoulder_left_angle = int(self.maprange((5, -5), (145, 35), raw_value))
        self._servo_service.front_shoulder_right_angle = int(self.maprange((5, -5), (145, 35), raw_value))

    def _deactivate(self):
        """
        Deactivates the robot by stopping movement, resting servos, and deactivating hardware.
        """
        self._buzzer.beep()
        self._is_activated = False
        self._is_running = False
        self._servo_service.rest_position()
        time.sleep(0.25)
        self._pca9685_board.deactivate_board()
        self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)

    def _activate(self):
        """
        Activates the robot by initializing servos, activating hardware, and setting to rest position.

        Returns:
            float: The current time to reset inactivity counter.
        """
        log.info('Press START/OPTIONS to re-enable the servos')
        self._buzzer.beep()
        self._is_activated = True
        self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ACTIVATE)
        self._pca9685_board.activate_board()
        self._servo_service = ServoService()
        time.sleep(0.25)
        self._servo_service.rest_position()
        # Reset inactivity counter on activation so timer starts now
        return time.time()

    def _handle_start_button_toggle(self, inactivity_counter):
        """
        Toggles the activation state of the robot based on the start button press.

        Args:
            inactivity_counter (float): The current inactivity counter value.

        Returns:
            float: The updated inactivity counter.
        """
        if self._is_activated:
            self._deactivate()
        else:
            inactivity_counter = self._activate()
        return inactivity_counter

    def maprange(self, from_range, to_range, value):
        """
        Maps a value from one range to another.

        Args:
            from_range (tuple): The source range as (start, end).
            to_range (tuple): The target range as (start, end).
            value: The value to map.

        Returns:
            The mapped value in the target range.
        """
        (from_start, from_end), (to_start, to_end) = from_range, to_range
        return to_start + ((value - from_start) * (to_end - to_start) / (from_end - from_start))
