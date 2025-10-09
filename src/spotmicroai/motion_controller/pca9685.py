from board import SCL, SDA  # type: ignore
import busio  # type: ignore
from adafruit_pca9685 import PCA9685  # type: ignore
from spotmicroai.utilities.config import Config

class PCA9685Board:
    def __init__(self):
        self.i2c = busio.I2C(SCL, SDA)
        self.pca9685 = None
        self.address = int(Config().get(Config.MOTION_CONTROLLER_PCA9685_ADDRESS), 0)
        self.reference_clock_speed = int(Config().get(Config.MOTION_CONTROLLER_PCA9685_REFERENCE_CLOCK_SPEED))
        self.frequency = int(Config().get(Config.MOTION_CONTROLLER_PCA9685_FREQUENCY))

    def activate(self):
        self.pca9685 = PCA9685(self.i2c, address=self.address, reference_clock_speed=self.reference_clock_speed)
        self.pca9685.frequency = self.frequency
        print('PCA9685 board activated')

    def deactivate(self):
        if self.pca9685:
            self.pca9685.deinit()
            self.pca9685 = None
        print('PCA9685 board deactivated')

    def get_channel(self, channel_index):
        if self.pca9685 is None:
            raise RuntimeError('PCA9685 board not activated')
        return self.pca9685.channels[channel_index]
