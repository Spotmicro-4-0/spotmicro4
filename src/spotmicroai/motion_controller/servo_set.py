from adafruit_motor import servo # type: ignore
from spotmicroai.motion_controller.pca9685 import PCA9685Board
from spotmicroai.motion_controller.servo_config import ServoConfigSet
from spotmicroai.singleton import Singleton

class ServoSet:
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

    def __init__(self, rear_shoulder_left, rear_leg_left, rear_foot_left,
                 rear_shoulder_right, rear_leg_right, rear_foot_right,
                 front_shoulder_left, front_leg_left, front_foot_left,
                 front_shoulder_right, front_leg_right, front_foot_right):
        self.rear_shoulder_left = rear_shoulder_left
        self.rear_leg_left = rear_leg_left
        self.rear_foot_left = rear_foot_left
        self.rear_shoulder_right = rear_shoulder_right
        self.rear_leg_right = rear_leg_right
        self.rear_foot_right = rear_foot_right
        self.front_shoulder_left = front_shoulder_left
        self.front_leg_left = front_leg_left
        self.front_foot_left = front_foot_left
        self.front_shoulder_right = front_shoulder_right
        self.front_leg_right = front_leg_right
        self.front_foot_right = front_foot_right