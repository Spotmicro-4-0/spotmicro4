"""
Buzzer handler for controlling audio feedback on GPIO.
"""

import time
from RPi import GPIO  # type: ignore
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.singleton import Singleton
from spotmicroai.motion_controller.constants import BEEP_DURATION


class Buzzer(metaclass=Singleton):
    """Controls the buzzer hardware for audio feedback.

    Attributes
    ----------
    config : Config
        Configuration object for motion controller settings
    port : int
        GPIO port number for the buzzer
    """

    config = Config()

    def __init__(self):
        """Initialize the Buzzer."""
        self.port = self.config.motion_controller.buzzer.gpio_port
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.port, GPIO.OUT)
        GPIO.output(self.port, False)

    def beep(self):
        """Plays a beep sound by activating the buzzer for the configured beep duration."""
        GPIO.output(self.port, True)
        time.sleep(BEEP_DURATION)
        GPIO.output(self.port, False)
