from adafruit_motor import servo # type: ignore
from spotmicroai.motion_controller.pca9685 import PCA9685Board
from spotmicroai.motion_controller.servo_config import ServoConfigSet
from spotmicroai.singleton import Singleton
from typing import Optional

class ServoSet(metaclass=Singleton):
    """A singleton class containing all 12 Adafruit servo objects that control the robot's movements.

    This class initializes and manages the 12 servos (3 per leg: shoulder, leg, and foot for front and rear, left and right),
    each configured with pulse width ranges from the ServoConfigSet. These servo objects are used to control
    the physical movements of the SpotMicro robot.

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

        # --- Initialize physical servo objects ---
        self.rear_shoulder_left = self._make_servo(_pca9685_board, _servo_config_set.rear_shoulder_left)
        self.rear_leg_left = self._make_servo(_pca9685_board, _servo_config_set.rear_leg_left)
        self.rear_foot_left = self._make_servo(_pca9685_board, _servo_config_set.rear_foot_left)

        self.rear_shoulder_right = self._make_servo(_pca9685_board, _servo_config_set.rear_shoulder_right)
        self.rear_leg_right = self._make_servo(_pca9685_board, _servo_config_set.rear_leg_right)
        self.rear_foot_right = self._make_servo(_pca9685_board, _servo_config_set.rear_foot_right)

        self.front_shoulder_left = self._make_servo(_pca9685_board, _servo_config_set.front_shoulder_left)
        self.front_leg_left = self._make_servo(_pca9685_board, _servo_config_set.front_leg_left)
        self.front_foot_left = self._make_servo(_pca9685_board, _servo_config_set.front_foot_left)

        self.front_shoulder_right = self._make_servo(_pca9685_board, _servo_config_set.front_shoulder_right)
        self.front_leg_right = self._make_servo(_pca9685_board, _servo_config_set.front_leg_right)
        self.front_foot_right = self._make_servo(_pca9685_board, _servo_config_set.front_foot_right)

        from typing import Optional

        self._staged_angles: dict[str, Optional[float]] = {
            "rear_shoulder_left": None,
            "rear_leg_left": None,
            "rear_foot_left": None,
            "rear_shoulder_right": None,
            "rear_leg_right": None,
            "rear_foot_right": None,
            "front_shoulder_left": None,
            "front_leg_left": None,
            "front_foot_left": None,
            "front_shoulder_right": None,
            "front_leg_right": None,
            "front_foot_right": None,
        }

    def _make_servo(self, board, config):
        s = servo.Servo(board.get_channel(config.channel))
        s.set_pulse_width_range(min_pulse=config.min_pulse, max_pulse=config.max_pulse)
        return s
    
     # --- Public API ---
    def stage_angle(self, name: str, angle: float):
        """Stage a servo angle without moving the servo yet."""
        if name not in self._staged_angles:
            raise ValueError(f"Invalid servo name: {name}")
        self._staged_angles[name] = angle

    def commit(self):
        """Apply all staged servo angles to their respective servos."""
        for name, angle in self._staged_angles.items():
            if angle is not None:
                servo_obj = getattr(self, name)
                servo_obj.angle = angle
        self.clear_staged()

    def clear_staged(self):
        """Reset all staged servo angles."""
        for k in self._staged_angles:
            self._staged_angles[k] = None