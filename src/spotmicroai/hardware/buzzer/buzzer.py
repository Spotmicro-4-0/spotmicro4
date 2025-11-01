"""
Buzzer handler for controlling audio feedback on GPIO.
"""

import time

from RPi import GPIO  # type: ignore

from spotmicroai import Singleton
from spotmicroai.configuration._config_provider import ConfigProvider
import spotmicroai.constants as constants


class Buzzer(metaclass=Singleton):
    """Controls the buzzer hardware for audio feedback.

    Attributes
    ----------
    config : ConfigProvider
        Configuration object for motion controller settings
    _port : int
        GPIO port number for the buzzer
    """

    config_provider = ConfigProvider()

    def __init__(self):
        """Initialize the Buzzer."""
        self._port = self.config_provider.get_buzzer_gpio_port()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._port, GPIO.OUT)
        GPIO.output(self._port, False)

    def beep(self):
        """Plays a beep sound by activating the buzzer for the configured beep duration."""
        GPIO.output(self._port, True)
        time.sleep(constants.BEEP_DURATION)
        GPIO.output(self._port, False)
