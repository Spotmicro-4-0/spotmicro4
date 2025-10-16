import time
from RPi import GPIO  # type: ignore
from spotmicroai.utilities.config import Config
from spotmicroai.utilities.singleton import Singleton


class Buzzer(metaclass=Singleton):
    config = Config()

    def __init__(self):
        self.port = self.config.motion_controller.buzzer.gpio_port
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.port, GPIO.OUT)
        GPIO.output(self.port, False)

    def beep(self):
        GPIO.output(self.port, True)
        time.sleep(0.5)
        GPIO.output(self.port, False)
