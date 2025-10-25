#!/home/pi/spotmicroai/venv/bin/python3 -u

import os
import sys
import time
from typing import cast

import RPi.GPIO as GPIO  # type: ignore
from adafruit_motor import servo  # type: ignore
from adafruit_pca9685 import PCA9685  # type: ignore
from board import SCL, SDA  # type: ignore
import busio  # type: ignore
from pick import pick  # type: ignore

from spotmicroai.configuration import ConfigProvider, ServoName
from spotmicroai.logger import Logger

log = Logger().setup_logger('Servo Range Test')

log.info('Testing Servo...')

pca = None
config_provider = ConfigProvider()
gpio_port = config_provider.abort_controller.gpio_port
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

i2c = busio.I2C(SCL, SDA)

pca_addr = config_provider.motion_controller.pca9685.address

while True:
    servo_name_enums = list(ServoName)
    options = {}
    for i, servo_enum in enumerate(servo_name_enums):
        name = servo_enum.value
        servo = config_provider.get_servo(name)
        options[i] = f'{name} - PCA[{pca_addr}] CHANNEL[{servo.channel}] - ANGLE[{servo.rest_angle}]'

    title = 'Select the Servo you want to test the range for'

    screen_options = list(options.values())

    selected_option, selected_index = pick(screen_options, title)

    servo_enum = servo_name_enums[cast(int, selected_index)]
    servo_name = servo_enum.value
    servo = config_provider.get_servo(servo_name)
    pca = config_provider.motion_controller.pca9685

    PCA9685_ADDRESS = pca.address
    PCA9685_REFERENCE_CLOCK_SPEED = pca.reference_clock_speed
    PCA9685_FREQUENCY = pca.frequency
    CHANNEL = servo.channel
    MIN_PULSE = servo.min_pulse
    MAX_PULSE = servo.max_pulse
    REST_ANGLE = servo.rest_angle

    min = MIN_PULSE
    max = MAX_PULSE
    rest = REST_ANGLE

    prev_min = min
    prev_max = max

    while True:

        try:
            user_input = input("Write the MIN value and press Enter, or press Enter for the default: ")

            if user_input == 'menu' or user_input == 'm':
                # active_servo.angle = None
                break
            if user_input == 'exit' or user_input == 'e':
                # active_servo.angle = None
                sys.exit(0)

            if len(user_input.split()) == 1:
                rest = user_input.split(' ')[0]
            elif len(user_input.split()) == 3:
                min, max, rest = user_input.split(' ')
            elif user_input == '':
                min = prev_min
                max = prev_max
            else:
                raise ValueError('Invalid Input')

            pca = PCA9685(i2c, address=int(PCA9685_ADDRESS, 0), reference_clock_speed=PCA9685_REFERENCE_CLOCK_SPEED)
            pca.frequency = PCA9685_FREQUENCY

            print(f'min: {min}, max: {max}, rest: {rest}')
            active_servo = servo.Servo(pca.channels[CHANNEL])
            active_servo.set_pulse_width_range(min_pulse=int(min), max_pulse=int(max))
            active_servo.angle = int(rest)

            time.sleep(0.1)

            prev_min = min
            prev_max = max
        finally:
            pca.deinit()  # type: ignore
