import time
from RPi import GPIO  # type: ignore
from spotmicroai.utilities.config import Config

class Buzzer:
    def __init__(self):
        self.port = Config().get(Config.MOTION_CONTROLLER_BUZZER_GPIO_PORT)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.port, GPIO.OUT)
        GPIO.output(self.port, False)

    def beep(self):
        GPIO.output(self.port, True)
        time.sleep(0.5)
        GPIO.output(self.port, False)