"""
PCA9685 handler for controlling PWM board on I2C.
"""

from board import SCL, SDA  # type: ignore
import busio  # type: ignore
from adafruit_pca9685 import PCA9685  # type: ignore
from spotmicroai.utilities.singleton import Singleton
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.log import Logger

log = Logger().setup_logger('Motion controller')


class PCA9685Board(metaclass=Singleton):
    """Controls the PCA9685 PWM board for servo control.

    Attributes
    ----------
    config : Config
        Configuration object for motion controller settings
    i2c : busio.I2C
        I2C bus interface
    pca9685 : PCA9685 or None
        PCA9685 board instance
    address : int
        I2C address of the PCA9685 board
    reference_clock_speed : int
        Reference clock speed for the PCA9685
    frequency : int
        PWM frequency
    """

    config = Config()

    def __init__(self):
        """Initialize the PCA9685Board."""
        self.i2c = busio.I2C(SCL, SDA)
        self.pca9685 = None
        self.address = int(self.config.motion_controller.pca9685.address, 0)
        self.reference_clock_speed = int(self.config.motion_controller.pca9685.reference_clock_speed)
        self.frequency = int(self.config.motion_controller.pca9685.frequency)

    def activate_board(self):
        """Activate the PCA9685 board."""
        self.pca9685 = PCA9685(self.i2c, address=self.address, reference_clock_speed=self.reference_clock_speed)
        self.pca9685.frequency = self.frequency
        log.info('PCA9685 board activated')

    def deactivate_board(self):
        """Deactivate the PCA9685 board."""
        if self.pca9685:
            self.pca9685.deinit()
            self.pca9685 = None
        log.info('PCA9685 board deactivated')

    def get_channel(self, channel_index):
        """Get a PWM channel by index.

        Parameters
        ----------
        channel_index : int
            The index of the PWM channel
        """
        if self.pca9685 is None:
            raise RuntimeError('PCA9685 board not activated')
        return self.pca9685.channels[channel_index]
