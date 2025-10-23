"""
Servo service for managing and controlling all 12 servos on the SpotMicroAI robot.
Provides high-level interface for setting servo angles, committing changes, and managing poses.
"""

from spotmicroai import Singleton
from spotmicroai.configuration import ConfigProvider, ServoName
import spotmicroai.constants as constants
from spotmicroai.drivers import PCA9685, Servo
from spotmicroai.runtime.motion_controller.models.pose import Pose


class ServoService(metaclass=Singleton):
    """Manages and controls all 12 servos using configuration loaded via Config (DotDict-enabled)."""

    def __init__(self):
        self._config_provider = ConfigProvider()
        _pca9685_board = PCA9685()

        # --- Initialize physical servo objects ---
        self._rear_shoulder_left = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.REAR_SHOULDER_LEFT)
        )
        self._rear_leg_left = self._make_servo(_pca9685_board, self._config_provider.get_servo(ServoName.REAR_LEG_LEFT))
        self._rear_foot_left = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.REAR_FOOT_LEFT)
        )

        self._rear_shoulder_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.REAR_SHOULDER_RIGHT)
        )
        self._rear_leg_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.REAR_LEG_RIGHT)
        )
        self._rear_foot_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.REAR_FOOT_RIGHT)
        )

        self._front_shoulder_left = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_SHOULDER_LEFT)
        )
        self._front_leg_left = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_LEG_LEFT)
        )
        self._front_foot_left = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_FOOT_LEFT)
        )

        self._front_shoulder_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_SHOULDER_RIGHT)
        )
        self._front_leg_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_LEG_RIGHT)
        )
        self._front_foot_right = self._make_servo(
            _pca9685_board, self._config_provider.get_servo(ServoName.FRONT_FOOT_RIGHT)
        )

        # Initialize staged angles to rest positions
        self.rear_shoulder_left_angle = self._config_provider.get_servo(ServoName.REAR_SHOULDER_LEFT).rest_angle
        self.rear_leg_left_angle = self._config_provider.get_servo(ServoName.REAR_LEG_LEFT).rest_angle
        self.rear_foot_left_angle = self._config_provider.get_servo(ServoName.REAR_FOOT_LEFT).rest_angle
        self.rear_shoulder_right_angle = self._config_provider.get_servo(ServoName.REAR_SHOULDER_RIGHT).rest_angle
        self.rear_leg_right_angle = self._config_provider.get_servo(ServoName.REAR_LEG_RIGHT).rest_angle
        self.rear_foot_right_angle = self._config_provider.get_servo(ServoName.REAR_FOOT_RIGHT).rest_angle
        self.front_shoulder_left_angle = self._config_provider.get_servo(ServoName.FRONT_SHOULDER_LEFT).rest_angle
        self.front_leg_left_angle = self._config_provider.get_servo(ServoName.FRONT_LEG_LEFT).rest_angle
        self.front_foot_left_angle = self._config_provider.get_servo(ServoName.FRONT_FOOT_LEFT).rest_angle
        self.front_shoulder_right_angle = self._config_provider.get_servo(ServoName.FRONT_SHOULDER_RIGHT).rest_angle
        self.front_leg_right_angle = self._config_provider.get_servo(ServoName.FRONT_LEG_RIGHT).rest_angle
        self.front_foot_right_angle = self._config_provider.get_servo(ServoName.FRONT_FOOT_RIGHT).rest_angle

        # Initialize staged angles
        self.clear_staged()

    def _complement(self, angle):
        """Return the complementary angle (180 - angle)."""
        return 180 - angle

    def _make_servo(self, board, config):
        """Create and configure one Adafruit servo object."""
        s = Servo(
            board.get_channel(config.channel),
            min_pulse=config.min_pulse,
            max_pulse=config.max_pulse,
            actuation_range=config.range,
            rest_angle=config.rest_angle,
        )
        return s

    def commit(self):
        """Apply all staged servo angles to their respective servo objects."""
        self._rear_shoulder_left.angle = self.rear_shoulder_left_angle
        self._rear_leg_left.angle = self.rear_leg_left_angle
        self._rear_foot_left.angle = self.rear_foot_left_angle
        self._rear_shoulder_right.angle = self.rear_shoulder_right_angle
        self._rear_leg_right.angle = self.rear_leg_right_angle
        self._rear_foot_right.angle = self.rear_foot_right_angle
        self._front_shoulder_left.angle = self.front_shoulder_left_angle
        self._front_leg_left.angle = self.front_leg_left_angle
        self._front_foot_left.angle = self.front_foot_left_angle
        self._front_shoulder_right.angle = self.front_shoulder_right_angle
        self._front_leg_right.angle = self.front_leg_right_angle
        self._front_foot_right.angle = self.front_foot_right_angle
        self.clear_staged()

    def clear_staged(self):
        """Reset all staged servo angles to their configured rest angles."""
        self.rear_shoulder_left_angle = self._config_provider.get_servo(ServoName.REAR_SHOULDER_LEFT).rest_angle
        self.rear_leg_left_angle = self._config_provider.get_servo(ServoName.REAR_LEG_LEFT).rest_angle
        self.rear_foot_left_angle = self._config_provider.get_servo(ServoName.REAR_FOOT_LEFT).rest_angle
        self.rear_shoulder_right_angle = self._config_provider.get_servo(ServoName.REAR_SHOULDER_RIGHT).rest_angle
        self.rear_leg_right_angle = self._config_provider.get_servo(ServoName.REAR_LEG_RIGHT).rest_angle
        self.rear_foot_right_angle = self._config_provider.get_servo(ServoName.REAR_FOOT_RIGHT).rest_angle
        self.front_shoulder_left_angle = self._config_provider.get_servo(ServoName.FRONT_SHOULDER_LEFT).rest_angle
        self.front_leg_left_angle = self._config_provider.get_servo(ServoName.FRONT_LEG_LEFT).rest_angle
        self.front_foot_left_angle = self._config_provider.get_servo(ServoName.FRONT_FOOT_LEFT).rest_angle
        self.front_shoulder_right_angle = self._config_provider.get_servo(ServoName.FRONT_SHOULDER_RIGHT).rest_angle
        self.front_leg_right_angle = self._config_provider.get_servo(ServoName.FRONT_LEG_RIGHT).rest_angle
        self.front_foot_right_angle = self._config_provider.get_servo(ServoName.FRONT_FOOT_RIGHT).rest_angle

    def rest_position(self):
        """Return the robot to its rest position."""
        self.clear_staged()
        self.commit()

    def set_pose(self, pose: Pose):
        self.rear_shoulder_left_angle = pose.rear_left.shoulder_angle
        self.rear_leg_left_angle = pose.rear_left.leg_angle
        self.rear_foot_left_angle = pose.rear_left.foot_angle

        self.rear_shoulder_right_angle = pose.rear_right.shoulder_angle
        self.rear_leg_right_angle = pose.rear_right.leg_angle
        self.rear_foot_right_angle = pose.rear_right.foot_angle

        self.front_shoulder_left_angle = pose.front_left.shoulder_angle
        self.front_leg_left_angle = pose.front_left.leg_angle
        self.front_foot_left_angle = pose.front_left.foot_angle

        self.front_shoulder_right_angle = pose.front_right.shoulder_angle
        self.front_leg_right_angle = pose.front_right.leg_angle
        self.front_foot_right_angle = pose.front_right.foot_angle

    def set_front_right_servos(self, foot_angle: float, leg_angle: float, shoulder_angle: float):
        """Helper function for setting servo angles for the front right leg.

        Parameters
        ----------
        foot_angle : float
            Servo angle for foot in degrees.
        leg_angle : float
            Servo angle for leg in degrees.
        shoulder_angle : float
            Servo angle for shoulder in degrees.
        """
        self.front_shoulder_right_angle = shoulder_angle
        self.front_leg_right_angle = max(self._complement(leg_angle + constants.LEG_SERVO_OFFSET), 0)
        self.front_foot_right_angle = self._complement(max(foot_angle - constants.FOOT_SERVO_OFFSET, 0))

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
        self.front_shoulder_left_angle = self._complement(shoulder_angle)
        self.front_leg_left_angle = min(leg_angle + constants.LEG_SERVO_OFFSET, 180)
        self.front_foot_left_angle = max(foot_angle - constants.FOOT_SERVO_OFFSET, 0)

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
        self.rear_shoulder_right_angle = self._complement(shoulder_angle)
        self.rear_leg_right_angle = max(self._complement(leg_angle + constants.LEG_SERVO_OFFSET), 0)
        self.rear_foot_right_angle = self._complement(max(foot_angle - constants.FOOT_SERVO_OFFSET, 0))

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
        self.rear_shoulder_left_angle = shoulder_angle
        self.rear_leg_left_angle = min(leg_angle + constants.LEG_SERVO_OFFSET, 180)
        self.rear_foot_left_angle = max(foot_angle - constants.FOOT_SERVO_OFFSET, 0)
