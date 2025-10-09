import json
import sys
import os
from spotmicroai.utilities.log import Logger
import jmespath  # http://jmespath.org/tutorial.html
import shutil
from pathlib import Path

log = Logger().setup_logger('Configuration')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=Singleton):
    ABORT_CONTROLLER_GPIO_PORT = 'abort_controller[0].gpio_port'
    LCD_SCREEN_CONTROLLER_I2C_ADDRESS = 'lcd_screen_controller[0].lcd_screen[0].address'
    REMOTE_CONTROLLER_CONTROLLER_DEVICE = 'remote_controller_controller[0].remote_controller[0].device'

    MOTION_CONTROLLER_PCA9685_ADDRESS = 'motion_controller[0].pca9685[0].address'
    MOTION_CONTROLLER_PCA9685_REFERENCE_CLOCK_SPEED = 'motion_controller[0].pca9685[0].reference_clock_speed'
    MOTION_CONTROLLER_PCA9685_FREQUENCY = 'motion_controller[0].pca9685[0].frequency'

    MOTION_CONTROLLER_BUZZER_GPIO_PORT = 'motion_controller[0].buzzer[0].gpio_port'

    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_PCA9685 = 'motion_controller[0].servos[0].rear_shoulder_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_CHANNEL = 'motion_controller[0].servos[0].rear_shoulder_left[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].rear_shoulder_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].rear_shoulder_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].rear_shoulder_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_PCA9685 = 'motion_controller[0].servos[0].rear_leg_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_CHANNEL = 'motion_controller[0].servos[0].rear_leg_left[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].rear_leg_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].rear_leg_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].rear_leg_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_PCA9685 = 'motion_controller[0].servos[0].rear_feet_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_CHANNEL = 'motion_controller[0].servos[0].rear_feet_left[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].rear_feet_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].rear_feet_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].rear_feet_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_PCA9685 = 'motion_controller[0].servos[0].rear_shoulder_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_CHANNEL = 'motion_controller[0].servos[0].rear_shoulder_right[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].rear_shoulder_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].rear_shoulder_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].rear_shoulder_right[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_PCA9685 = 'motion_controller[0].servos[0].rear_leg_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_CHANNEL = 'motion_controller[0].servos[0].rear_leg_right[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].rear_leg_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].rear_leg_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].rear_leg_right[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_PCA9685 = 'motion_controller[0].servos[0].rear_feet_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_CHANNEL = 'motion_controller[0].servos[0].rear_feet_right[0].channel'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].rear_feet_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].rear_feet_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_REAR_FEET_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].rear_feet_right[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_PCA9685 = 'motion_controller[0].servos[0].front_shoulder_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_CHANNEL = 'motion_controller[0].servos[0].front_shoulder_left[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].front_shoulder_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].front_shoulder_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].front_shoulder_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_PCA9685 = 'motion_controller[0].servos[0].front_leg_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_CHANNEL = 'motion_controller[0].servos[0].front_leg_left[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].front_leg_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].front_leg_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].front_leg_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_PCA9685 = 'motion_controller[0].servos[0].front_feet_left[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_CHANNEL = 'motion_controller[0].servos[0].front_feet_left[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_MIN_PULSE = 'motion_controller[0].servos[0].front_feet_left[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_MAX_PULSE = 'motion_controller[0].servos[0].front_feet_left[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_LEFT_REST_ANGLE = 'motion_controller[0].servos[0].front_feet_left[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_PCA9685 = 'motion_controller[0].servos[0].front_shoulder_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_CHANNEL = 'motion_controller[0].servos[0].front_shoulder_right[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].front_shoulder_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].front_shoulder_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].front_shoulder_right[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_PCA9685 = 'motion_controller[0].servos[0].front_leg_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_CHANNEL = 'motion_controller[0].servos[0].front_leg_right[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].front_leg_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].front_leg_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].front_leg_right[0].rest_angle'

    MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_PCA9685 = 'motion_controller[0].servos[0].front_feet_right[0].pca9685'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_CHANNEL = 'motion_controller[0].servos[0].front_feet_right[0].channel'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_MIN_PULSE = 'motion_controller[0].servos[0].front_feet_right[0].min_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_MAX_PULSE = 'motion_controller[0].servos[0].front_feet_right[0].max_pulse'
    MOTION_CONTROLLER_SERVOS_FRONT_FEET_RIGHT_REST_ANGLE = 'motion_controller[0].servos[0].front_feet_right[0].rest_angle'

    MOTION_CONTROLLER_GAIT = 'motion_controller[0].gait'
    MOTION_CONTROLLER_POSES = 'motion_controller[0].poses'

    values = {}

    def __init__(self):

        try:
            log.debug('Loading configuration...')

            self.load_config()
            self.list_modules()

        except Exception as e:
            log.error('Problem while loading the configuration file', e)

    def load_config(self):
        try:
            if not os.path.exists(str(Path.home()) + '/spotmicroai.json'):
                shutil.copyfile(str(Path.home()) + '/spotmicroai/spotmicroai.default',
                                str(Path.home()) + '/spotmicroai.json')

            with open(str(Path.home()) + '/spotmicroai.json') as json_file:
                self.values = json.load(json_file)
                # log.debug(json.dumps(self.values, indent=4, sort_keys=True))

        except Exception as e:
            log.error("Configuration file don't exist or is not a valid json, aborting.")
            sys.exit(1)

    def list_modules(self):
        log.info('Detected configuration for the modules: ' + ', '.join(self.values.keys()))

    def save_config(self):
        try:
            with open(os.path.expanduser('~/spotmicroai.json'), 'w') as outfile:
                json.dump(self.values, outfile)
        except Exception as e:
            log.error("Problem saving the configuration file", e)

    def get(self, search_pattern):
        log.debug(search_pattern + ': ' + str(jmespath.search(search_pattern, self.values)))
        return jmespath.search(search_pattern, self.values)

    def get_by_section_name(self, search_pattern):

        CHANNEL = 'motion_controller[0].servos[0].' + str(search_pattern) + '[0].channel'
        MIN_PULSE = 'motion_controller[0].servos[0].' + str(search_pattern) + '[0].min_pulse'
        MAX_PULSE = 'motion_controller[0].servos[0].' + str(search_pattern) + '[0].max_pulse'
        REST_ANGLE = 'motion_controller[0].servos[0].' + str(search_pattern) + '[0].rest_angle'

        PCA9685_ADDRESS = 'motion_controller[0].pca9685[0].address'
        PCA9685_REFERENCE_CLOCK_SPEED = 'motion_controller[0].pca9685[0].reference_clock_speed'
        PCA9685_FREQUENCY = 'motion_controller[0].pca9685[0].frequency'

        log.info('PCA9685_ADDRESS: ' + str(jmespath.search(PCA9685_ADDRESS, self.values)))
        log.info('PCA9685_REFERENCE_CLOCK_SPEED: ' + str(jmespath.search(PCA9685_REFERENCE_CLOCK_SPEED, self.values)))
        log.info('PCA9685_FREQUENCY: ' + str(jmespath.search(PCA9685_FREQUENCY, self.values)))
        log.info('CHANNEL: ' + str(jmespath.search(CHANNEL, self.values)))
        log.info('MIN_PULSE: ' + str(jmespath.search(MIN_PULSE, self.values)))
        log.info('MAX_PULSE: ' + str(jmespath.search(MAX_PULSE, self.values)))
        log.info('REST_ANGLE: ' + str(jmespath.search(REST_ANGLE, self.values)))

        return jmespath.search(PCA9685_ADDRESS, self.values), jmespath.search(PCA9685_REFERENCE_CLOCK_SPEED, self.values), jmespath.search(PCA9685_FREQUENCY, self.values), jmespath.search(CHANNEL, self.values), jmespath.search(MIN_PULSE, self.values), jmespath.search(MAX_PULSE, self.values), jmespath.search(REST_ANGLE, self.values)
