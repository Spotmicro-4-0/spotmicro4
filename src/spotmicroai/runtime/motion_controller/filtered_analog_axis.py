import math
import time


class FilteredAnalogAxis:
    """
    Encapsulates analog joystick axis smoothing, deadzone filtering,
    and optional non-linear scaling.
    """

    def __init__(
        self,
        deadzone: float = 0.05,
        smoothing: float = 0.1,
        nonlinear_exp: float = 1.0,
        update_callback=None,
        min_update_interval: float = 0.02,
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

    def reset(self):
        self._last_value = 0.0
        self._last_update_time = 0.0

    @property
    def value(self):
        return self._last_value
