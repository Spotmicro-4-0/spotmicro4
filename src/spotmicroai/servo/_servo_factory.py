"""Servo calibration hardware control module.

Manages PCA9685 board initialization and direct servo control during calibration.
Provides pulse width and angle-based servo positioning with safety clamping.
"""

from spotmicroai.configuration._config_provider import ConfigProvider, ServoName
from spotmicroai.drivers import PCA9685
from spotmicroai.servo._servo import Servo


class ServoFactory:
    """Factory for creating servo instances with proper initialization."""

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

        # Create and return servo instance
        return Servo(
            servo_name,
            channel,
            min_pulse=servo_config.min_pulse,
            max_pulse=servo_config.max_pulse,
            actuation_range=servo_config.range,
            rest_angle=servo_config.rest_angle,
        )
