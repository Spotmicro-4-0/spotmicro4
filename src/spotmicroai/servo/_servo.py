"""
Servo wrapper that abstracts the Adafruit servo helper.

This version uses real calibration values (min_pulse, max_pulse, actuation_range)
and sets the servo to a defined rest position on initialization.
"""

from adafruit_motor import servo as adafruit_servo  # type: ignore


class Servo:
    """
    Lightweight wrapper providing a stable, safety-clamped interface
    over the Adafruit Servo class.

    Example:
        s = Servo(
            pwm_channel=board.get_channel(config.channel),
            min_pulse=1463,
            max_pulse=2441,
            min_angle=60,
            max_angle=120,
            rest_angle=90,
        )
        s.set_angle(65)
    """

    def __init__(
        self,
        pwm_channel,
        min_pulse: float,
        max_pulse: float,
        min_angle: float,
        max_angle: float,
        rest_angle: float,
    ) -> None:
        """
        Initialize the servo with calibration values.

        Args:
            pwm_channel: The PCA9685 or PWM channel controlling the servo.
            min_pulse: Minimum pulse width in microseconds (µs) at the servo's minimum angle.
            max_pulse: Maximum pulse width in microseconds (µs) at the servo's maximum angle.
                If min_pulse > max_pulse, the servo is inverted.
            min_angle: Minimum physical angle in degrees.
            max_angle: Maximum physical angle in degrees.
            rest_angle: Default angle to move to on initialization.
        """
        self._pwm_channel = pwm_channel
        self._min_angle = min_angle
        self._max_angle = max_angle
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse
        self._rest_angle = rest_angle

        # Determine if servo is inverted
        self._is_inverted = min_pulse > max_pulse

        # Calculate range for Adafruit servo (always positive)
        self._pulse_range = abs(max_pulse - min_pulse)
        self._angle_range = abs(max_angle - min_angle)

        # Initialize Adafruit servo with absolute values for range
        self._servo = adafruit_servo.Servo(
            pwm_channel,
            min_pulse=min(min_pulse, max_pulse),
            max_pulse=max(min_pulse, max_pulse),
            actuation_range=self._angle_range,
        )

        # Initialize with rest angle
        self.angle = rest_angle

    @property
    def angle(self) -> float:
        """Get the current physical angle in degrees, computed from the current pulse."""
        return self._pulse_to_angle(self.pulse)

    @angle.setter
    def angle(self, value: float) -> None:
        """
        Move the servo to the requested physical angle.

        Clamps the angle to [min_angle, max_angle], handles inverted servos,
        and keeps the pulse value in sync.

        Args:
            value: Target angle in degrees
        """
        # Clamp to valid angle range
        clamped_angle = max(self._min_angle, min(self._max_angle, value))

        # Convert physical angle to pulse width
        pulse = self._angle_to_pulse(clamped_angle)
        # Set the pulse
        self.pulse = pulse

    @property
    def pulse(self) -> float:
        """Get the current pulse width in microseconds."""
        # Calculate pulse from the current duty cycle
        # Reverse of _pulse_to_duty_cycle: pulse = (duty_cycle / 65535) * 20000
        return (self._pwm_channel.duty_cycle / 65535.0) * 20000

    @pulse.setter
    def pulse(self, value: float) -> None:
        """Set the servo to a specific pulse width and update the angle.

        Args:
            value: The pulse width in microseconds to set
        """
        # Clamp pulse to valid range
        min_pulse_abs = min(self._min_pulse, self._max_pulse)
        max_pulse_abs = max(self._min_pulse, self._max_pulse)
        clamped_pulse = max(min_pulse_abs, min(max_pulse_abs, value))
        self._write_pulse(clamped_pulse)

    def set_pulse_unsafe(self, value: float) -> None:
        """Set the servo pulse width directly, bypassing safety clamps (for calibration)."""
        self._write_pulse(value)

    def _write_pulse(self, pulse_us: float) -> None:
        """Low-level helper to send a pulse width to the PWM channel."""
        self._pwm_channel.duty_cycle = (pulse_us / 20000.0) * 65535

    @property
    def min_pulse(self) -> float:
        """Get the minimum pulse width in microseconds."""
        return self._min_pulse

    @property
    def max_pulse(self) -> float:
        """Get the maximum pulse width in microseconds."""
        return self._max_pulse

    @property
    def min_angle(self) -> float:
        """Get the minimum angle in degrees."""
        return self._min_angle

    @property
    def max_angle(self) -> float:
        """Get the maximum angle in degrees."""
        return self._max_angle

    @property
    def rest_angle(self) -> float:
        """Get the rest angle in degrees."""
        return self._rest_angle

    def recalibrate(self, min_pulse: float, max_pulse: float, new_range: float) -> None:
        """
        Recalibrate the servo with new pulse width limits and actuation range.

        This method allows dynamic adjustment of the servo's calibration parameters
        without recreating the Servo object. It updates both the Adafruit Servo's
        internal mapping and this wrapper's stored configuration values.

        Args:
            min_pulse: Minimum pulse width in microseconds (µs) corresponding to
                the lowest physical angle.
            max_pulse: Maximum pulse width in microseconds (µs) corresponding to
                the highest physical angle.
            new_range: Total angular sweep of the servo in degrees.

        Example:
            s.recalibrate(min_pulse=1000, max_pulse=1500, new_range=130)
        """
        self._min_pulse = min_pulse
        self._max_pulse = max_pulse
        self._is_inverted = min_pulse > max_pulse
        self._pulse_range = abs(max_pulse - min_pulse)

        # Update Adafruit servo with new calibration
        self._servo.set_pulse_width_range(min(min_pulse, max_pulse), max(min_pulse, max_pulse))
        self._servo.actuation_range = new_range

        self.angle = self._rest_angle

    def _angle_to_pulse(self, angle: float) -> float:
        """Convert a physical angle to its corresponding pulse width.

        Handles inverted servos correctly.
        """
        # Clamp angle
        clamped = max(self._min_angle, min(self._max_angle, angle))

        # Normalize between 0–1
        normalized = (clamped - self._min_angle) / self._angle_range

        if self._is_inverted:
            # For inverted servos, reverse direction and base off _max_pulse
            return self._max_pulse + (1.0 - normalized) * (self._min_pulse - self._max_pulse)
        else:
            # Normal mapping
            return self._min_pulse + normalized * (self._max_pulse - self._min_pulse)

    def _pulse_to_angle(self, pulse: float) -> float:
        """Convert a pulse width to its corresponding physical angle.

        Args:
            pulse: Pulse width in microseconds

        Returns:
            Physical angle in degrees
        """
        # Handle inversion explicitly to keep math direction correct
        if self._is_inverted:
            normalized = (self._min_pulse - pulse) / (self._min_pulse - self._max_pulse)
        else:
            normalized = (pulse - self._min_pulse) / (self._max_pulse - self._min_pulse)

        # Compute angle using integer math for consistency
        angle = self._min_angle + round(normalized * self._angle_range)

        # Clamp just in case of rounding edge cases
        if angle < self._min_angle:
            angle = self._min_angle
        elif angle > self._max_angle:
            angle = self._max_angle

        return angle

    @property
    def is_inverted(self) -> bool:
        """Get whether the servo is inverted or not."""
        return self._is_inverted
