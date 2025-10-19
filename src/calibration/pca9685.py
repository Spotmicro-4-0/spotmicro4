"""
Thin wrapper around the Adafruit PCA9685 controller to hide third-party details.
"""

from typing import Optional

from adafruit_pca9685 import PCA9685 as _PCA9685  # type: ignore[import]
import board  # type: ignore[import]
import busio  # type: ignore[import]


class PCA9685:
    """
    Wrapper that exposes the minimal functionality needed by the calibration tool.
    """

    _shared_bus: Optional[busio.I2C] = None

    def __init__(self, address: int, frequency: int) -> None:
        if PCA9685._shared_bus is None:
            try:
                PCA9685._shared_bus = busio.I2C(board.SCL, board.SDA)
            except Exception as exc:  # pragma: no cover - hardware access
                raise RuntimeError("Failed to initialise I2C bus for PCA9685.") from exc

        try:
            self._controller = _PCA9685(PCA9685._shared_bus, address=address)
            self._controller.frequency = frequency
        except Exception as exc:  # pragma: no cover - hardware access
            raise RuntimeError("Failed to initialise PCA9685 controller.") from exc

    def channel(self, index: int):
        """Return the requested PWM channel interface."""
        return self._controller.channels[index]

    @property
    def frequency(self) -> int:
        """Expose the configured PWM frequency."""
        return self._controller.frequency
