from adafruit_motor import servo  # type: ignore

from spotmicroai.motion_controller.wrappers.pca9685 import PCA9685Board
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.singleton import Singleton


class ServoService(metaclass=Singleton):
    """Manages and controls all 12 servos using configuration loaded via Config (DotDict-enabled)."""

    def __init__(self):
        self._config = Config()
        _pca9685_board = PCA9685Board()

        # Access servos directly via dot notation
        servo_configs = self._config.motion_controller.servos

        # --- Initialize physical servo objects ---
        self._rear_shoulder_left = self._make_servo(_pca9685_board, servo_configs.rear_shoulder_left)
        self._rear_leg_left = self._make_servo(_pca9685_board, servo_configs.rear_leg_left)
        self._rear_foot_left = self._make_servo(_pca9685_board, servo_configs.rear_foot_left)

        self._rear_shoulder_right = self._make_servo(_pca9685_board, servo_configs.rear_shoulder_right)
        self._rear_leg_right = self._make_servo(_pca9685_board, servo_configs.rear_leg_right)
        self._rear_foot_right = self._make_servo(_pca9685_board, servo_configs.rear_foot_right)

        self._front_shoulder_left = self._make_servo(_pca9685_board, servo_configs.front_shoulder_left)
        self._front_leg_left = self._make_servo(_pca9685_board, servo_configs.front_leg_left)
        self._front_foot_left = self._make_servo(_pca9685_board, servo_configs.front_foot_left)

        self._front_shoulder_right = self._make_servo(_pca9685_board, servo_configs.front_shoulder_right)
        self._front_leg_right = self._make_servo(_pca9685_board, servo_configs.front_leg_right)
        self._front_foot_right = self._make_servo(_pca9685_board, servo_configs.front_foot_right)

        # Initialize staged angles
        self.clear_staged()

    def _make_servo(self, board, config):
        """Create and configure one Adafruit servo object."""
        s = servo.Servo(board.get_channel(config.channel))
        s.set_pulse_width_range(min_pulse=config.min_pulse, max_pulse=config.max_pulse)
        return s

    def commit(self):
        """Apply all staged servo angles to their respective servo objects."""
        for name in [
            "rear_shoulder_left",
            "rear_leg_left",
            "rear_foot_left",
            "rear_shoulder_right",
            "rear_leg_right",
            "rear_foot_right",
            "front_shoulder_left",
            "front_leg_left",
            "front_foot_left",
            "front_shoulder_right",
            "front_leg_right",
            "front_foot_right",
        ]:
            angle = getattr(self, f"{name}_angle", None)
            if angle is not None:
                getattr(self, f"_{name}").angle = angle
        self.clear_staged()

    def clear_staged(self):
        """Reset all staged servo angles to their configured rest angles."""
        servos = self._config.motion_controller.servos
        for name in [
            "rear_shoulder_left",
            "rear_leg_left",
            "rear_foot_left",
            "rear_shoulder_right",
            "rear_leg_right",
            "rear_foot_right",
            "front_shoulder_left",
            "front_leg_left",
            "front_foot_left",
            "front_shoulder_right",
            "front_leg_right",
            "front_foot_right",
        ]:
            setattr(self, f"{name}_angle", getattr(servos, name).rest_angle)

    def rest_position(self):
        """Return the robot to its rest position."""
        self.clear_staged()
        self.commit()
