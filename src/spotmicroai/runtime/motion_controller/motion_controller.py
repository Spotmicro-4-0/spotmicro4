import math
import queue
import signal
import sys
import time

from spotmicroai import labels
import spotmicroai.constants as constants
from spotmicroai.hardware.servo.servo_service import ServoService
from spotmicroai.logger import Logger
from spotmicroai.runtime.controller_event import ControllerEvent
from spotmicroai.runtime.messaging import LcdMessage, MessageAbortCommand, MessageBus, MessageTopic, MessageTopicStatus
from spotmicroai.runtime.motion_controller.filtered_controller_event import FilteredControllerEvent
from spotmicroai.runtime.motion_controller.services import KeyframeService, PoseService, TelemetryService
from spotmicroai.singleton import Singleton

log = Logger().setup_logger('Motion controller')


class MotionController(metaclass=Singleton):
    """
    Controls the motion of the SpotMicro robot, handling servo movements, pose adjustments,
    and responding to controller inputs for walking, standing, and other actions.
    """

    _servo_service: ServoService
    _pose_service: PoseService
    _filtered_controller_event: FilteredControllerEvent

    _is_activated = False
    _is_running = False
    _keyframe_service: KeyframeService
    _telemetry_service: TelemetryService

    def __init__(self):
        """
        Initializes the MotionController with necessary services and queues.

        Args:
            communication_queues (dict): Dictionary of queues for inter-controller communication.
        """
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._servo_service = ServoService()
            self._pose_service = PoseService()
            self._keyframe_service = KeyframeService()
            self._filtered_controller_event = FilteredControllerEvent()

            # Initialize telemetry system
            self._telemetry_service = TelemetryService(self)

            self.prev_pitch_input: float | None = None
            self.prev_pitch_analog: float | None = None

            message_bus = MessageBus()
            self._motion_topic = message_bus.motion
            self._abort_topic = message_bus.abort
            self._lcd_topic = message_bus.lcd
            # self._telemetry_topic = message_bus.telemetry

            self._lcd_topic.put(LcdMessage(MessageTopic.MOTION, MessageTopicStatus.OK))

            time.sleep(constants.DEFAULT_SLEEP)

        except Exception as e:
            log.error(labels.MOTION_INIT_PROBLEM, e)
            self._lcd_topic.put(LcdMessage(MessageTopic.MOTION, MessageTopicStatus.OK))
            sys.exit(1)

    def exit_gracefully(self, _signum, _frame):
        """
        Handles graceful shutdown on signal reception, moving servos to rest and deactivating hardware.
        """
        log.info(labels.MOTION_GRACEFUL_SHUTDOWN)

        # Move servos to neutral (rest) first
        self._servo_service.rest_position()
        time.sleep(0.3)

        self._servo_service.deactivate_servos()

        self._abort_topic.put(MessageAbortCommand.ABORT)
        self._is_activated = False
        log.info(labels.MOTION_TERMINATED)
        sys.exit(0)

    def do_process_events_from_queues(self) -> None:
        """
        Main event processing loop that handles controller inputs, updates servo positions,
        manages activation states, and updates telemetry.
        """

        # State Variables
        inactivity_counter = time.time()

        raw_event: ControllerEvent | None = None
        self._filtered_controller_event = FilteredControllerEvent()

        # Telemetry variables
        cycle_index = None
        cycle_ratio = None
        leg_positions = None

        iteration_window_start = time.time()
        iteration_time_accumulator = 0.0
        iteration_samples = 0

        while True:
            frame_start = time.time()

            try:
                raw_event = self._motion_topic.get(block=False)
            except queue.Empty:
                raw_event = None

            # Filter the raw event through debouncing and smoothing
            if raw_event is not None:
                self._filtered_controller_event.update(raw_event)

            # Handle START button with debouncing
            if self._filtered_controller_event.start:
                inactivity_counter = self._handle_start_button_toggle(inactivity_counter)

            if not self._is_activated:
                time.sleep(0.1)
                continue

            # Get filtered event reference for cleaner code
            filtered_event = self._filtered_controller_event

            # Check if there's any user input activity
            has_input = filtered_event.has_activity()

            if not has_input:
                # if there is no user input, check to see if it have been long enough to warn the user
                if (time.time() - inactivity_counter) >= constants.INACTIVITY_TIME:
                    log.info(labels.MOTION_INACTIVITY_WARNING.format(constants.INACTIVITY_TIME))
                    log.info(labels.MOTION_SHUTDOWN_SERVOS)
                    log.info(labels.MOTION_PRESS_START_ENABLE)
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

                if filtered_event.a:
                    self._is_running = False
                    self._servo_service.rest_position()

                # Handle cases when robot is running
                if self._is_running:
                    # Right Trigger
                    # if filtered_event.right_trigger:
                    # Left Trigger
                    # if filtered_event.left_trigger:

                    if filtered_event.y:
                        pass

                    if filtered_event.b:
                        pass

                    if filtered_event.x:
                        pass

                    # D-Pad Left/Right
                    if filtered_event.dpad_horizontal != 0:
                        pass
                    # D-Pad Up/Down
                    if filtered_event.dpad_vertical != 0:
                        if filtered_event.dpad_vertical > 0:
                            self._keyframe_service.adjust_walking_speed(-1)
                        else:
                            self._keyframe_service.adjust_walking_speed(1)

                    # Left Thumbstick Up/Down
                    if filtered_event.left_stick_y != 0:
                        self._keyframe_service.set_forward_factor(filtered_event.left_stick_y)

                    # Left Thumbstick Left/Right
                    if filtered_event.left_stick_x != 0:
                        self._keyframe_service.set_rotation_factor(filtered_event.left_stick_x)

                    # Left Thumbstick Click
                    if filtered_event.left_stick_click:
                        self._keyframe_service.reset_movement()

                    # Right Thumbstick Up/Down
                    if filtered_event.right_stick_y != 0:
                        self._keyframe_service.set_lean(filtered_event.right_stick_y)
                    # Right Thumbstick Left/Right
                    if filtered_event.right_stick_x != 0:
                        self._keyframe_service.set_height_offset(filtered_event.right_stick_x)
                    # Right Thumbstick Click
                    if filtered_event.right_stick_click:
                        self._keyframe_service.reset_body_adjustments()
                else:
                    # Right Bumper
                    if filtered_event.right_bumper:
                        # Next Pose
                        time.sleep(0.5)
                        next_pose = self._pose_service.next()
                        self._servo_service.set_pose(next_pose)
                    # Left Bumper
                    if filtered_event.left_bumper:
                        # Prev Pose
                        time.sleep(0.5)
                        prev_pose = self._pose_service.previous()
                        self._servo_service.set_pose(prev_pose)

                    if filtered_event.dpad_vertical != 0:
                        self.body_move_pitch(filtered_event.dpad_vertical)

                    if filtered_event.dpad_horizontal != 0:
                        self.body_move_roll(filtered_event.dpad_horizontal)

                    if filtered_event.left_stick_y != 0:
                        self.body_move_pitch_analog(filtered_event.left_stick_y)

                    if filtered_event.left_stick_x != 0:
                        self.body_move_roll_analog(filtered_event.left_stick_x)

                    if filtered_event.right_stick_y != 0:
                        self.body_move_yaw_analog(filtered_event.right_stick_y)

                    if filtered_event.right_stick_x != 0:
                        self.body_move_height_analog(filtered_event.right_stick_x)

                    # if filtered_event.y:
                    #     self.standing_position()

                    # if filtered_event.b:
                    #     self.handle_instinct(self._instincts['pushUp'])

                    # if filtered_event.x:
                    #     self.handle_instinct(self._instincts['sit'])

                    # if filtered_event.y:
                    #     self.handle_instinct(self._instincts['sleep'])

                # Handle BACK button (walking toggle) with debouncing
                if filtered_event.back:
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
            idle_time = max(constants.FRAME_DURATION - elapsed_time, 0)
            loop_time_ms = elapsed_time * 1000
            idle_time_ms = idle_time * 1000

            # Publish telemetry (service handles throttling and queue stats internally)
            self._telemetry_service.publish(
                event=filtered_event.value if has_input else None,
                loop_time_ms=loop_time_ms,
                idle_time_ms=idle_time_ms,
                cycle_index=cycle_index,
                cycle_ratio=cycle_ratio,
                leg_positions=leg_positions,
            )

            if elapsed_time < constants.FRAME_DURATION:
                time.sleep(constants.FRAME_DURATION - elapsed_time)

            iteration_end = time.time()
            iteration_duration = iteration_end - frame_start
            iteration_time_accumulator += iteration_duration
            iteration_samples += 1

            if (iteration_end - iteration_window_start) >= 1.0 and iteration_samples > 0:
                avg_iteration_duration = iteration_time_accumulator / iteration_samples
                avg_iteration_frequency = 1.0 / avg_iteration_duration if avg_iteration_duration > 0 else 0.0
                log.info(
                    "Motion loop avg iteration time: %.2f ms (%.2f Hz)",
                    avg_iteration_duration * 1000,
                    avg_iteration_frequency,
                )
                iteration_window_start = iteration_end
                iteration_time_accumulator = 0.0
                iteration_samples = 0

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
        # --- Initialize on first call to avoid startup jerk ---
        prev = getattr(self, "prev_pitch_input", None)
        if prev is None:
            self.prev_pitch_input = raw_value
            return

        # --- Smooth input ---
        alpha = 0.1  # tuning factor (0.05 = smoother, 0.2 = quicker)
        smoothed_value = prev + alpha * (raw_value - prev)
        self.prev_pitch_input = smoothed_value

        # --- Apply deadzone ---
        if abs(smoothed_value) < 0.05:
            # self._servo_service.rest_position()
            return

        # --- Optional exponential response for fine control near center ---
        scaled = math.copysign(abs(smoothed_value) ** 1.5, smoothed_value)

        # --- Scale increments ---
        leg_increment = 10 * scaled
        foot_increment = 15 * scaled

        # --- Apply pitch adjustments using direction directly ---
        self._servo_service.rear_leg_left_angle += leg_increment
        self._servo_service.rear_foot_left_angle -= foot_increment
        self._servo_service.rear_leg_right_angle -= leg_increment
        self._servo_service.rear_foot_right_angle += foot_increment
        self._servo_service.front_leg_left_angle += leg_increment
        self._servo_service.front_foot_left_angle -= foot_increment
        self._servo_service.front_leg_right_angle -= leg_increment
        self._servo_service.front_foot_right_angle += foot_increment

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

    def body_move_pitch_analog(self, raw_value: float):
        """
        Smoothly adjusts the robot's body pitch based on analog input,
        without forcing servos back to center when the stick returns to zero.
        """

        # --- Tunable parameters ---
        INPUT_SCALE = 3.5  # smaller = less sensitive
        RESPONSE_CURVE = 1.4  # >1.0 softens center response
        ALPHA = 0.1  # lower = smoother, higher = quicker

        # --- Unified servo angle mapping (only used for motion delta) ---
        # Using symmetric ranges so positive and negative inputs are mirror images
        ANGLE_RANGES = {
            "leg": (-10, 10),  # Symmetric: ±10 degrees
            "foot": (-5, 5),  # Symmetric: ±5 degrees
        }

        # --- Initialize previous value on first call to avoid startup jerk ---
        prev = getattr(self, "prev_pitch_analog", None)
        if prev is None:
            self.prev_pitch_analog = raw_value
            return

        # --- Smooth input using exponential moving average ---
        smoothed_value = prev + ALPHA * (raw_value - prev)
        self.prev_pitch_analog = smoothed_value

        # --- Nonlinear response (for softer control near center) ---
        curved = math.copysign(abs(smoothed_value) ** RESPONSE_CURVE, smoothed_value)

        # --- Scale to motion range (-INPUT_SCALE to +INPUT_SCALE) ---
        mapped_input = curved * INPUT_SCALE

        # --- Compute incremental motion instead of absolute centering ---
        leg_delta = self.maprange((-INPUT_SCALE, INPUT_SCALE), ANGLE_RANGES["leg"], mapped_input)
        foot_delta = self.maprange((-INPUT_SCALE, INPUT_SCALE), ANGLE_RANGES["foot"], mapped_input)

        # Apply small deltas to current angles (accumulative motion)
        self._servo_service.front_leg_left_angle += leg_delta
        self._servo_service.front_foot_left_angle += foot_delta

        self._servo_service.front_leg_right_angle += leg_delta
        self._servo_service.front_foot_right_angle += foot_delta

        self._servo_service.rear_leg_left_angle += leg_delta
        self._servo_service.rear_foot_left_angle += foot_delta

        self._servo_service.rear_leg_right_angle += leg_delta
        self._servo_service.rear_foot_right_angle += foot_delta

    def body_move_roll_analog(self, raw_value):
        """
        Adjusts the robot's body roll using analog input values.

        Args:
            raw_value: The raw analog input value for roll adjustment.
        """
        raw_value = math.floor(raw_value * 10 / 2)

        # Roll: left and right shoulders move opposite
        self._servo_service.front_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))

        self._servo_service.front_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))

    def body_move_height_analog(self, raw_value):
        """
        Adjusts the robot's body height using analog input values.

        Args:
            raw_value: The raw analog input value for height adjustment.
        """

        raw_value = math.floor(raw_value * 10 / 2)

        # Raise/lower body equally on all legs
        for name in ["front_leg_left_angle", "rear_leg_left_angle", "front_leg_right_angle", "rear_leg_right_angle"]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (180, 20), raw_value)))

        for name in [
            "front_foot_left_angle",
            "rear_foot_left_angle",
            "front_foot_right_angle",
            "rear_foot_right_angle",
        ]:
            setattr(self._servo_service, name, int(self.maprange((-5, 5), (130, 170), raw_value)))

    def body_move_yaw_analog(self, raw_value):
        """
        Adjusts the robot's body yaw using analog input values.

        Args:
            raw_value: The raw analog input value for yaw adjustment.
        """
        raw_value = math.floor(raw_value * 10 / 2)

        # Yaw: diagonal shoulders move opposite
        self._servo_service.front_shoulder_left_angle = int(self.maprange((-5, 5), (35, 145), raw_value))
        self._servo_service.rear_shoulder_right_angle = int(self.maprange((-5, 5), (35, 145), raw_value))

        self._servo_service.front_shoulder_right_angle = int(self.maprange((-5, 5), (145, 35), raw_value))
        self._servo_service.rear_shoulder_left_angle = int(self.maprange((-5, 5), (145, 35), raw_value))

    def _deactivate(self):
        """
        Deactivates the robot by stopping movement, resting servos, and deactivating hardware.
        """
        self._is_activated = False
        self._is_running = False
        self._servo_service.rest_position()
        time.sleep(0.25)
        self._servo_service.deactivate_servos()
        self._abort_topic.put(MessageAbortCommand.ABORT)

    def _activate(self):
        """
        Activates the robot by initializing servos, activating hardware, and setting to rest position.

            Returns:
            float: The current time to reset inactivity counter.
        """
        log.info(labels.MOTION_REACTIVATE_SERVOS)
        self._is_activated = True
        self._abort_topic.put(MessageAbortCommand.ACTIVATE)
        self._servo_service.activate_servos()
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
