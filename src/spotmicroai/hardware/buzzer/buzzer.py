"""
Buzzer handler for controlling audio feedback on GPIO.
"""

import threading
import time

from RPi import GPIO  # type: ignore

from spotmicroai.singleton import Singleton
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
        self._beep_thread = None
        self._stop_beep = threading.Event()
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._port, GPIO.OUT)
        GPIO.output(self._port, False)

    def beep(self):
        """Plays a beep sound by activating the buzzer for the configured beep duration."""
        if self._beep_thread and self._beep_thread.is_alive():
            return

        self._stop_beep.clear()
        self._beep_thread = threading.Thread(target=self._do_beep, daemon=True)
        self._beep_thread.start()

    def stop(self):
        """Stops any ongoing beep immediately."""
        self._stop_beep.set()
        GPIO.output(self._port, False)

    def _do_beep(self):
        """Internal method that performs the blocking beep operation in a separate thread."""
        try:
            GPIO.output(self._port, True)
            time.sleep(constants.BEEP_DURATION)
        finally:
            GPIO.output(self._port, False)
