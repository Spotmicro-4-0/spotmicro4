from adafruit_motor import servo # type: ignore
from spotmicroai.motion_controller.pca9685 import PCA9685Board
from spotmicroai.motion_controller.servo_config import ServoConfigSet
from spotmicroai.singleton import Singleton

class ServoSet(metaclass=Singleton):
    """A class containing all the 12 servos.

    Used to track all 12 servos

    Attributes:
        rear_shoulder_left: The rear left shoulder servo
        rear_leg_left: The rear left leg servo
        rear_foot_left: The rear left foot servo
        rear_shoulder_right: The rear right shoulder servo
        rear_leg_right: The rear right leg servo
        rear_foot_right: The rear right foot servo
        front_shoulder_left: The front left shoulder servo
        front_leg_left: The front left leg servo
        front_foot_left: The front left foot servo
        front_shoulder_right: The front right shoulder servo
        front_leg_right: The front right leg servo
        front_foot_right: The front right foot servo
    """

    rear_shoulder_left: servo.Servo
    rear_leg_left: servo.Servo
    rear_foot_left: servo.Servo
    rear_shoulder_right: servo.Servo
    rear_leg_right: servo.Servo
    rear_foot_right: servo.Servo
    front_shoulder_left: servo.Servo
    front_leg_left: servo.Servo
    front_foot_left: servo.Servo
    front_shoulder_right: servo.Servo
    front_leg_right: servo.Servo
    front_foot_right: servo.Servo

    def __init__(self):
        _servo_config_set = ServoConfigSet()
        _pca9685_board = PCA9685Board()

        rear_left_shoulder_config = _servo_config_set.rear_shoulder_left
        self.rear_shoulder_left = servo.Servo(_pca9685_board.get_channel(rear_left_shoulder_config.channel))
        self.rear_shoulder_left.set_pulse_width_range(min_pulse = rear_left_shoulder_config.min_pulse , max_pulse = rear_left_shoulder_config.max_pulse)

        rear_left_leg_config = _servo_config_set.rear_leg_left
        self.rear_leg_left = servo.Servo(_pca9685_board.get_channel(rear_left_leg_config.channel))
        self.rear_leg_left.set_pulse_width_range(min_pulse = rear_left_leg_config.min_pulse , max_pulse = rear_left_leg_config.max_pulse)

        rear_left_foot_config = _servo_config_set.rear_foot_left
        self.rear_foot_left = servo.Servo(_pca9685_board.get_channel(rear_left_foot_config.channel))
        self.rear_foot_left.set_pulse_width_range(min_pulse = rear_left_foot_config.min_pulse , max_pulse = rear_left_foot_config.max_pulse)

        rear_right_shoulder_config = _servo_config_set.rear_shoulder_right
        self.rear_shoulder_right = servo.Servo(_pca9685_board.get_channel(rear_right_shoulder_config.channel))
        self.rear_shoulder_right.set_pulse_width_range(min_pulse = rear_right_shoulder_config.min_pulse , max_pulse = rear_right_shoulder_config.max_pulse)

        rear_right_leg_config = _servo_config_set.rear_leg_right
        self.rear_leg_right = servo.Servo(_pca9685_board.get_channel(rear_right_leg_config.channel))
        self.rear_leg_right.set_pulse_width_range(min_pulse = rear_right_leg_config.min_pulse , max_pulse = rear_right_leg_config.max_pulse)

        rear_right_foot_config = _servo_config_set.rear_foot_right
        self.rear_foot_right = servo.Servo(_pca9685_board.get_channel(rear_right_foot_config.channel))
        self.rear_foot_right.set_pulse_width_range(min_pulse = rear_right_foot_config.min_pulse , max_pulse = rear_right_foot_config.max_pulse)

        front_left_shoulder_config = _servo_config_set.front_shoulder_left
        self.front_shoulder_left = servo.Servo(_pca9685_board.get_channel(front_left_shoulder_config.channel))
        self.front_shoulder_left.set_pulse_width_range(min_pulse = front_left_shoulder_config.min_pulse , max_pulse = front_left_shoulder_config.max_pulse)

        front_left_leg_config = _servo_config_set.front_leg_left
        self.front_leg_left = servo.Servo(_pca9685_board.get_channel(front_left_leg_config.channel))
        self.front_leg_left.set_pulse_width_range(min_pulse = front_left_leg_config.min_pulse , max_pulse = front_left_leg_config.max_pulse)

        front_left_foot_config = _servo_config_set.front_foot_left
        self.front_foot_left = servo.Servo(_pca9685_board.get_channel(front_left_foot_config.channel))
        self.front_foot_left.set_pulse_width_range(min_pulse = front_left_foot_config.min_pulse , max_pulse = front_left_foot_config.max_pulse)

        front_right_shoulder_config = _servo_config_set.front_shoulder_right
        self.front_shoulder_right = servo.Servo(_pca9685_board.get_channel(front_right_shoulder_config.channel))
        self.front_shoulder_right.set_pulse_width_range(min_pulse = front_right_shoulder_config.min_pulse , max_pulse = front_right_shoulder_config.max_pulse)

        front_right_leg_config = _servo_config_set.front_leg_right
        self.front_leg_right = servo.Servo(_pca9685_board.get_channel(front_right_leg_config.channel))
        self.front_leg_right.set_pulse_width_range(min_pulse = front_right_leg_config.min_pulse , max_pulse = front_right_leg_config.max_pulse)

        front_right_foot_config = _servo_config_set.front_foot_right
        self.front_foot_right = servo.Servo(_pca9685_board.get_channel(front_right_foot_config.channel))
        self.front_foot_right.set_pulse_width_range(min_pulse = front_right_foot_config.min_pulse , max_pulse = front_right_foot_config.max_pulse)
