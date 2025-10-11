import math
import queue
import signal
import sys
import time
from spotmicroai.motion_controller.coordinate import Coordinate
from spotmicroai.motion_controller.keyframe import KeyframeTransition
from spotmicroai.motion_controller.poses import Poses
from spotmicroai.motion_controller.servo_set import ServoSet
from spotmicroai.motion_controller.walking_cycle import WalkingCycle
import spotmicroai.utilities.queues as queues
from spotmicroai.motion_controller.pca9685 import PCA9685Board
from spotmicroai.utilities.general import General
from spotmicroai.utilities.log import Logger
from .buzzer import Buzzer
from .constants import LEG_SERVO_OFFSET, FOOT_SERVO_OFFSET, ROTATION_OFFSET, INACTIVITY_TIME
from .controller_event import ControllerEvent

log = Logger().setup_logger('Motion controller')

class MotionController:
    
    _pca9685_board: PCA9685Board
    _servos: ServoSet
    _poses: Poses
    _buzzer: Buzzer
    _walking_cycle: WalkingCycle

    _is_activated = False
    _is_running = False
    _keyframeTransition: KeyframeTransition

    _forward_factor = 0
    _max_forward_factor = 0.5
    _rotation_factor = 0.0
    _lean_factor = 0.0
    _height_factor = 1
    _walking_speed = 10

    def __init__(self, communication_queues):
        try:
            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self._pca9685_board = PCA9685Board()
            self._buzzer = Buzzer()
            self._poses = Poses()
            self._keyframeTransition = KeyframeTransition()
            self._walking_cycle = WalkingCycle()
            self._servos = ServoSet()
            
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
        self._servos.rest_position()
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
        elapsed = 0.0
        start = 0
        last_index = 0
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
                    self._servos.rest_position()
                    time.sleep(0.25)
                    self._pca9685_board.deactivate()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                else:
                    log.info('Press START/OPTIONS to re-enable the servos')
                    self._buzzer.beep()
                    self._is_activated = True
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ACTIVATE)
                    self._pca9685_board.activate()
                    time.sleep(0.25)
                    self._servos.rest_position()
                    start = time.time()
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
                    
                    self._servos.rest_position()
                    time.sleep(0.1)
                    self._pca9685_board.deactivate()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    self._is_activated = False
                    self._is_running = False
                continue

            else:
                # If there activity, reset the timer
                inactivity_counter = time.time()
            
            try:
                if self._is_running:

                    # This logic counts from 0 to 6 (length of the walking cycle)
                    elapsed += (time.time() - start) * self._walking_speed
                    elapsed = elapsed % len(self._walking_cycle.values)

                    start = time.time()
                    index = math.floor(elapsed)
                    ratio = elapsed - index

                    if last_index != index:
                        # There are 4 entries in the keyframes array, one per leg. Each contains two states, current and previous
                        # Shifting the keyframes moves the second entry into the first entry making it the 'current' state 
                        self._keyframeTransition.createNextKeyframe()

                        # Calculate Lateral Movement - Sideway movement
                        x_rot, z_rot = self.calculate_rotational_movement(index)
                        
                        current_coordinate = self._walking_cycle.values[index]
                        # Handle Front-Right and Back-Left legs first
                        # Here, we replace the second entry for each leg with newly calculated
                        x = current_coordinate.x * -self._forward_factor + x_rot
                        y = current_coordinate.y
                        z = current_coordinate.z + z_rot

                        self._keyframeTransition.current.front_right = Coordinate(x, y, z)

                        x = current_coordinate.x * -self._forward_factor - x_rot
                        y = current_coordinate.y
                        z = current_coordinate.z + z_rot
                        self._keyframeTransition.current.rear_left = Coordinate(x, y, z)

                        adjusted_index = (index + 3) % len(self._walking_cycle.values)
                        x_rot, z_rot = self.calculate_rotational_movement(adjusted_index)
                        # Handle the other two legs, Front-Left and Back-Right
                        current_coordinate = self._walking_cycle.values[adjusted_index]
                        
                        x = current_coordinate.x * -self._forward_factor - x_rot
                        y = current_coordinate.y
                        z = current_coordinate.z - z_rot
                        self._keyframeTransition.current.front_left = Coordinate(x, y, z)

                        x = current_coordinate.x * -self._forward_factor + x_rot
                        y = current_coordinate.y
                        z = current_coordinate.z - z_rot
                        self._keyframeTransition.current.rear_right = Coordinate(x, y, z)

                        last_index = index

                    # The call below interpolates the next frame. Basically, it checks what fraction of a second has elapsed since the last frame to calculate a ratio
                    # Then it uses the ratio to adjust the values of the last frame accordingly. 
                    self.interpolate_next_keyframe(ratio)

                if event[ControllerEvent.A]:
                    self._is_running = False
                    self._servos.rest_position()

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
                            self._walking_speed = min(max(self._walking_speed - 1, 0), 15)
                        else:
                            self._walking_speed = max(min(self._walking_speed + 1, 15), 0)
                    
                    # Left Thumbstick Up/Down
                    if event[ControllerEvent.LEFT_STICK_Y]:
                        self.set_forward_factor(event[ControllerEvent.LEFT_STICK_Y])
                    
                    # Left Thumbstick Left/Right
                    if event[ControllerEvent.LEFT_STICK_X]:
                        self.set_rotation_factor(event[ControllerEvent.LEFT_STICK_X])

                    # Left Thumbstick Click
                    if event[ControllerEvent.LEFT_STICK_CLICK]:
                        self._rotation_factor = 0
                        self._forward_factor = 0

                    # Right Thumbstick Up/Down
                    if event[ControllerEvent.RIGHT_STICK_Y]:
                        self.set_lean(event[ControllerEvent.RIGHT_STICK_Y])
                    # Right Thumbstick Left/Right
                    if event[ControllerEvent.RIGHT_STICK_X]:
                        self.set_height_offset(event[ControllerEvent.RIGHT_STICK_X])
                        # self.set_lean(event[ControllerEvent.RIGHT_STICK_X])
                    # Right Thumbstick Click
                    if event[ControllerEvent.RIGHT_STICK_CLICK]:
                        self.set_height_offset(0)
                        self.set_lean(0)
                else:
                    # Right Bumper
                    if self.check_event(ControllerEvent.RIGHT_BUMPER, event, prev_event):
                        # Next Pose
                        time.sleep(0.5)
                        self.handle_pose(self._poses.next)
                    # Left Bumper
                    if self.check_event(ControllerEvent.LEFT_BUMPER, event, prev_event):
                        # Prev Pose
                        time.sleep(1)
                        self.handle_pose(self._poses.previous)

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

                    start = time.time()
                    self._is_running = not self._is_running
                    time.sleep(0.5)

                self._servos.commit()

                prev_event = event
            finally:
                #continue
                pass
            elapsed_time = time.time() - frame_start
            
            if elapsed_time < FRAME_DURATION:
                time.sleep(FRAME_DURATION - elapsed_time)

    def check_event(self, key, event, prev_event):
        return key in event and event[key] != 0 and key in prev_event and prev_event[key] == 0

    def handle_pose(self, pose):
        self._servos.rear_shoulder_left_angle = pose.rear_left[0]
        self._servos.rear_leg_left_angle = pose.rear_left[1]
        self._servos.rear_foot_left_angle = pose.rear_left[2]

        self._servos.rear_shoulder_right_angle = pose.rear_right[0]
        self._servos.rear_leg_right_angle = pose.rear_right[1]
        self._servos.rear_foot_right_angle = pose.rear_right[2]

        self._servos.front_shoulder_left_angle = pose.front_left[0]
        self._servos.front_leg_left_angle = pose.front_left[1]
        self._servos.front_foot_left_angle = pose.front_left[2]

        self._servos.front_shoulder_right_angle = pose.front_right[0]
        self._servos.front_leg_right_angle = pose.front_right[1]
        self._servos.front_foot_right_angle = pose.front_right[2]

    def calculate_rotational_movement(self, index):
        # This angle calculation is only used when rotating the bot clockwise or counter clockwise
        angle = 45.0 / 180.0 * math.pi
        x_rot = math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = math.cos(angle) * self._rotation_factor * ROTATION_OFFSET

        angle = (45 + self._walking_cycle.values[index].x) / 180.0 * math.pi
        x_rot = x_rot - math.sin(angle) * self._rotation_factor * ROTATION_OFFSET
        z_rot = z_rot - math.cos(angle) * self._rotation_factor * ROTATION_OFFSET
        
        return x_rot, z_rot

    def set_forward_factor(self, factor):
        """Set forward and backward movement.

        Parameters
        ----------
        factor : float
            Positive values move forward, negative values move back. Should be in the range -1.0 - 1.0.
        """
        self._forward_factor = factor

    def set_rotation_factor(self, factor):
        """Set rotation movement.

        Parameters
        ----------
        factor : float
            Positive values rotate right, negative values rotate left. Should be in the range -1.0 - 1.0.
        """
        if self._rotation_factor >= 0 and factor >= self._rotation_factor:
            self._rotation_factor = min(self._rotation_factor + 0.025, 1)

        if self._rotation_factor > 0 and factor < 0:
            self._rotation_factor = max(self._rotation_factor - 0.025, -1)

        if self._rotation_factor < 0 and factor > 0:
            self._rotation_factor = min(self._rotation_factor + 0.025, 1)

        if self._rotation_factor < 0 and factor < self._rotation_factor:
            self._rotation_factor = max(self._rotation_factor - 0.025, -1)

    def set_lean(self, lean):
        """Set the distance that it should lean left to right.

        Parameters
        ----------
        lean : float
            Positive values lean right, negative values lean left. Should be in the range -1.0 - 1.0.
        """
        self._lean_factor = lean * 50

    def set_height_offset(self, height):
        """Set the extra distance for the chassis to be off the ground.

        Parameters
        ----------
        height : float
            Should be in the range 0.0-1.0.
        """
        self._height_factor = height * 40

    def interpolate_next_keyframe(self, ratio):
        """Interpolate between the current and next keyframes for each leg and apply the servo positions.

        Parameters
        ----------
        ratio : float
            The ratio of each keyframe in the interpolation. Should be in the range 0.0-1.0.
        """
        # Front Right
        start_coord = Coordinate(self._keyframeTransition.previous.front_right.x, self._keyframeTransition.previous.front_right.y + self._height_factor, self._keyframeTransition.previous.front_right.z - self._lean_factor)
        end_coord = Coordinate(self._keyframeTransition.current.front_right.x, self._keyframeTransition.current.front_right.y + self._height_factor, self._keyframeTransition.current.front_right.z - self._lean_factor)
        foot, leg, shoulder = start_coord.interpolate_to(end_coord, ratio).inverse_kinematics()
        self.front_right_leg(foot, leg, shoulder)

        # Rear Left
        start_coord = Coordinate(self._keyframeTransition.previous.rear_left.x, self._keyframeTransition.previous.rear_left.y + self._height_factor, self._keyframeTransition.previous.rear_left.z + self._lean_factor)
        end_coord = Coordinate(self._keyframeTransition.current.rear_left.x, self._keyframeTransition.current.rear_left.y + self._height_factor, self._keyframeTransition.current.rear_left.z + self._lean_factor)
        foot, leg, shoulder = start_coord.interpolate_to(end_coord, ratio).inverse_kinematics()
        self.rear_left_leg(foot, leg, shoulder)

        # Front Left
        start_coord = Coordinate(self._keyframeTransition.previous.front_left.x, self._keyframeTransition.previous.front_left.y + self._height_factor, self._keyframeTransition.previous.front_left.z + self._lean_factor)
        end_coord = Coordinate(self._keyframeTransition.current.front_left.x, self._keyframeTransition.current.front_left.y + self._height_factor, self._keyframeTransition.current.front_left.z + self._lean_factor)
        foot, leg, shoulder = start_coord.interpolate_to(end_coord, ratio).inverse_kinematics()
        self.front_left_leg(foot, leg, shoulder)

        # Rear Right
        start_coord = Coordinate(self._keyframeTransition.previous.rear_right.x, self._keyframeTransition.previous.rear_right.y + self._height_factor, self._keyframeTransition.previous.rear_right.z - self._lean_factor)
        end_coord = Coordinate(self._keyframeTransition.current.rear_right.x, self._keyframeTransition.current.rear_right.y + self._height_factor, self._keyframeTransition.current.rear_right.z - self._lean_factor)
        foot, leg, shoulder = start_coord.interpolate_to(end_coord, ratio).inverse_kinematics()
        self.rear_right_leg(foot, leg, shoulder)

    def rear_left_leg(self, foot, leg, shoulder):
        """Helper function for setting servo angles for the back left leg.

        Parameters
        ----------
        foot : float
            Servo angle for foot in degrees.
        leg : float
            Servo angle for leg in degrees.
        shoulder : float
            Servo angle for shoulder in degrees.
        """
        self._servos.rear_shoulder_left_angle = shoulder
        self._servos.rear_leg_left_angle = min(leg + LEG_SERVO_OFFSET, 180)
        self._servos.rear_foot_left_angle = max(foot - FOOT_SERVO_OFFSET, 0)

    def rear_right_leg(self, foot, leg, shoulder):
        """Helper function for setting servo angles for the back right leg.

        Parameters
        ----------
        foot : float
            Servo angle for foot in degrees.
        leg : float
            Servo angle for leg in degrees.
        shoulder : float
            Servo angle for shoulder in degrees.
        """
        self._servos.rear_shoulder_right_angle = 180 - shoulder
        self._servos.rear_leg_right_angle = max(180 - (leg + LEG_SERVO_OFFSET), 0)
        self._servos.rear_foot_right_angle = 180 - max(foot - FOOT_SERVO_OFFSET, 0)

    def front_left_leg(self, foot, leg, shoulder):
        """Helper function for setting servo angles for the front left leg.

        Parameters
        ----------
        foot : float
            Servo angle for foot in degrees.
        leg : float
            Servo angle for leg in degrees.
        shoulder : float
            Servo angle for shoulder in degrees.
        """
        self._servos.front_shoulder_left_angle = 180 - shoulder
        self._servos.front_leg_left_angle = min(leg + LEG_SERVO_OFFSET, 180)
        self._servos.front_foot_left_angle = max(foot - FOOT_SERVO_OFFSET, 0)

    def front_right_leg(self, foot, leg, shoulder):
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
        self._servos.front_shoulder_right_angle = shoulder
        self._servos.front_leg_right_angle = max(180 - (leg + LEG_SERVO_OFFSET), 0)
        self._servos.front_foot_right_angle = 180 - max(foot - FOOT_SERVO_OFFSET, 0)

    def body_move_pitch(self, raw_value):

        leg_increment = 10
        foot_increment = 15

        if raw_value < 0:
            self._servos.rear_leg_left_angle -= leg_increment
            self._servos.rear_foot_left_angle += foot_increment
            self._servos.rear_leg_right_angle += leg_increment
            self._servos.rear_foot_right_angle -= foot_increment
            self._servos.front_leg_left_angle -= leg_increment
            self._servos.front_foot_left_angle += foot_increment
            self._servos.front_leg_right_angle += leg_increment
            self._servos.front_foot_right_angle -= foot_increment

        elif raw_value > 0:
            self._servos.rear_leg_left_angle += leg_increment
            self._servos.rear_foot_left_angle -= foot_increment
            self._servos.rear_leg_right_angle -= leg_increment
            self._servos.rear_foot_right_angle += foot_increment
            self._servos.front_leg_left_angle += leg_increment
            self._servos.front_foot_left_angle -= foot_increment
            self._servos.front_leg_right_angle -= leg_increment
            self._servos.front_foot_right_angle += foot_increment


        else:
            self._servos.rest_position()

    def body_move_roll(self, raw_value):

        range = 1

        if raw_value < 0:
            self._servos.rear_shoulder_left_angle = max(self._servos.rear_shoulder_left_angle - range, 0)
            self._servos.rear_shoulder_right_angle = max(self._servos.rear_shoulder_right_angle - range, 0)
            self._servos.front_shoulder_left_angle = min(self._servos.front_shoulder_left_angle + range, 180)
            self._servos.front_shoulder_right_angle = min(self._servos.front_shoulder_right_angle + range, 180)

        elif raw_value > 0:
            self._servos.rear_shoulder_left_angle = min(self._servos.rear_shoulder_left_angle + range, 180)
            self._servos.rear_shoulder_right_angle = min(self._servos.rear_shoulder_right_angle + range, 180)
            self._servos.front_shoulder_left_angle = max(self._servos.front_shoulder_left_angle - range, 0)
            self._servos.front_shoulder_right_angle = max(self._servos.front_shoulder_right_angle - range, 0)

        else:
            self._servos.rest_position()

    def standing_position(self):

        variation_leg = 30
        variation_foot = 50

        self._servos.rear_shoulder_left_angle += 10
        self._servos.rear_leg_left_angle -= variation_leg
        self._servos.rear_foot_left_angle += variation_foot

        self._servos.rear_shoulder_right_angle -= 10
        self._servos.rear_leg_right_angle += variation_leg
        self._servos.rear_foot_right_angle -= variation_foot

        time.sleep(0.05)

        self._servos.front_shoulder_left_angle -= 10
        self._servos.front_leg_left_angle -= variation_leg - 5
        self._servos.front_foot_left_angle += variation_foot - 5

        self._servos.front_shoulder_right_angle += 10
        self._servos.front_leg_right_angle += variation_leg + 5
        self._servos.front_foot_right_angle -= variation_foot + 5

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

        self._servos.rear_leg_left_angle = int(General().maprange((5, -5), (180, 180), raw_value))
        self._servos.rear_foot_left_angle = int(General().maprange((5, -5), (10, 50), raw_value))
        self._servos.rear_leg_right_angle = int(General().maprange((5, -5), (0, 0), raw_value))
        self._servos.rear_foot_right_angle = int(General().maprange((5, -5), (170, 130), raw_value))

        self._servos.front_leg_left_angle = int(General().maprange((-5, 5), (160, 180), raw_value))
        self._servos.front_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servos.front_leg_right_angle = int(General().maprange((-5, 5), (20, 0), raw_value))
        self._servos.front_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_roll_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servos.rear_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servos.rear_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        
        self._servos.front_shoulder_left_angle = int(General().maprange((-5, 5), (145, 35), raw_value))
        self._servos.front_shoulder_right_angle = int(General().maprange((-5, 5), (145, 35), raw_value))

    def body_move_height_analog(self, raw_value):

        raw_value = math.floor(raw_value * 10 / 2)

        self._servos.rear_leg_left_angle = int(General().maprange((5, -5), (160, 180), raw_value))
        self._servos.rear_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servos.rear_leg_right_angle = int(General().maprange((5, -5), (20, 0), raw_value))
        self._servos.rear_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

        self._servos.front_leg_left_angle = int(General().maprange((5, -5), (160, 180), raw_value))
        self._servos.front_foot_left_angle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self._servos.front_leg_right_angle = int(General().maprange((5, -5), (20, 0), raw_value))
        self._servos.front_foot_right_angle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_yaw_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self._servos.rear_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servos.rear_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        
        self._servos.front_shoulder_left_angle = int(General().maprange((5, -5), (145, 35), raw_value))
        self._servos.front_shoulder_right_angle = int(General().maprange((5, -5), (145, 35), raw_value))