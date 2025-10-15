#!/home/pi/spotmicroai/venv/bin/python3 -u

import busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
from pick import pick
import time
import os
import sys
import RPi.GPIO as GPIO

from spotmicroai.utilities.log import Logger
from spotmicroai.utilities.config import Config

log = Logger().setup_logger('Shutdown SERVOS')

log.info('Shutting down...')

pca = None
gpio_port = Config().get('abort_controller[0].gpio_port')
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

i2c = busio.I2C(SCL, SDA)

options = [
    'rear_shoulder_left',
    'rear_leg_left',
    'rear_feet_left',
    'rear_shoulder_right',
    'rear_leg_right',
    'rear_feet_right',
    'front_shoulder_left',
    'front_leg_left',
    'front_feet_left',
    'front_shoulder_right',
    'front_leg_right',
    'front_feet_right']  

for selected_option in options:
    PCA9685_ADDRESS, PCA9685_REFERENCE_CLOCK_SPEED, PCA9685_FREQUENCY, CHANNEL, MIN_PULSE, MAX_PULSE, REST_ANGLE = Config().get_by_section_name(selected_option)
    try:
        pca = PCA9685(i2c, address=int(PCA9685_ADDRESS, 0), reference_clock_speed=PCA9685_REFERENCE_CLOCK_SPEED)
        pca.frequency = PCA9685_FREQUENCY

        active_servo = servo.Servo(pca.channels[CHANNEL])
        active_servo.set_pulse_width_range(min_pulse=MIN_PULSE, max_pulse=MAX_PULSE)
        active_servo.angle = None
        time.sleep(0.1)
    finally:
        pca.deinit()
