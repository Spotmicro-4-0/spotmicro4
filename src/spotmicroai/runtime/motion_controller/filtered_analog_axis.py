import math
import time


class FilteredAnalogAxis:
    """
    Encapsulates analog joystick axis smoothing, deadzone filtering,
    and optional non-linear scaling.
    """

    def __init__(
        self,
        deadzone: float = 0.03,
        smoothing: float = 0.4,
        nonlinear_exp: float = 1.3,
        update_callback=None,
        min_update_interval: float = 0.01,
    ):
        self.deadzone = deadzone
        self.alpha = smoothing
        self.nonlinear_exp = nonlinear_exp
        self.callback = update_callback
        self.min_update_interval = min_update_interval

        self._last_value = 0.0
        self._last_update_time = 0.0

    def update(self, raw: float):
        """Process a new joystick event and return a filtered value."""
        now = time.time()

        # --- Deadzone ---
        if abs(raw) < self.deadzone:
            raw = 0.0

        # --- Low-pass filter (smooth transitions) ---
        smoothed = self._last_value + self.alpha * (raw - self._last_value)

        # --- Nonlinear scaling (optional exponential response) ---
        if self.nonlinear_exp != 1.0:
            smoothed = math.copysign(abs(smoothed) ** self.nonlinear_exp, smoothed)

        # --- Rate limiting ---
        if now - self._last_update_time < self.min_update_interval:
            return self._last_value

        # --- Save and callback ---
        self._last_update_time = now
        self._last_value = smoothed

        if self.callback:
            self.callback(smoothed)

        return smoothed

    # Strong smoothing near the center and weaker at high speeds
    def update_adaptive(self, raw: float):
        now = time.time()
        if abs(raw) < self.deadzone:
            raw = 0.0

        # Adaptive smoothing: less smoothing when input is large
        adaptive_alpha = self.alpha * (1 - abs(raw)) + 0.7 * abs(raw)
        smoothed = self._last_value + adaptive_alpha * (raw - self._last_value)

        if self.nonlinear_exp != 1.0:
            smoothed = math.copysign(abs(smoothed) ** self.nonlinear_exp, smoothed)

        if now - self._last_update_time < self.min_update_interval:
            return self._last_value

        self._last_update_time = now
        self._last_value = smoothed
        if self.callback:
            self.callback(smoothed)
        return smoothed

    def reset(self):
        self._last_value = 0.0
        self._last_update_time = 0.0

    @property
    def value(self):
        return self._last_value
