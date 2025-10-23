"""
Servo wrapper that abstracts the Adafruit servo helper.
"""

from typing import Optional

from adafruit_motor import servo as adafruit_servo  # type: ignore[import]


class Servo:
    """
    Lightweight wrapper providing a stable interface over the Adafruit Servo class.
    """

    def __init__(
        self,
        pwm_channel,
        *,
        min_pulse: int,
        max_pulse: int,
        actuation_range: int,
        neutral_angle: float,
        min_angle: float,
        max_angle: float,
    ) -> None:
        self._servo = adafruit_servo.Servo(
            pwm_channel,
            min_pulse=min_pulse,
            max_pulse=max_pulse,
            actuation_range=actuation_range,
        )
        self._min_angle = min_angle
        self._max_angle = max_angle
        self.set_angle(neutral_angle)

    def set_angle(self, angle: float) -> float:
        """
        Move the servo to the requested angle (clamped to safe bounds).
        """
        bounded = max(self._min_angle, min(self._max_angle, angle))
        self._servo.angle = bounded
        return bounded

    @property
    def angle(self) -> Optional[float]:
        """Expose the last angle commanded to the servo."""
        return self._servo.angle
