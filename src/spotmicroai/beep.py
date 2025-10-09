#!/home/pi/spotmicroai/venv/bin/python3 -u

import sys
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)
GPIO.output(21, True)
time.sleep(1)
GPIO.output(21, False)

sys.exit(1)
