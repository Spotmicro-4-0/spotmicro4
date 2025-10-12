from spotmicroai.motion_controller.models.servo_config import ServoConfig
from spotmicroai.singleton import Singleton
from spotmicroai.utilities.config import Config

class ServoConfigService(metaclass=Singleton):
    """A class containing the configurations for all the 12 servos.

    This singleton class loads the static servo configurations from the spotmicroai.json file
    and serves as an abstraction layer in front of the Config utility class, providing
    easy access to immutable servo settings for the entire application.

    Used to track the configurations of all servos

    Attributes:
        rear_shoulder_left: The configuration for the left rear shoulder servo
        rear_leg_left: The configuration for the left rear leg servo
        rear_foot_left: The configuration for the left rear foot servo
        rear_shoulder_right: The configuration for the right rear shoulder servo
        rear_leg_right: The configuration for the right rear leg servo
        rear_foot_right: The configuration for the right rear foot servo
        front_shoulder_left: The configuration for the left front shoulder servo
        front_leg_left: The configuration for the left front leg servo
        front_foot_left: The configuration for the left front foot servo
        front_shoulder_right: The configuration for the right front shoulder servo
        front_leg_right: The configuration for the right front leg servo
        front_foot_right: The configuration for the right front foot servo
    """
    rear_shoulder_left: ServoConfig
    rear_leg_left: ServoConfig
    rear_foot_left: ServoConfig
    rear_shoulder_right: ServoConfig
    rear_leg_right: ServoConfig
    rear_foot_right: ServoConfig
    front_shoulder_left: ServoConfig
    front_leg_left: ServoConfig
    front_foot_left: ServoConfig
    front_shoulder_right: ServoConfig
    front_leg_right: ServoConfig
    front_foot_right: ServoConfig

    def __init__(self):
        config = Config()

        self.rear_shoulder_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_LEFT_REST_ANGLE)
        )
        self.rear_leg_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_LEFT_REST_ANGLE)
        )
        self.rear_foot_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_LEFT_REST_ANGLE)
        )
        self.rear_shoulder_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_SHOULDER_RIGHT_REST_ANGLE)
        )
        self.rear_leg_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_LEG_RIGHT_REST_ANGLE)
        )
        self.rear_foot_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_REAR_FOOT_RIGHT_REST_ANGLE)
        )
        self.front_shoulder_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_LEFT_REST_ANGLE)
        )
        self.front_leg_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_LEFT_REST_ANGLE)
        )
        self.front_foot_left = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_LEFT_REST_ANGLE)
        )
        self.front_shoulder_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_SHOULDER_RIGHT_REST_ANGLE)
        )
        self.front_leg_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_LEG_RIGHT_REST_ANGLE)
        )
        self.front_foot_right = ServoConfig(
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_CHANNEL),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_MIN_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_MAX_PULSE),
            config.get(Config.MOTION_CONTROLLER_SERVOS_FRONT_FOOT_RIGHT_REST_ANGLE)
        )