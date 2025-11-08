"""
PCA9685 handler for controlling PWM board on I2C.
"""

from adafruit_pca9685 import PCA9685 as _PCA9685  # type: ignore
from board import SCL, SDA  # type: ignore
import busio  # type: ignore

from spotmicroai.singleton import Singleton
from spotmicroai.configuration import ConfigProvider
from spotmicroai.logger import Logger

log = Logger().setup_logger('Motion controller')


class PCA9685(metaclass=Singleton):
    """Controls the PCA9685 PWM board for servo control.

    Attributes
    ----------
    config : Config
        Configuration object for motion controller settings
    _i2c : busio.I2C
        I2C bus interface
    _pca9685 : PCA9685 or None
        PCA9685 board instance
    _address : int
        I2C address of the PCA9685 board
    _reference_clock_speed : int
        Reference clock speed for the PCA9685
    _frequency : int
        PWM frequency
    """

    config_provider = ConfigProvider()

    def __init__(self) -> None:
        """Initialize the PCA9685Board."""
        self._i2c = busio.I2C(SCL, SDA)
        self._pca9685 = None
        self._address: int = self.config_provider.get_pca9685_address()
        self._reference_clock_speed: int = self.config_provider.get_pca9685_reference_clock_speed()
        self._frequency: int = self.config_provider.get_pca9685_frequency()

    def activate_board(self):
        """Activate the PCA9685 board."""
        self._pca9685 = _PCA9685(self._i2c, address=self._address, reference_clock_speed=self._reference_clock_speed)
        self._pca9685.frequency = self._frequency

    def deactivate_board(self):
        """Deactivate the PCA9685 board."""
        if self._pca9685:
            self._pca9685.deinit()
            self._pca9685 = None

    def is_active(self) -> bool:
        """Check if the PCA9685 board is activated.

        Returns
        -------
        bool
            True if board is activated, False otherwise
        """
        return self._pca9685 is not None

    def get_channel(self, channel_index):
        """Get a PWM channel by index.

        Parameters
        ----------
        channel_index : int
            The index of the PWM channel
        """
        if self._pca9685 is None:
            raise RuntimeError('PCA9685 board not activated')
        return self._pca9685.channels[channel_index]

    def write_all_channels(self, pulse_widths_us: list[float]) -> None:
        """Write all 16 channels in a single batched I²C transaction.

        Uses the PCA9685 auto-increment feature to write all channel registers
        (LED0_ON_L through LED15_OFF_H) in one contiguous write starting at
        register 0x06. This reduces I²C overhead from 12-16 transactions to 1.

        Parameters
        ----------
        pulse_widths_us : list[float]
            List of 16 pulse widths in microseconds (one per channel).
            Channels not in use should have neutral values (typically 1500µs).

        Raises
        ------
        RuntimeError
            If PCA9685 board not activated or invalid pulse count
        """
        if self._pca9685 is None:
            raise RuntimeError('PCA9685 board not activated')

        if len(pulse_widths_us) != 16:
            raise ValueError(f'Expected 16 pulse widths, got {len(pulse_widths_us)}')

        # Build 64-byte payload: 4 bytes per channel × 16 channels
        # Each channel has: ON_L, ON_H, OFF_L, OFF_H
        buffer = bytearray(64)

        for channel_idx, pulse_us in enumerate(pulse_widths_us):
            # Convert pulse width to 12-bit PWM count (0-4095)
            # Standard servo frame = 20ms = 20000µs at 50Hz
            # 12-bit range: 4096 steps
            pwm_count = int((pulse_us / 20000.0) * 4095)

            # Clamp to valid 12-bit range
            pwm_count = max(0, min(4095, pwm_count))

            # Standard servo timing: ON at count 0, OFF at calculated count
            on_value = 0
            off_value = pwm_count

            # Pack into buffer: ON_L, ON_H, OFF_L, OFF_H
            base_idx = channel_idx * 4
            buffer[base_idx] = on_value & 0xFF
            buffer[base_idx + 1] = (on_value >> 8) & 0xFF
            buffer[base_idx + 2] = off_value & 0xFF
            buffer[base_idx + 3] = (off_value >> 8) & 0xFF

        # Write to register 0x06 (LED0_ON_L) with auto-increment
        # The PCA9685 will auto-increment through all 64 registers
        LED0_ON_L_REGISTER = 0x06
        self._i2c.writeto(self._address, bytes([LED0_ON_L_REGISTER]) + buffer)
