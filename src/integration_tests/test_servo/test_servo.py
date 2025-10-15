#!/home/pi/spotmicroai/venv/bin/python3 -u

import busio # type: ignore
from board import SCL, SDA # type: ignore
from adafruit_pca9685 import PCA9685 # type: ignore
from adafruit_motor import servo # type: ignore
from pick import pick # type: ignore
import time
import os
import sys
import RPi.GPIO as GPIO # type: ignore

from spotmicroai.utilities.log import Logger
from spotmicroai.utilities.config import Config

log = Logger().setup_logger('Servo Range Test')

log.info('Testing Servo...')

pca = None
gpio_port = Config().get('abort_controller[0].gpio_port')
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

i2c = busio.I2C(SCL, SDA)

while True:
    options = {
        0: 'front_shoulder_left  - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_REST_ANGLE)) + ']',
        1: 'front_leg_left       - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_REST_ANGLE)) + ']',
        2: 'front_foot_left      - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_REST_ANGLE)) + ']',
        3: 'front_shoulder_right - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_REST_ANGLE)) + ']',
        4: 'front_leg_right      - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_CHANNEL)) + '] - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_REST_ANGLE)) + ']',
        5: 'front_foot_right     - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_CHANNEL)) + '] - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_REST_ANGLE)) + ']',
        6: 'rear_shoulder_left   - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_REST_ANGLE)) + ']',
        7: 'rear_leg_left        - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_REST_ANGLE)) + ']',
        8: 'rear_foot_left       - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_REST_ANGLE)) + ']',
        9: 'rear_shoulder_right  - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_REST_ANGLE)) + ']',
        10: 'rear_leg_right       - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_REST_ANGLE)) + ']',
        11: 'rear_foot_right      - PCA[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_PCA9685)) + '] CHANNEL[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_CHANNEL)) + ']  - ANGLE[' + str(Config().get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_REST_ANGLE)) + ']'}

    title = 'Select the Servo you want to test the range for'

    screen_options = list(options.values())

    selected_option, selected_index = pick(screen_options, title)

    PCA9685_ADDRESS, PCA9685_REFERENCE_CLOCK_SPEED, PCA9685_FREQUENCY, CHANNEL, MIN_PULSE, MAX_PULSE, REST_ANGLE = Config().get_by_section_name(selected_option.split()[0])

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
                raise Exception('Invalid Input')

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
            pca.deinit() # type: ignore
