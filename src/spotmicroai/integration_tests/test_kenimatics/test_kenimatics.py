#!/home/pi/spotmicroai/venv/bin/python3 -u

import os
import sys
import time

import RPi.GPIO as GPIO
from adafruit_motor import servo
from adafruit_pca9685 import PCA9685
from board import SCL, SDA
import busio
from pick import pick

from spotmicroai.configuration._config_provider import ConfigProvider
from spotmicroai.logger import Logger

LEG_SERVO_OFFSET = 120


class ServoConfig:
    PCA9685_address = None
    PCA9685_reference_clock_speed = None
    pca9685_frequency = None
    channel = None
    min_pulse = None
    max_pulse = None
    rest_angle = None

    i2c = None
    pca = None

    servo = None

    def __init__(self, servo_name):
        log.info(f'Initializing ServoConfig with name: {servo_name}')

        config_provider = ConfigProvider()
        servo = config_provider.get_servo_config(servo_name)
        pca = config_provider.motion_controller.pca9685
        i2c = busio.I2C(SCL, SDA)

        self.i2c = i2c
        self.pca9685_address = pca.address
        self.pca9685_reference_clock_speed = pca.reference_clock_speed
        self.pca9685_frequency = pca.frequency
        self.channel = servo.channel
        self.min_pulse = servo.min_pulse
        self.max_pulse = servo.max_pulse
        self.rest_angle = servo.rest_angle

        log.info('Initializing ServoConfig with values:')
        log.info(f'PCA9685_address: {self.pca9685_address}')
        log.info(f'PCA9685_reference_clock_speed: {self.pca9685_reference_clock_speed}')
        log.info(f'PCA9685_frequency: {self.pca9685_frequency}')
        log.info(f'Channel: {self.channel}')
        log.info(f'Min Pulse: {self.min_pulse}')
        log.info(f'Max Pulse: {self.max_pulse}')
        log.info(f'Rest Angle: {self.rest_angle}')

        self.pca = PCA9685(
            i2c, address=int(self.pca9685_address, 0), reference_clock_speed=self.pca9685_reference_clock_speed
        )
        self.pca.frequency = self.pca9685_frequency

        log.info(f'Creating Servo object on channel: {self.channel}')
        self.servo = servo.Servo(self.pca.channels[self.channel])
        log.info(f'Setting pulse width range with min: {self.min_pulse} and max: {self.max_pulse}')
        self.servo.set_pulse_width_range(min_pulse=int(self.min_pulse), max_pulse=int(self.max_pulse))
        log.info(f'Setting angle to rest angle: {self.rest_angle}')

    def deinit(self):
        self.pca.deinit()


class KenimaticsTest:
    shoulder_servo_config = None
    leg_servo_config = None
    foot_servo_config = None

    def __init__(self, shoulder_servo_name, leg_servo_name, foot_servo_name):
        log.info('Initializing KenimaticsTest with values:')
        log.info(f'Shoulder: {shoulder_servo_name}')
        log.info(f'Leg: {leg_servo_name}')
        log.info(f'Foot: {foot_servo_name}')

        self.shoulder_servo_config = ServoConfig(shoulder_servo_name)
        self.leg_servo_config = ServoConfig(leg_servo_name)
        self.foot_servo_config = ServoConfig(foot_servo_name)

    def deinit(self):
        log.info('Deinitializing KenimaticsTest')
        self.shoulder_servo_config.deinit()
        self.leg_servo_config.deinit()
        self.foot_servo_config.deinit()

    def move(self, omega, theta, phi):
        log.info('Moving KenimaticsTest with values:')
        log.info(f'Omega - Shoulder rest angle: {omega}')
        log.info(f'Theta - Leg rest angle: {theta}')
        log.info(f'Phi: - Foot rest angle {phi}')

        self.shoulder_servo_config.servo.angle = omega
        self.leg_servo_config.servo.angle = theta
        self.foot_servo_config.servo.angle = phi


log = Logger().setup_logger('Kenimatics Test')
log.info('Testing Kenimatics...')

config = ConfigProvider()
gpio_port = config.abort_controller.gpio_port
GPIO.setmode(GPIO.BCM)
GPIO.setup(gpio_port, GPIO.OUT)
GPIO.output(gpio_port, False)

kenimaticsTest = None

while True:
    options = {0: 'Rear Left', 1: 'Rear Right', 2: 'Front Left', 3: 'Front Right'}

    title = 'Select the limb you want to test'

    screen_options = list(options.values())
    selected_option, selected_index = pick(screen_options, title)

    if selected_index == 0:
        log.info('Selected option: Rear Left')
        kenimaticsTest = KenimaticsTest('rear_shoulder_left', 'rear_leg_left', 'rear_feet_left')
    elif selected_index == 1:
        log.info('Selected option: Rear Right')
        kenimaticsTest = KenimaticsTest('rear_shoulder_right', 'rear_leg_right', 'rear_feet_right')
    elif selected_index == 2:
        log.info('Selected option: Front Left')
        kenimaticsTest = KenimaticsTest('front_shoulder_left', 'front_leg_left', 'front_feet_left')
    elif selected_index == 3:
        log.info('Selected option: Front Right')
        kenimaticsTest = KenimaticsTest('front_shoulder_right', 'front_leg_right', 'front_feet_right')
    else:
        raise Exception('Invalid input')

    while True:
        try:
            user_input = input("Write the X Y Z distances you want move the servos to separated by spaces: ")
            os.system('clear')
            if user_input == 'menu' or user_input == 'm':
                break
            if user_input == 'exit' or user_input == 'e':
                sys.exit(0)

            try:
                x, y, z = user_input.split(' ')
                x = int(x)
                y = int(y)
                z = int(z)
            except:
                log.error('Invalid input. Try again')

            log.info('Calculating angles...')
            phi, theta, omega = InverseKinematics(x, y, z)
            log.info(f'phi: {phi}, theta: {theta}, omega: {omega}')

            if selected_index == 0:  # rear left
                log.info('Selected Rear Left')
                theta = min(theta + LEG_SERVO_OFFSET, 180)
                phi = max(phi, 0)
            elif selected_index == 1:  # rear right
                log.info('Selected Rear Right')
                omega = 180 - omega
                theta = max(180 - (theta + LEG_SERVO_OFFSET), 0)
                phi = 180 - max(phi, 0)
            elif selected_index == 2:  # front left
                log.info('Selected Front Left')
                omega = 180 - omega
                theta = min(theta + LEG_SERVO_OFFSET, 180)
                phi = max(phi, 0)
            elif selected_index == 3:  # front right
                log.info('Selected Rear Left')
                theta = min(180 - (phi + LEG_SERVO_OFFSET), 0)
                phi = 180 - max(phi, 0)

            kenimaticsTest.move(omega, theta, phi)

            time.sleep(0.1)
            log.info('')
            log.info('')  # blank lines for readability

        except Exception as e:
            log.error(f"Error occurred: {e}")
            GPIO.output(gpio_port, False)
            GPIO.cleanup()
            sys.exit(0)
