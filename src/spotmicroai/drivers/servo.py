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
        self._servo = adafruit_servo.Servo(
            pwm_channel,
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            actuation_range=actuation_range,
        )
        self._range = actuation_range
        self._rest_angle = rest_angle
        self._last_angle = None

        # Move servo to its defined rest position immediately
        self.set_angle(rest_angle)

    def set_angle(self, angle: float) -> float:
        """
        Move the servo to the requested angle, clamped to [0, actuation_range].

        Args:
            angle: Desired logical angle in degrees.

        Returns:
            The clamped angle actually applied to the servo.
        """
        clamp = max(0.0, min(self._range, angle))
        try:
            self._servo.angle = clamp
            self._last_angle = clamp
        except Exception as e:
            print(f"[WARN] Servo command failed: {e}")
        return clamp

    @property
    def angle(self) -> float:
        """Return the last commanded angle."""
        return self._last_angle if self._last_angle is not None else self._rest_angle
