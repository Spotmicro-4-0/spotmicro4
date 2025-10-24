#!/home/pi/spotmicroai/venv/bin/python3 -u

import time

import RPi.GPIO as GPIO
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio

from spotmicroai.configuration import ConfigProvider
from spotmicroai.logger import Logger

log = Logger().setup_logger('Test Motion')

log.info('Testing Motion...')

config_provider = ConfigProvider()
pca = config_provider.motion_controller.pca9685

pca9685_address = int(pca.address, 0)
pca9685_reference_clock_speed = pca.reference_clock_speed
pca9685_frequency = pca.frequency

log.info('Use the command "i2cdetect -y 1" to list your i2c devices connected and')
log.info('write your pca9685 i2c address(es) and settings in your configuration file ~/spotmicroai/spotmicroai.json')
log.info('There is configuration present for the pca9685 board')

input("Press Enter to start the tests...")

pca = None

gpio_port = config_provider.abort_controller.gpio_port

try:

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(gpio_port, GPIO.OUT)

    GPIO.output(gpio_port, False)
    time.sleep(1)

    i2c = busio.I2C(SCL, SDA)

    pca = PCA9685(i2c, address=pca9685_address, reference_clock_speed=pca9685_reference_clock_speed)
    pca.frequency = 50

    for x in range(0, 15):
        active_servo = servo.Servo(pca.channels[x])
        active_servo.set_pulse_width_range(min_pulse=500, max_pulse=2500)

        active_servo.angle = 90
        time.sleep(0.1)
        active_servo.angle = 90
        time.sleep(0.1)

    time.sleep(1)

    for x in range(0, 15):
        active_servo = servo.Servo(pca.channels[x])
        active_servo.set_pulse_width_range(min_pulse=500, max_pulse=2500)

        active_servo.angle = 110
        time.sleep(0.1)
        active_servo.angle = 110
        time.sleep(0.1)

    time.sleep(1)

    input("Press Enter to cut power in servos...")

    GPIO.output(gpio_port, True)
    time.sleep(1)

    input("Press Enter to reenable power in servos...")

    GPIO.output(gpio_port, False)
    time.sleep(1)


finally:
    GPIO.output(gpio_port, True)
    pca.deinit()
