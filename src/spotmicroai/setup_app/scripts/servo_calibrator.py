"""Servo calibration hardware control module.

Manages PCA9685 board initialization and direct servo control during calibration.
Provides pulse width and angle-based servo positioning with safety clamping.
"""

from spotmicroai.configuration import ConfigProvider, ServoName
from spotmicroai.drivers import PCA9685, Servo


class ServoCalibrator:
    """Manages servo hardware control during calibration."""

    def __init__(self, servo_name: ServoName):
        """Initialize the servo calibrator.

        Args:
            servo_name: The ServoName enum value for the servo to calibrate.

        Raises:
            RuntimeError: If PCA9685 board fails to initialize or servo not found.
        """
        self.servo_name = servo_name
        self.config_provider = ConfigProvider()

        # Initialize PCA9685 board
        pca9685 = PCA9685()
        pca9685.activate_board()

        # Get servo configuration
        servo_config = self.config_provider.get_servo(servo_name)
        channel = pca9685.get_channel(servo_config.channel)

        # Create servo instance
        self.servo = Servo(
            channel,
            min_pulse=servo_config.min_pulse,
            max_pulse=servo_config.max_pulse,
            actuation_range=servo_config.range,
            rest_angle=servo_config.rest_angle,
        )

    @staticmethod
    def clamp_angle(angle: float) -> float:
        """Clamp angle to valid servo range (0-270 degrees).

        Args:
            angle: The desired angle in degrees.

        Returns:
            Clamped angle within 0-270 degree range.
        """
        return max(0, min(270, angle))

    @staticmethod
    def clamp_pulse(pulse: float) -> float:
        """Clamp pulse width to valid range (500-2500 microseconds).

        Args:
            pulse: The desired pulse width in microseconds.

        Returns:
            Clamped pulse width within 500-2500 µs range.
        """
        return max(500, min(2500, pulse))

    def set_servo_angle(self, angle: float) -> float:
        """Move servo to provided angle.

        Args:
            angle: The target angle in degrees.

        Returns:
            The actual angle set after clamping.
        """
        target = self.clamp_angle(angle)
        self.servo.angle = target
        return target

    def set_servo_pulse(self, pulse_us: float) -> float:
        """Set servo pulse width directly.

        Used for precise calibration positioning. Converts microsecond pulse
        width to PWM duty cycle for the PCA9685 channel.

        Args:
            pulse_us: The target pulse width in microseconds.

        Returns:
            The actual pulse width set after clamping.
        """
        target = self.clamp_pulse(pulse_us)
        self.servo.channel.duty_cycle = int((target / 20000) * 65535)
        return target

    def get_current_pulse_width(self) -> int:
        """Get current pulse width from servo.

        Returns:
            The current pulse width in microseconds.
        """
        # Pulse width = (duty_cycle / 65535) * 20000
        return int((self.servo.channel.duty_cycle / 65535) * 20000)
