"""Servo calibration hardware control module.

Manages PCA9685 board initialization and direct servo control during calibration.
Provides pulse width and angle-based servo positioning with safety clamping.
"""

from spotmicroai.configuration._config_provider import ConfigProvider, ServoName
from spotmicroai.constants import SERVO_PULSE_WIDTH_MAX, SERVO_PULSE_WIDTH_MIN
from spotmicroai.labels import (
    ERR_SERVO_CONFIG_MAX_PULSE_OUT_OF_RANGE,
    ERR_SERVO_CONFIG_MIN_MAX_EQUAL,
    ERR_SERVO_CONFIG_MIN_PULSE_OUT_OF_RANGE,
)
from spotmicroai.servo import JOINT_ANGLE_LIMITS, JointType, Servo
from spotmicroai.servo.pca9685 import PCA9685


class ServoFactory:
    """Factory for creating servo instances with proper initialization."""

    @staticmethod
    def _validate_servo_config(servo_name: ServoName, min_pulse: float, max_pulse: float) -> None:
        """Validate servo pulse width configuration.

        Args:
            servo_name: The servo name for error messaging.
            min_pulse: The minimum pulse width in microseconds.
            max_pulse: The maximum pulse width in microseconds.

        Raises:
            ValueError: If validation fails.
        """
        if min_pulse == max_pulse:
            raise ValueError(
                ERR_SERVO_CONFIG_MIN_MAX_EQUAL.format(servo_name=servo_name, min_pulse=min_pulse, max_pulse=max_pulse)
            )

        if not SERVO_PULSE_WIDTH_MIN <= min_pulse <= SERVO_PULSE_WIDTH_MAX:
            raise ValueError(
                ERR_SERVO_CONFIG_MIN_PULSE_OUT_OF_RANGE.format(
                    servo_name=servo_name,
                    min_pulse=min_pulse,
                    SERVO_PULSE_WIDTH_MIN=SERVO_PULSE_WIDTH_MIN,
                    SERVO_PULSE_WIDTH_MAX=SERVO_PULSE_WIDTH_MAX,
                )
            )

        if not SERVO_PULSE_WIDTH_MIN <= max_pulse <= SERVO_PULSE_WIDTH_MAX:
            raise ValueError(
                ERR_SERVO_CONFIG_MAX_PULSE_OUT_OF_RANGE.format(
                    servo_name=servo_name,
                    max_pulse=max_pulse,
                    SERVO_PULSE_WIDTH_MIN=SERVO_PULSE_WIDTH_MIN,
                    SERVO_PULSE_WIDTH_MAX=SERVO_PULSE_WIDTH_MAX,
                )
            )

    @staticmethod
    def create(servo_name: ServoName) -> Servo:
        """Create and initialize a servo instance.

        Args:
            servo_name: The ServoName enum value for the servo to create.

        Returns:
            A fully initialized Servo instance.

        Raises:
            RuntimeError: If PCA9685 board fails to initialize or servo not found.
        """
        config_provider = ConfigProvider()

        # Initialize PCA9685 board
        pca9685 = PCA9685()
        pca9685.activate_board()

        # Get servo configuration
        servo_config = config_provider.get_servo_config(servo_name)
        channel = pca9685.get_channel(servo_config.channel)

        # Validate pulse width configuration
        ServoFactory._validate_servo_config(servo_name, servo_config.min_pulse, servo_config.max_pulse)

        # Infer joint type and load calibration spec
        joint_type = JointType.from_servo_name(servo_name)
        limits = JOINT_ANGLE_LIMITS[joint_type]
        min_angle = limits.min_angle
        max_angle = limits.max_angle
        rest_angle = limits.rest_angle

        # Create and return servo instance
        return Servo(
            channel,
            min_pulse=servo_config.min_pulse,
            max_pulse=servo_config.max_pulse,
            min_angle=min_angle,
            max_angle=max_angle,
            rest_angle=rest_angle,
        )
