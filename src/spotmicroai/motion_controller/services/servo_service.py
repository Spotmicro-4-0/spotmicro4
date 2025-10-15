from adafruit_motor import servo  # type: ignore
from spotmicroai.motion_controller.wrappers.pca9685 import PCA9685Board
from spotmicroai.singleton import Singleton
from spotmicroai.utilities.config import Config


class ServoService(metaclass=Singleton):
    """A singleton class containing all 12 Adafruit servo objects that control the robot's movements.

    This class initializes and manages the 12 servos (3 per leg: shoulder, leg, and foot for front and rear, left and right),
    each configured with pulse width ranges from the ServoConfigSet. These servo objects are used to control
    the physical movements of the SpotMicro robot.

    Staged angles can be set on the public attributes (e.g., rear_shoulder_left_angle), but changes are not applied
    to the servos until commit() is called. This allows batching multiple angle updates for synchronized movement.

    Used to track all 12 servos

    Attributes:
        rear_shoulder_left_angle: Staged angle for rear left shoulder servo (call commit() to apply)
        rear_leg_left_angle: Staged angle for rear left leg servo (call commit() to apply)
        rear_foot_left_angle: Staged angle for rear left foot servo (call commit() to apply)
        rear_shoulder_right_angle: Staged angle for rear right shoulder servo (call commit() to apply)
        rear_leg_right_angle: Staged angle for rear right leg servo (call commit() to apply)
        rear_foot_right_angle: Staged angle for rear right foot servo (call commit() to apply)
        front_shoulder_left_angle: Staged angle for front left shoulder servo (call commit() to apply)
        front_leg_left_angle: Staged angle for front left leg servo (call commit() to apply)
        front_foot_left_angle: Staged angle for front left foot servo (call commit() to apply)
        front_shoulder_right_angle: Staged angle for front right shoulder servo (call commit() to apply)
        front_leg_right_angle: Staged angle for front right leg servo (call commit() to apply)
        front_foot_right_angle: Staged angle for front right foot servo (call commit() to apply)
    """

    rear_shoulder_left_angle: float
    rear_leg_left_angle: float
    rear_foot_left_angle: float
    rear_shoulder_right_angle: float
    rear_leg_right_angle: float
    rear_foot_right_angle: float
    front_shoulder_left_angle: float
    front_leg_left_angle: float
    front_foot_left_angle: float
    front_shoulder_right_angle: float
    front_leg_right_angle: float
    front_foot_right_angle: float

    def __init__(self):
        self._config = Config()
        _pca9685_board = PCA9685Board()

        # --- Initialize physical servo objects ---
        self._rear_shoulder_left = self._make_servo(_pca9685_board, self._config.rear_shoulder_left)
        self._rear_leg_left = self._make_servo(_pca9685_board, self._config.rear_leg_left)
        self._rear_foot_left = self._make_servo(_pca9685_board, self._config.rear_foot_left)

        self._rear_shoulder_right = self._make_servo(_pca9685_board, self._config.rear_shoulder_right)
        self._rear_leg_right = self._make_servo(_pca9685_board, self._config.rear_leg_right)
        self._rear_foot_right = self._make_servo(_pca9685_board, self._config.rear_foot_right)

        self._front_shoulder_left = self._make_servo(_pca9685_board, self._config.front_shoulder_left)
        self._front_leg_left = self._make_servo(_pca9685_board, self._config.front_leg_left)
        self._front_foot_left = self._make_servo(_pca9685_board, self._config.front_foot_left)

        self._front_shoulder_right = self._make_servo(_pca9685_board, self._config.front_shoulder_right)
        self._front_leg_right = self._make_servo(_pca9685_board, self._config.front_leg_right)
        self._front_foot_right = self._make_servo(_pca9685_board, self._config.front_foot_right)

        # Initialize staged angles
        self.clear_staged()

    def _make_servo(self, board, config):
        s = servo.Servo(board.get_channel(config.channel))
        s.set_pulse_width_range(min_pulse=config.min_pulse, max_pulse=config.max_pulse)
        return s
    
    def commit(self):
        """Apply all staged servo angles to their respective servos."""
        angle_attrs = [
            "rear_shoulder_left_angle",
            "rear_leg_left_angle",
            "rear_foot_left_angle",
            "rear_shoulder_right_angle",
            "rear_leg_right_angle",
            "rear_foot_right_angle",
            "front_shoulder_left_angle",
            "front_leg_left_angle",
            "front_foot_left_angle",
            "front_shoulder_right_angle",
            "front_leg_right_angle",
            "front_foot_right_angle",
        ]
        for attr in angle_attrs:
            angle = getattr(self, attr)
            if angle is not None:
                servo_name = f"_{attr.replace('_angle', '')}"
                servo_obj = getattr(self, servo_name)
                servo_obj.angle = angle
        self.clear_staged()

    def clear_staged(self):
        """Reset all staged servo angles to their default rest angles."""
        self.rear_shoulder_left_angle = self._config.rear_shoulder_left.rest_angle
        self.rear_leg_left_angle = self._config.rear_leg_left.rest_angle
        self.rear_foot_left_angle = self._config.rear_foot_left.rest_angle
        self.rear_shoulder_right_angle = self._config.rear_shoulder_right.rest_angle
        self.rear_leg_right_angle = self._config.rear_leg_right.rest_angle
        self.rear_foot_right_angle = self._config.rear_foot_right.rest_angle
        self.front_shoulder_left_angle = self._config.front_shoulder_left.rest_angle
        self.front_leg_left_angle = self._config.front_leg_left.rest_angle
        self.front_foot_left_angle = self._config.front_foot_left.rest_angle
        self.front_shoulder_right_angle = self._config.front_shoulder_right.rest_angle
        self.front_leg_right_angle = self._config.front_leg_right.rest_angle
        self.front_foot_right_angle = self._config.front_foot_right.rest_angle
    
    def rest_position(self):
        self.clear_staged()
        self.commit();