"""
Servo wrapper that abstracts the Adafruit servo helper.

This version uses real calibration values (min_pulse, max_pulse, actuation_range)
and sets the servo to a defined rest position on initialization.
"""

from adafruit_motor import servo as adafruit_servo  # type: ignore[import]


class Servo:
    """
    Lightweight wrapper providing a stable, safety-clamped interface
    over the Adafruit Servo class.

    Example:
        s = Servo(
            board.get_channel(config.channel),
            min_pulse=1463,
            max_pulse=2441,
            actuation_range=130,
            rest_angle=20,
        )
        s.set_angle(65)
    """

    def __init__(
        self,
        pwm_channel,
        min_pulse: int,
        max_pulse: int,
        actuation_range: int,
        rest_angle: float,
    ) -> None:
        """
        Initialize the servo with calibration values.

        Args:
            pwm_channel: The PCA9685 or PWM channel controlling the servo.
            min_pulse: Minimum pulse width in microseconds (µs) at 0°.
            max_pulse: Maximum pulse width in microseconds (µs) at actuation_range°.
            actuation_range: Total angular span (degrees) defined by calibration.
            rest_angle: Default angle to move to on initialization.
        """
        self._pwm_channel = pwm_channel
        self._servo = adafruit_servo.Servo(
            pwm_channel,
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            actuation_range=actuation_range,
        )
        self._range = actuation_range
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse
        self._rest_angle = rest_angle
        self._last_angle = None

    @property
    def angle(self) -> float:
        """Return the last commanded angle."""
        return self._last_angle if self._last_angle is not None else self._rest_angle

    @angle.setter
    def angle(self, value: float) -> None:
        """Set the servo to the requested angle."""
        clamp = max(0.0, min(self._range, value))
        self._servo.angle = clamp
        self._last_angle = clamp

    @property
    def min_pulse(self) -> int:
        """Get the minimum pulse width in microseconds."""
        return self._min_pulse

    @min_pulse.setter
    def min_pulse(self, value: int) -> None:
        """Set the minimum pulse width in microseconds."""
        self._min_pulse = value

    @property
    def max_pulse(self) -> int:
        """Get the maximum pulse width in microseconds."""
        return self._max_pulse

    @max_pulse.setter
    def max_pulse(self, value: int) -> None:
        """Set the maximum pulse width in microseconds."""
        self._max_pulse = value

    @property
    def rest_angle(self) -> float:
        """Get the rest angle in degrees."""
        return self._rest_angle

    @rest_angle.setter
    def rest_angle(self, value: float) -> None:
        """Set the rest angle in degrees."""
        self._rest_angle = value

    @property
    def range(self) -> int:
        """Get the actuation range in degrees."""
        return self._range

    @property
    def channel(self):
        """Get the underlying PWM channel for direct pulse control."""
        return self._pwm_channel
