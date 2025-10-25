"""
PCA9685 handler for controlling PWM board on I2C.
"""

from adafruit_pca9685 import PCA9685 as _PCA9685  # type: ignore
from board import SCL, SDA  # type: ignore
import busio  # type: ignore

from spotmicroai import Singleton
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

    def __init__(self):
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
