#region Standard Dependencies Imports
from enum import Enum
import math
import queue
import signal
import sys
import busio  # type: ignore
from board import SCL, SDA  # type: ignore
from adafruit_pca9685 import PCA9685  # type: ignore
from adafruit_motor import servo  # type: ignore
import RPi.GPIO as GPIO  # type: ignore
import time
from spotmicroai.motion_controller.InverseKinematics import InverseKinematics, interpolate
from spotmicroai.motion_controller.models import Coordinate, Instinct, Keyframe, KeyframeCollection, ServoConfigurations, ServoConfigurationsCollection, ServoConfigurationsForLimb, ServoStateCollection, ServoStateForLimb
from spotmicroai.utilities.log import Logger
from spotmicroai.utilities.config import Config
import spotmicroai.utilities.queues as queues
from spotmicroai.utilities.general import General

#endregion

log = Logger().setup_logger('Motion controller')

#############################################
class MotionController:
    
    #############################################
    #region Enum Declarations
    class GaitType(Enum):
        # Enum difinition for the available gaits
        Walk = 0
        Trot = 1
        Pace = 2
        Hop = 3
        Lope = 4
        Gallop = 5
        Spanish = 6

    class JointType(Enum):
        Shoulder = 0
        Leg = 1
        Foot = 2

    #endregion

    #############################################
    #region PCA9685 Board Variables
    boards = 1
    i2c = None
    pca9685_1 = None
    pca9685_2 = None

    pca9685_1_address = None
    pca9685_1_reference_clock_speed = None
    pca9685_1_frequency = None
    pca9685_2_address = None
    pca9685_2_reference_clock_speed = None
    pca9685_2_frequency = None
    #endregion

    #############################################
    #region Servo Variables
    servos_configurations = ServoConfigurationsCollection
    servos = ServoStateCollection
    #endregion'

    #############################################
    #region Buzzer Variables
    buzzer_pin = None
    #endregion'

    #############################################
    #region Motion Keyframe Variables
    _is_activated = False

    _is_running = False
    _current_gait_type = 0
    _current_instinct_type = 0
    _keyframes = []
    instincts = None

    _forward_factor = 0
    _max_forward_factor = 0.5
    _rotation_factor = 0.0
    _lean_factor = 0.0
    _height_factor = 1
    _gait_speed = 10
    _event = {}
    _prev_event = {}

    LEG_SERVO_OFFSET = 120
    FOOT_SERVO_OFFSET = 0
    ROTATION_OFFSET = 40

    # This represents the number of seconds in which if no activity is detected, the robot shuts down
    INACTIVITY_TIME = 10
    #endregion

    def __init__(self, communication_queues):

        try:
            print('Starting controller...')

            signal.signal(signal.SIGINT, self.exit_gracefully)
            signal.signal(signal.SIGTERM, self.exit_gracefully)

            self.i2c = busio.I2C(SCL, SDA)
            self.load_pca9685_boards_configuration()
            self.load_servos_configuration()

            self._abort_queue = communication_queues[queues.ABORT_CONTROLLER]
            self._motion_queue = communication_queues[queues.MOTION_CONTROLLER]
            self._lcd_screen_queue = communication_queues[queues.LCD_SCREEN_CONTROLLER]

            if self.pca9685_2_address:
                self._lcd_screen_queue.put('motion_controller_1 OK')
                self._lcd_screen_queue.put('motion_controller_2 OK')
            else:
                self._lcd_screen_queue.put('motion_controller_1 OK')
                self._lcd_screen_queue.put('motion_controller_2 NOK')

            self.init_keyframes()
            self.setup_buzzer()

        except Exception as e:
            log.error('Motion controller initialization problem', e)
            self._lcd_screen_queue.put('motion_controller_1 NOK')
            self._lcd_screen_queue.put('motion_controller_2 NOK')
            try:
                self.pca9685_1.deinit()
            finally:
                try:
                    if self.boards == 2:
                        self.pca9685_2.deinit()
                finally:
                    sys.exit(1)

    def exit_gracefully(self, signum, frame):
        try:
            time.sleep(0.25)
            self.deactivate_pca9685_boards()
            self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
            self._is_activated = False
        finally:
            try:
                if self.boards == 2:
                    self.pca9685_2.deinit()
            finally:
                log.info('Terminated')
                sys.exit(0)

    def init_keyframes(self):   
        self._keyframes = KeyframeCollection(Keyframe(Coordinate(0, 150, 0), Coordinate(0, 150, 0)), 
                                             Keyframe(Coordinate(0, 150, 0), Coordinate(0, 150, 0)), 
                                             Keyframe(Coordinate(0, 150, 0), Coordinate(0, 150, 0)), 
                                             Keyframe(Coordinate(0, 150, 0), Coordinate(0, 150, 0)))

    def do_process_events_from_queues(self):

        # State Variables
        elapsed = 0.0
        gait = self.load_gait_from_config()
        self.instincts = self.load_instincts_from_config()
        start = 0
        last_index = 0
        inactivity_counter = time.time()
        log.info('Press START/OPTIONS to enable the servos')

        activate_debounce_time = 0
        gait_debounce_time = 0

        while True:
            ########################################################################
            #region Handle reading events
            try:
                self._event = self._motion_queue.get(block=False)

            except queue.Empty:
                self._event = {}
            #endregion
            
            ########################################################################
            #region Handle start/stop events
            if 'start' in self._event and self._event['start'] == 1:
                if time.time() - activate_debounce_time < 1:
                    continue
                else:
                    activate_debounce_time = time.time()

                if self._is_activated:
                    self.beep()
                    self.rest_position()
                    time.sleep(0.25)
                    self.deactivate_pca9685_boards()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    self._is_activated = False
                else:
                    log.info('Press START/OPTIONS to re-enable the servos')
                    self.beep()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ACTIVATE)
                    self.activate_pca9685_boards()
                    self.activate_servos()
                    self.rest_position()
                    start = time.time()
                    # Reset inactivity counter on activation so timer starts now
                    inactivity_counter = time.time()
                    self._is_activated = True
            #endregion

            ########################################################################
            #region Check for inactivity
            if not self._is_activated:
                time.sleep(0.1)
                continue

            if self._event == {}:
                # if there is no user input, check to see if it have been long enough to warn the user
                if (time.time() - inactivity_counter) >= self.INACTIVITY_TIME:
                    log.info(f'Inactivity lasted {self.INACTIVITY_TIME} seconds. Press start to reactivate')
                    log.info('Shutting down the servos.')
                    log.info('Press START/OPTIONS to enable the servos')
                    
                    self.rest_position()
                    time.sleep(0.1)
                    self.deactivate_pca9685_boards()
                    self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                    self._is_activated = False
                    self._is_running = False
                continue

            else:
                # If there activity, reset the timer
                inactivity_counter = time.time()
            #endregion

            ########################################################################
            #region Handle Keyframe kinematics
            try:
                if self._is_running:

                    # This logic counts from 0 to 6 (length of the gait array)
                    elapsed += (time.time() - start) * self._gait_speed
                    elapsed = elapsed % len(gait)

                    start = time.time()
                    index = math.floor(elapsed)
                    ratio = elapsed - index

                    if last_index != index:
                        # There are 4 entries in the keyframes array, one per leg. Each contains two states, current and previous
                        # Shifting the keyframes moves the second entry into the first entry making it the 'current' state 
                        self._shift_keyframes()

                        # Calculate Lateral Movement - Sideway movement
                        x_rot, z_rot = self.calculate_rotational_movement(gait, index)
                        
                        # Handle Front-Right and Back-Left legs first
                        # Here, we replace the second entry for each leg with newly calculated
                        x = gait[index].x * -self._forward_factor + x_rot
                        y = gait[index].y
                        z = gait[index].z + z_rot

                        self._keyframes.frontRight.current = Coordinate(x, y, z)

                        x = gait[index].x * -self._forward_factor - x_rot
                        y = gait[index].y
                        z = gait[index].z + z_rot
                        # if (self._current_gait_type == self.GaitType.Walk.value):
                        self._keyframes.backLeft.current = Coordinate(x, y, z)
                        # else:
                        #     self._keyframes.backRight.current = Coordinate(x, y, z)

                        # Handle the other two legs, Front-Left and Back-Right
                        adjusted_index = (index + 3) % len(gait)
                        x_rot, z_rot = self.calculate_rotational_movement(gait, adjusted_index)
                        
                        x = gait[adjusted_index].x * -self._forward_factor - x_rot
                        y = gait[adjusted_index].y
                        z = gait[adjusted_index].z - z_rot
                        self._keyframes.frontLeft.current = Coordinate(x, y, z)

                        x = gait[adjusted_index].x * -self._forward_factor + x_rot
                        y = gait[adjusted_index].y
                        z = gait[adjusted_index].z - z_rot
                        # if (self._current_gait_type == self.GaitType.Walk.value):
                        self._keyframes.backRight.current = Coordinate(x, y, z)
                        # else:
                        #     self._keyframes.backLeft.current = Coordinate(x, y, z)

                        last_index = index

                    # The call below interpolates the next frame. Basically, it checks what fraction of a second has elapsed since the last frame to calculate a ratio
                    # Then it uses the ratio to adjust the values of the last frame accordingly. 
                    self.interpolateKeyframes(ratio)

            #endregion  
            
                ########################################################################
                #region Handle Key presses

                if self._event['a']:
                    self._is_running = False
                    self.rest_position()

                # Handle cases when robot is running
                if self._is_running:
                    # Right Trigger
                    # if self.check_event('gas'):
                    #     self._current_gait_type = 0
                    # Left Trigger
                    # if self.check_event('brake'):
                    #     self._current_gait_type = 0
                    
                    if self.check_event('y'):
                        self._current_gait_type = self.GaitType.Walk.value

                    if self.check_event('b'):
                        self._current_gait_type = self.GaitType.Trot.value

                    if self.check_event('x'):
                        self._current_gait_type = self.GaitType.Hop.value

                    # D-Pad Left/Right
                    if self.check_event('hat0x'):
                        pass                
                    # D-Pad Up/Down
                    if self.check_event('hat0y'):
                        if self._event['hat0y'] > 0:
                            self._gait_speed = min(max(self._gait_speed - 1, 0), 15)
                        else:
                            self._gait_speed = max(min(self._gait_speed + 1, 15), 0)
                    
                    # Left Thumbstick Up/Down
                    if self._event['ly']:
                        self.set_forward_factor(self._event['ly'])
                    
                    # Left Thumbstick Left/Right
                    if self._event['lx']:
                        self.set_rotation_factor(self._event['lx'])

                    # Left Thumbstick Click
                    if self._event['thumbl']:
                        self._rotation_factor = 0
                        self._forward_factor = 0

                    # Right Thumbstick Up/Down
                    if self._event['lz']:
                        self.set_lean(self._event['lz'])
                    # Right Thumbstick Left/Right
                    if self._event['rz']:
                        self.set_height_offset(self._event['rz'])
                        # self.set_lean(self._event['rz'])
                    # Right Thumbstick Click
                    if self._event['thumbr']:
                        self.set_height_offset(0)
                        self.set_lean(0)
                else:
                    # Right Bumper
                    if self.check_event('tr'):
                        # Next Instinct
                        self._current_instinct_type = abs((self._current_instinct_type + 1) % len(self.instincts))
                        time.sleep(1)
                        self.handle_instinct(self.instincts[self._current_instinct_type])
                    # Left Bumper
                    if self.check_event('tl'):
                        # Prev Instinct
                        self._current_instinct_type = abs((self._current_instinct_type - 1) % len(self.instincts))
                        time.sleep(1)
                        self.handle_instinct(self.instincts[self._current_instinct_type])

                    if self._event['hat0y']:
                        self.body_move_pitch(self._event['hat0y'])

                    if self._event['hat0x']:
                        self.body_move_roll(self._event['hat0x'])

                    if self._event['ly']:
                        self.body_move_pitch_analog(self._event['ly'])

                    if self._event['lx']:
                        self.body_move_roll_analog(self._event['lx'])

                    if self._event['lz']:
                        self.body_move_yaw_analog(self._event['lz'])

                    if self._event['rz']:
                        self.body_move_height_analog(self._event['rz'])

                    # if self._event['y']:
                    #     self.standing_position()

                    # if self._event['b']:
                    #     self.handle_instinct(self._instincts['pushUp'])

                    # if self._event['x']:
                    #     self.handle_instinct(self._instincts['sit'])
                    
                    # if self._event['y']:
                    #     self.handle_instinct(self._instincts['sleep'])
                    
                    self.move()

                if self._event['select'] == 1:
                    if time.time() - gait_debounce_time < 1:
                        continue
                    else:
                        gait_debounce_time = time.time()

                    start = time.time()
                    self._is_running = not self._is_running
                    time.sleep(0.5)

                self._prev_event = self._event
            finally:
                #continue
                pass
            #endregion

    def load_gait_from_config(self):
        raw_gait = Config().get(Config.GAIT_KEYFRAMES)
        gait = []

        for keyframe in raw_gait:
            gait.append(Coordinate(keyframe[0], keyframe[1], keyframe[2]))
        
        return gait
    
    def load_instincts_from_config(self):
        instincts_config = Config().get(Config.INSTINCTS_KEYFRAMES)
        result = []
        for key, value in instincts_config.items():
            back_left = (value[0][0], value[0][1], value[0][2])
            back_right = (value[1][0], value[1][1], value[1][2])
            front_left = (value[2][0], value[2][1], value[2][2])
            front_right = (value[3][0], value[3][1], value[3][2])
            result.append(Instinct(back_left, back_right, front_left, front_right))
        
        return result

    def check_event(self, key):
        return key in self._event and self._event[key] != 0 and key in self._prev_event and self._prev_event[key] == 0

    def handle_instinct(self, instinct):
        self.servos_configurations.rearLeft.shoulder.restAngle = instinct.rearLeft[0]
        self.servos_configurations.rearLeft.leg.restAngle = instinct.rearLeft[1]
        self.servos_configurations.rearLeft.foot.restAngle = instinct.rearLeft[2]

        self.servos_configurations.rearRight.shoulder.restAngle = instinct.rearRight[0]
        self.servos_configurations.rearRight.leg.restAngle = instinct.rearRight[1]
        self.servos_configurations.rearRight.foot.restAngle = instinct.rearRight[2]

        self.servos_configurations.frontLeft.shoulder.restAngle = instinct.frontLeft[0]
        self.servos_configurations.frontLeft.leg.restAngle = instinct.frontLeft[1]
        self.servos_configurations.frontLeft.foot.restAngle = instinct.frontLeft[2]

        self.servos_configurations.frontRight.shoulder.restAngle = instinct.frontRight[0]
        self.servos_configurations.frontRight.leg.restAngle = instinct.frontRight[1]
        self.servos_configurations.frontRight.foot.restAngle = instinct.frontRight[2]

    def print_diagnostics(self):
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearLeft.shoulder.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearLeft.leg.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearLeft.foot.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearRight.shoulder.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearRight.leg.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.rearRight.foot.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontLeft.shoulder.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontLeft.leg.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontLeft.foot.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontRight.shoulder.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontRight.leg.restAngle))
        print('self.servos_configurations.rearLeft.shoulder.restAngle: ' + str(self.servos_configurations.frontRight.foot.restAngle))
        print('')

    def calculate_rotational_movement(self, gait, index):
        # This angle calculation is only used when rotating the bot clockwise or counter clockwise
        angle = 45.0 / 180.0 * math.pi
        x_rot = math.sin(angle) * self._rotation_factor * self.ROTATION_OFFSET
        z_rot = math.cos(angle) * self._rotation_factor * self.ROTATION_OFFSET

        angle = (45 + gait[index].x) / 180.0 * math.pi
        x_rot = x_rot - math.sin(angle) * self._rotation_factor * self.ROTATION_OFFSET
        z_rot = z_rot - math.cos(angle) * self._rotation_factor * self.ROTATION_OFFSET
        
        return x_rot, z_rot

    ########################################################################
    #region Kinematics functions
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

    def _process_keyframe(self, leg: Keyframe, height_factor, lean_factor, ratio):
        start_coord = Coordinate(leg.previous.x, leg.previous.y + height_factor, leg.previous.z + lean_factor)
        end_coord = Coordinate(leg.current.x, leg.current.y + height_factor, leg.current.z + lean_factor)

        return InverseKinematics(
            interpolate(start_coord.x, end_coord.x, ratio),
            interpolate(start_coord.y, end_coord.y, ratio),
            interpolate(start_coord.z, end_coord.z, ratio))

    ########################################################################
    #region Kinematics Helper functions
    def interpolateKeyframes(self, ratio):
        """Interpolate between the current and next keyframes for each leg and apply the servo positions.

        Parameters
        ----------
        ratio : float
            The ratio of each keyframe in the interpolation. Should be in the range 0.0-1.0.
        """
        foot, leg, shoulder = self._process_keyframe(self._keyframes.frontRight, self._height_factor, -self._lean_factor, ratio)
        self.frontRightLeg(foot, leg, shoulder)

        foot, leg, shoulder = self._process_keyframe(self._keyframes.backLeft, self._height_factor, self._lean_factor, ratio)
        self.rearLeftLeg(foot, leg, shoulder)

        foot, leg, shoulder = self._process_keyframe(self._keyframes.frontLeft, self._height_factor, self._lean_factor, ratio)
        self.frontLeftLeg(foot, leg, shoulder)

        foot, leg, shoulder = self._process_keyframe(self._keyframes.backRight, self._height_factor, -self._lean_factor, ratio)
        self.rearRightLeg(foot, leg, shoulder)

    def rearLeftLeg(self, foot, leg, shoulder):
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
        self.servos.rearLeft.shoulder.angle = shoulder
        self.servos.rearLeft.leg.angle = min(leg + self.LEG_SERVO_OFFSET, 180)
        self.servos.rearLeft.foot.angle = max(foot - self.FOOT_SERVO_OFFSET, 0)

    def rearRightLeg(self, foot, leg, shoulder):
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
        self.servos.rearRight.shoulder.angle = 180 - shoulder
        self.servos.rearRight.leg.angle = max(180 - (leg + self.LEG_SERVO_OFFSET), 0)
        self.servos.rearRight.foot.angle = 180 - max(foot - self.FOOT_SERVO_OFFSET, 0)

    def frontLeftLeg(self, foot, leg, shoulder):
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
        self.servos.frontLeft.shoulder.angle = 180 - shoulder
        self.servos.frontLeft.leg.angle = min(leg + self.LEG_SERVO_OFFSET, 180)
        self.servos.frontLeft.foot.angle = max(foot - self.FOOT_SERVO_OFFSET, 0)

    def frontRightLeg(self, foot, leg, shoulder):
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
        self.servos.frontRight.shoulder.angle = shoulder
        self.servos.frontRight.leg.angle = max(180 - (leg + self.LEG_SERVO_OFFSET), 0)
        self.servos.frontRight.foot.angle = 180 - max(foot - self.FOOT_SERVO_OFFSET, 0)

    def _shift_keyframes(self, ratio = 0):
        """Shift the next keyframe to be the current keyframe.
        
        Parameters
        ----------
        ratio : float
            Ratio for interpolating keyframes if shifting between keyframe transitions.
        """
        if ratio > 0:

            self._keyframes.backLeft.previous = self._calc_previous_keyframe(self._keyframes.backLeft, ratio)
            self._keyframes.backRight.previous = self._calc_previous_keyframe(self._keyframes.backRight, ratio)
            self._keyframes.frontLeft.previous = self._calc_previous_keyframe(self._keyframes.frontLeft, ratio)
            self._keyframes.frontRight.previous = self._calc_previous_keyframe(self._keyframes.frontRight, ratio)

        else:
            self._keyframes.backLeft.previous = self._keyframes.backLeft.current
            self._keyframes.backRight.previous = self._keyframes.backRight.current
            self._keyframes.frontLeft.previous = self._keyframes.frontLeft.current
            self._keyframes.frontRight.previous = self._keyframes.frontRight.current

    def _calc_previous_keyframe(self, leg, ratio):
            prev = leg.previous
            curr = leg.current
            
            x = interpolate(prev.x, curr.x, ratio)
            y = interpolate(prev.y, curr.y, ratio)
            z = interpolate(prev.z, curr.z, ratio)

            return Coordinate(x, y, z)

    #endregion

    def load_pca9685_boards_configuration(self):
        self.pca9685_1_address = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_1_ADDRESS), 0)
        self.pca9685_1_reference_clock_speed = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_1_REFERENCE_CLOCK_SPEED))
        self.pca9685_1_frequency = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_1_FREQUENCY))

        self.pca9685_2_address = False
        try:
            self.pca9685_2_address = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_2_ADDRESS), 0)

            if self.pca9685_2_address:
                self.pca9685_2_reference_clock_speed = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_2_REFERENCE_CLOCK_SPEED))
                self.pca9685_2_frequency = int(Config().get(Config.MOTION_CONTROLLER_BOARDS_PCA9685_2_FREQUENCY))

        except Exception as e:
            print("Only 1 PCA9685 is present in the configuration")

    def activate_pca9685_boards(self):

        self.pca9685_1 = PCA9685(self.i2c, address=self.pca9685_1_address,
                                 reference_clock_speed=self.pca9685_1_reference_clock_speed)
        self.pca9685_1.frequency = self.pca9685_1_frequency

        if self.pca9685_2_address:
            self.pca9685_2 = PCA9685(self.i2c, address=self.pca9685_2_address,
                                     reference_clock_speed=self.pca9685_2_reference_clock_speed)
            self.pca9685_2.frequency = self.pca9685_2_frequency
            self.boards = 2

        self._is_activated = True
        print(str(self.boards) + ' PCA9685 board(s) activated')

    def deactivate_pca9685_boards(self):

        try:
            if self.pca9685_1:
                self.pca9685_1.deinit()
        finally:
            try:
                if self.boards == 2 and self.pca9685_2:
                    self.pca9685_2.deinit()
            finally:
                self._abort_queue.put(queues.ABORT_CONTROLLER_ACTION_ABORT)
                self._is_activated = False

        print(str(self.boards) + ' PCA9685 board(s) deactivated')

    def load_servos_configuration(self):

        #region Rear Left Limb
        rear_left_shoulder = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_REST_ANGLE)
        )

        rear_left_leg = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_REST_ANGLE)
        )

        rear_left_foot = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_REST_ANGLE)
        )

        rear_left_limb = ServoConfigurationsForLimb(rear_left_shoulder, rear_left_leg, rear_left_foot)
        #endregion

        #region Rear Right Limb
        rear_right_shoulder = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_REST_ANGLE)
        )

        rear_right_leg = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_REST_ANGLE)
        )

        rear_right_foot = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_REST_ANGLE)
        )

        rear_right_limb = ServoConfigurationsForLimb(rear_right_shoulder, rear_right_leg, rear_right_foot)
        #endregion

        #region Front Left Limb
        front_left_shoulder = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_REST_ANGLE)
        )

        front_left_leg = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_REST_ANGLE)
        )

        front_left_foot = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_REST_ANGLE)
        )

        front_left_limb = ServoConfigurationsForLimb(front_left_shoulder, front_left_leg, front_left_foot)
        #endregion

        #region Front Right Limb
        front_right_shoulder = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_REST_ANGLE)
        )

        front_right_leg = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_REST_ANGLE)
        )

        front_right_foot = ServoConfigurations(
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_CHANNEL),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_MIN_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_MAX_PULSE),
            Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_REST_ANGLE)
        )

        front_right_limb = ServoConfigurationsForLimb(front_right_shoulder, front_right_leg, front_right_foot)
        #endregion

        # Servo configurations collection
        self.servos_configurations = ServoConfigurationsCollection(rear_left_limb, rear_right_limb, front_left_limb, front_right_limb)

    def activate_servos(self):
        #region Rear Left Limb
        rear_left_shoulder_config = self.servos_configurations.rearLeft.shoulder
        rear_left_shoulder_servo = servo.Servo(self.pca9685_1.channels[rear_left_shoulder_config.channel])
        rear_left_shoulder_servo.set_pulse_width_range(min_pulse = rear_left_shoulder_config.minPulse , max_pulse = rear_left_shoulder_config.maxPulse)

        rear_left_leg_config = self.servos_configurations.rearLeft.leg
        rear_left_leg_servo = servo.Servo(self.pca9685_1.channels[rear_left_leg_config.channel])
        rear_left_leg_servo.set_pulse_width_range(min_pulse = rear_left_leg_config.minPulse , max_pulse = rear_left_leg_config.maxPulse)

        rear_left_foot_config = self.servos_configurations.rearLeft.foot
        rear_left_foot_servo = servo.Servo(self.pca9685_1.channels[rear_left_foot_config.channel])
        rear_left_foot_servo.set_pulse_width_range(min_pulse = rear_left_foot_config.minPulse , max_pulse = rear_left_foot_config.maxPulse)

        rear_left_limb_servo = ServoStateForLimb(rear_left_shoulder_servo, rear_left_leg_servo, rear_left_foot_servo)
        #endregion

        #region Rear Right Limb
        rear_right_shoulder_config = self.servos_configurations.rearRight.shoulder
        rear_right_shoulder_servo = servo.Servo(self.pca9685_1.channels[rear_right_shoulder_config.channel])
        rear_right_shoulder_servo.set_pulse_width_range(min_pulse = rear_right_shoulder_config.minPulse , max_pulse = rear_right_shoulder_config.maxPulse)

        rear_right_leg_config = self.servos_configurations.rearRight.leg
        rear_right_leg_servo = servo.Servo(self.pca9685_1.channels[rear_right_leg_config.channel])
        rear_right_leg_servo.set_pulse_width_range(min_pulse = rear_right_leg_config.minPulse , max_pulse = rear_right_leg_config.maxPulse)

        rear_right_foot_config = self.servos_configurations.rearRight.foot
        rear_right_foot_servo = servo.Servo(self.pca9685_1.channels[rear_right_foot_config.channel])
        rear_right_foot_servo.set_pulse_width_range(min_pulse = rear_right_foot_config.minPulse , max_pulse = rear_right_foot_config.maxPulse)

        rear_right_limb_servo = ServoStateForLimb(rear_right_shoulder_servo, rear_right_leg_servo, rear_right_foot_servo)
        #endregion

        #region Front Left Limb
        front_left_shoulder_config = self.servos_configurations.frontLeft.shoulder
        front_left_shoulder_servo = servo.Servo(self.pca9685_1.channels[front_left_shoulder_config.channel])
        front_left_shoulder_servo.set_pulse_width_range(min_pulse = front_left_shoulder_config.minPulse , max_pulse = front_left_shoulder_config.maxPulse)

        front_left_leg_config = self.servos_configurations.frontLeft.leg
        front_left_leg_servo = servo.Servo(self.pca9685_1.channels[front_left_leg_config.channel])
        front_left_leg_servo.set_pulse_width_range(min_pulse = front_left_leg_config.minPulse , max_pulse = front_left_leg_config.maxPulse)

        front_left_foot_config = self.servos_configurations.frontLeft.foot
        front_left_foot_servo = servo.Servo(self.pca9685_1.channels[front_left_foot_config.channel])
        front_left_foot_servo.set_pulse_width_range(min_pulse = front_left_foot_config.minPulse , max_pulse = front_left_foot_config.maxPulse)

        front_left_limb_servo = ServoStateForLimb(front_left_shoulder_servo, front_left_leg_servo, front_left_foot_servo)
        #endregion

        #region Front right Limb
        front_right_shoulder_config = self.servos_configurations.frontRight.shoulder
        front_right_shoulder_servo = servo.Servo(self.pca9685_1.channels[front_right_shoulder_config.channel])
        front_right_shoulder_servo.set_pulse_width_range(min_pulse = front_right_shoulder_config.minPulse , max_pulse = front_right_shoulder_config.maxPulse)

        front_right_leg_config = self.servos_configurations.frontRight.leg
        front_right_leg_servo = servo.Servo(self.pca9685_1.channels[front_right_leg_config.channel])
        front_right_leg_servo.set_pulse_width_range(min_pulse = front_right_leg_config.minPulse , max_pulse = front_right_leg_config.maxPulse)

        front_right_foot_config = self.servos_configurations.frontRight.foot
        front_right_foot_servo = servo.Servo(self.pca9685_1.channels[front_right_foot_config.channel])
        front_right_foot_servo.set_pulse_width_range(min_pulse = front_right_foot_config.minPulse , max_pulse = front_right_foot_config.maxPulse)

        front_right_limb_servo = ServoStateForLimb(front_right_shoulder_servo, front_right_leg_servo, front_right_foot_servo)
        #endregion

        self.servos = ServoStateCollection(rear_left_limb_servo, rear_right_limb_servo, front_left_limb_servo, front_right_limb_servo)

    def move(self):
        # Rear Left Limb
        try:
            self.servos.rearLeft.shoulder.angle = self.servos_configurations.rearLeft.shoulder.restAngle
        except ValueError as e:
            log.error('Impossible rear left shoulder angle requested: ' + str(self.servos_configurations.rearLeft.shoulder.restAngle))

        try:
            self.servos.rearLeft.leg.angle = self.servos_configurations.rearLeft.leg.restAngle
        except ValueError as e:
            log.error('Impossible rear left leg angle requested: ' + str(self.servos_configurations.rearLeft.leg.restAngle))

        try:
            self.servos.rearLeft.foot.angle = self.servos_configurations.rearLeft.foot.restAngle
        except ValueError as e:
            log.error('Impossible rear left foot angle requested: ' + str(self.servos_configurations.rearLeft.foot.restAngle))

        # Rear Right Limb
        try:
            self.servos.rearRight.shoulder.angle = self.servos_configurations.rearRight.shoulder.restAngle
        except ValueError as e:
            log.error('Impossible rear right shoulder angle requested: ' + str(self.servos_configurations.rearRight.shoulder.restAngle))

        try:
            self.servos.rearRight.leg.angle = self.servos_configurations.rearRight.leg.restAngle
        except ValueError as e:
            log.error('Impossible rear right leg angle requested: ' + str(self.servos_configurations.rearRight.leg.restAngle))

        try:
            self.servos.rearRight.foot.angle = self.servos_configurations.rearRight.foot.restAngle
        except ValueError as e:
            log.error('Impossible rear right foot angle requested: ' + str(self.servos_configurations.rearRight.foot.restAngle))

        # Front Left Limb
        try:
            self.servos.frontLeft.shoulder.angle = self.servos_configurations.frontLeft.shoulder.restAngle
        except ValueError as e:
            log.error('Impossible front left shoulder angle requested: ' + str(self.servos_configurations.frontLeft.shoulder.restAngle))

        try:
            self.servos.frontLeft.leg.angle = self.servos_configurations.frontLeft.leg.restAngle
        except ValueError as e:
            log.error('Impossible front left leg angle requested: ' + str(self.servos_configurations.frontLeft.leg.restAngle))

        try:
            self.servos.frontLeft.foot.angle = self.servos_configurations.frontLeft.foot.restAngle
        except ValueError as e:
            log.error('Impossible front left foot angle requested: ' + str(self.servos_configurations.frontLeft.foot.restAngle))

        # Front Right Limb
        try:
            self.servos.frontRight.shoulder.angle = self.servos_configurations.frontRight.shoulder.restAngle
        except ValueError as e:
            log.error('Impossible front right shoulder angle requested: ' + str(self.servos_configurations.frontRight.shoulder.restAngle))

        try:
            self.servos.frontRight.leg.angle = self.servos_configurations.frontRight.leg.restAngle
        except ValueError as e:
            log.error('Impossible front right leg angle requested: ' + str(self.servos_configurations.frontRight.leg.restAngle))

        try:
            self.servos.frontRight.foot.angle = self.servos_configurations.frontRight.foot.restAngle
        except ValueError as e:
            log.error('Impossible front right foot angle requested: ' + str(self.servos_configurations.frontRight.foot.restAngle))

    def rest_position(self):
        self.servos.rearLeft.shoulder.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_REST_ANGLE)
        self.servos.rearLeft.leg.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_REST_ANGLE)
        self.servos.rearLeft.foot.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_REST_ANGLE)
        self.servos.rearRight.shoulder.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_REST_ANGLE)
        self.servos.rearRight.leg.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_REST_ANGLE)
        self.servos.rearRight.foot.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_REST_ANGLE)
        self.servos.frontLeft.shoulder.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_REST_ANGLE)
        self.servos.frontLeft.leg.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_REST_ANGLE)
        self.servos.frontLeft.foot.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_REST_ANGLE)
        self.servos.frontRight.shoulder.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_REST_ANGLE)
        self.servos.frontRight.leg.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_REST_ANGLE)
        self.servos.frontRight.foot.restAngle = Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_REST_ANGLE)

    def body_move_pitch(self, raw_value):

        leg_increment = 10
        foot_increment = 15

        if raw_value < 0:
            self.servos_configurations.rearLeft.leg.restAngle -= leg_increment
            self.servos_configurations.rearLeft.foot.restAngle += foot_increment
            self.servos_configurations.rearRight.leg.restAngle += leg_increment
            self.servos_configurations.rearRight.foot.restAngle -= foot_increment
            self.servos_configurations.frontLeft.leg.restAngle -= leg_increment
            self.servos_configurations.frontLeft.foot.restAngle += foot_increment
            self.servos_configurations.frontRight.leg.restAngle += leg_increment
            self.servos_configurations.frontRight.foot.restAngle -= foot_increment

        elif raw_value > 0:
            self.servos_configurations.rearLeft.leg.restAngle += leg_increment
            self.servos_configurations.rearLeft.foot.restAngle -= foot_increment
            self.servos_configurations.rearRight.leg.restAngle -= leg_increment
            self.servos_configurations.rearRight.foot.restAngle += foot_increment
            self.servos_configurations.frontLeft.leg.restAngle += leg_increment
            self.servos_configurations.frontLeft.foot.restAngle -= foot_increment
            self.servos_configurations.frontRight.leg.restAngle -= leg_increment
            self.servos_configurations.frontRight.foot.restAngle += foot_increment


        else:
            self.rest_position()
        self.print_diagnostics()

    def body_move_roll(self, raw_value):

        range = 1

        if raw_value < 0:
            self.servos_configurations.rearLeft.shoulder.restAngle = max(self.servos_configurations.rearLeft.shoulder.restAngle - range, 0)
            self.servos_configurations.rearRight.shoulder.restAngle = max(self.servos_configurations.rearRight.shoulder.restAngle - range, 0)
            self.servos_configurations.frontLeft.shoulder.restAngle = min(self.servos_configurations.frontLeft.shoulder.restAngle + range, 180)
            self.servos_configurations.frontRight.shoulder.restAngle = min(self.servos_configurations.frontRight.shoulder.restAngle + range, 180)

        elif raw_value > 0:
            self.servos_configurations.rearLeft.shoulder.restAngle = min(self.servos_configurations.rearLeft.shoulder.restAngle + range, 180)
            self.servos_configurations.rearRight.shoulder.restAngle = min(self.servos_configurations.rearRight.shoulder.restAngle + range, 180)
            self.servos_configurations.frontLeft.shoulder.restAngle = max(self.servos_configurations.frontLeft.shoulder.restAngle - range, 0)
            self.servos_configurations.frontRight.shoulder.restAngle = max(self.servos_configurations.frontRight.shoulder.restAngle - range, 0)

        else:
            self.rest_position()
        self.print_diagnostics()

    def standing_position(self):

        variation_leg = 30
        variation_foot = 50

        self.servos_configurations.rearLeft.shoulder.restAngle = self.servos_configurations.rearLeft.shoulder.restAngle + 10
        self.servos_configurations.rearLeft.leg.restAngle = self.servos_configurations.rearLeft.leg.restAngle - variation_leg
        self.servos_configurations.rearLeft.foot.restAngle = self.servos_configurations.rearLeft.foot.restAngle + variation_foot

        self.servos_configurations.rearRight.shoulder.restAngle = self.servos_configurations.rearRight.shoulder.restAngle - 10
        self.servos_configurations.rearRight.leg.restAngle = self.servos_configurations.rearRight.leg.restAngle + variation_leg
        self.servos_configurations.rearRight.foot.restAngle = self.servos_configurations.rearRight.foot.restAngle - variation_foot

        time.sleep(0.05)

        self.servos_configurations.frontLeft.shoulder.restAngle = self.servos_configurations.frontLeft.shoulder.restAngle - 10
        self.servos_configurations.frontLeft.leg.restAngle = self.servos_configurations.frontLeft.leg.restAngle - variation_leg + 5
        self.servos_configurations.frontLeft.foot.restAngle = self.servos_configurations.frontLeft.foot.restAngle + variation_foot - 5

        self.servos_configurations.frontRight.shoulder.restAngle = self.servos_configurations.frontRight.shoulder.restAngle + 10
        self.servos_configurations.frontRight.leg.restAngle = self.servos_configurations.frontRight.leg.restAngle + variation_leg - 5
        self.servos_configurations.frontRight.foot.restAngle = self.servos_configurations.frontRight.foot.restAngle - variation_foot + 5

        self.print_diagnostics()

    # def body_move_position_right(self):

    #     move = 20

    #     variation_leg = 50
    #     variation_feet = 70

    #     self.servos_configurations.rearLeft.shoulder.restAngle = self.servos_configurations.rearLeft.shoulder.restAngle + 10 + move
    #     self.servos_configurations.rearLeft.leg.restAngle = self.servos_configurations.rearLeft.leg.restAngle - variation_leg
    #     self.servos_configurations.rearLeft.foot.restAngle = self.servos_configurations.rearLeft.foot.restAngle + variation_feet

    #     self.servos_configurations.rearRight.shoulder.restAngle = self.servos_configurations.rearRight.shoulder.restAngle - 10 + move
    #     self.servos_configurations.rearRight.leg.restAngle = self.servos_configurations.rearRight.leg.restAngle + variation_leg
    #     self.servos_configurations.rearRight.foot.restAngle = self.servos_configurations.rearRight.foot.restAngle - variation_feet

    #     time.sleep(0.05)

    #     self.servos_configurations.frontLeft.shoulder.restAngle = self.servos_configurations.frontLeft.shoulder.restAngle - 10 - move
    #     self.servos_configurations.frontLeft.leg.restAngle = self.servos_configurations.frontLeft.leg.restAngle - variation_leg + 5
    #     self.servos_configurations.frontLeft.foot.restAngle = self.servos_configurations.frontLeft.foot.restAngle + variation_feet - 5

    #     self.servos_configurations.frontRight.shoulder.restAngle = self.servos_configurations.frontRight.shoulder.restAngle + 10 - move
    #     self.servos_configurations.frontRight.leg.restAngle = self.servos_configurations.frontRight.leg.restAngle + variation_leg - 5
    #     self.servos_configurations.frontRight.foot.restAngle = self.servos_configurations.frontRight.foot.restAngle - variation_feet + 5

    # def body_move_position_left(self):

    #     move = 20

    #     variation_leg = 50
    #     variation_feet = 70

    #     self.servos_configurations.rearLeft.shoulder.restAngle = self.servos_configurations.rearLeft.shoulder.restAngle + 10 - move
    #     self.servos_configurations.rearLeft.leg.restAngle = self.servos_configurations.rearLeft.leg.restAngle - variation_leg
    #     self.servos_configurations.rearLeft.foot.restAngle = self.servos_configurations.rearLeft.foot.restAngle + variation_feet

    #     self.servos_configurations.rearRight.shoulder.restAngle = self.servos_configurations.rearRight.shoulder.restAngle - 10 - move
    #     self.servos_configurations.rearRight.leg.restAngle = self.servos_configurations.rearRight.leg.restAngle + variation_leg
    #     self.servos_configurations.rearRight.foot.restAngle = self.servos_configurations.rearRight.foot.restAngle - variation_feet

    #     time.sleep(0.05)

    #     self.servos_configurations.frontLeft.shoulder.restAngle = self.servos_configurations.frontLeft.shoulder.restAngle - 10 + move
    #     self.servos_configurations.frontLeft.leg.restAngle = self.servos_configurations.frontLeft.leg.restAngle - variation_leg + 5
    #     self.servos_configurations.frontLeft.foot.restAngle = self.servos_configurations.frontLeft.foot.restAngle + variation_feet - 5

    #     self.servos_configurations.frontRight.shoulder.restAngle = self.servos_configurations.frontRight.shoulder.restAngle + 10 + move
    #     self.servos_configurations.frontRight.leg.restAngle = self.servos_configurations.frontRight.leg.restAngle + variation_leg - 5
    #     self.servos_configurations.frontRight.foot.restAngle = self.servos_configurations.frontRight.foot.restAngle - variation_feet + 5

    #############################################
    # Left thumbstick controls
    #############################################

    def body_move_pitch_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self.servos_configurations.rearLeft.leg.restAngle = int(General().maprange((5, -5), (180, 180), raw_value))
        self.servos_configurations.rearLeft.foot.restAngle = int(General().maprange((5, -5), (10, 50), raw_value))
        self.servos_configurations.rearRight.leg.restAngle = int(General().maprange((5, -5), (0, 0), raw_value))
        self.servos_configurations.rearRight.foot.restAngle = int(General().maprange((5, -5), (170, 130), raw_value))

        self.servos_configurations.frontLeft.leg.restAngle = int(General().maprange((-5, 5), (160, 180), raw_value))
        self.servos_configurations.frontLeft.foot.restAngle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self.servos_configurations.frontRight.leg.restAngle = int(General().maprange((-5, 5), (20, 0), raw_value))
        self.servos_configurations.frontRight.foot.restAngle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_roll_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self.servos_configurations.rearLeft.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))
        self.servos_configurations.rearRight.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))
        
        self.servos_configurations.frontLeft.shoulder.restAngle = int(General().maprange((-5, 5), (145, 35), raw_value))
        self.servos_configurations.frontRight.shoulder.restAngle = int(General().maprange((-5, 5), (145, 35), raw_value))

    def body_move_height_analog(self, raw_value):

        raw_value = math.floor(raw_value * 10 / 2)

        self.servos_configurations.rearLeft.leg.restAngle = int(General().maprange((5, -5), (160, 180), raw_value))
        self.servos_configurations.rearLeft.foot.restAngle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self.servos_configurations.rearRight.leg.restAngle = int(General().maprange((5, -5), (20, 0), raw_value))
        self.servos_configurations.rearRight.foot.restAngle = int(General().maprange((-5, 5), (170, 130), raw_value))

        self.servos_configurations.frontLeft.leg.restAngle = int(General().maprange((5, -5), (160, 180), raw_value))
        self.servos_configurations.frontLeft.foot.restAngle = int(General().maprange((-5, 5), (10, 50), raw_value))
        self.servos_configurations.frontRight.leg.restAngle = int(General().maprange((5, -5), (20, 0), raw_value))
        self.servos_configurations.frontRight.foot.restAngle = int(General().maprange((-5, 5), (170, 130), raw_value))

    def body_move_yaw_analog(self, raw_value):
        raw_value = math.floor(raw_value * 10 / 2)

        self.servos_configurations.rearLeft.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))
        self.servos_configurations.rearRight.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))
        
        self.servos_configurations.frontLeft.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))
        self.servos_configurations.frontRight.shoulder.restAngle = int(General().maprange((5, -5), (145, 35), raw_value))

    def setup_buzzer(self):
        self.buzzer_pin = Config().get('buzzer[0].gpio_port')

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.buzzer_pin, GPIO.OUT)
        GPIO.output(self.buzzer_pin, False)

    def beep(self):
        GPIO.output(self.buzzer_pin, True)
        time.sleep(0.5)
        GPIO.output(self.buzzer_pin, False)