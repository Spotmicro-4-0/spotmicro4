#!/home/pi/spotmicroai/venv/bin/python3 -u

import sys
from pick import pick
import time
import RPi.GPIO as GPIO

from spotmicroai.utilities.log import Logger
from spotmicroai.utilities.config import Config

log = Logger().setup_logger('Buzzer Test')

log.info('Testing Buzzer...')

gpio_port = Config().get('buzzer[0].gpio_port')

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

while True:
    options = {
        0: 'Short Beep',
        1: 'Long Beep',
        2: 'Multiple Beeps' ,
        3: 'Exit' 
    }

    title = 'Select the pattern you want to test'

    screen_options = list(options.values())

    selected_option, selected_index = pick(screen_options, title)

    if (selected_index == 0):
        GPIO.output(gpio_port, True)
        time.sleep(1)
        GPIO.output(gpio_port, False)
    elif (selected_index == 1):
        GPIO.output(gpio_port, True)
        time.sleep(3)
        GPIO.output(gpio_port, False)
    elif (selected_index == 2):
        GPIO.output(gpio_port, True)
        time.sleep(1)
        GPIO.output(gpio_port, False)
        time.sleep(1)
        GPIO.output(gpio_port, True)
        time.sleep(1)
        GPIO.output(gpio_port, False)
    else:
        GPIO.output(gpio_port, False)
        sys.exit(0)
