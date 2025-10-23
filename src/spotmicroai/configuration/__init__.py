from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List

from spotmicroai import Singleton
from spotmicroai.logger import Logger

log = Logger().setup_logger('Configuration')


@dataclass
class ServoConfig:
    """Servo configuration dataclass"""

    channel: int
    min_pulse: int
    max_pulse: int
    rest_angle: int
    range: int


class ServoName(Enum):
    """Enum for all 12 servo names"""

    FRONT_SHOULDER_LEFT = 'front_shoulder_left'
    FRONT_LEG_LEFT = 'front_leg_left'
    FRONT_FOOT_LEFT = 'front_foot_left'
    FRONT_SHOULDER_RIGHT = 'front_shoulder_right'
    FRONT_LEG_RIGHT = 'front_leg_right'
    FRONT_FOOT_RIGHT = 'front_foot_right'
    REAR_SHOULDER_LEFT = 'rear_shoulder_left'
    REAR_LEG_LEFT = 'rear_leg_left'
    REAR_FOOT_LEFT = 'rear_foot_left'
    REAR_SHOULDER_RIGHT = 'rear_shoulder_right'
    REAR_LEG_RIGHT = 'rear_leg_right'
    REAR_FOOT_RIGHT = 'rear_foot_right'


class ConfigProvider(metaclass=Singleton):
    """
    Configuration management for SpotMicroAI.

    Usage examples:
        config = ConfigProvider()

        # Get values
        gpio_port = config.get_abort_gpio_port()
        servo = config.get_servo('front_shoulder_left')
        pose = config.get_pose('stand')

        # Set values
        config.set_abort_gpio_port(18)
        config.set_servo_channel('front_shoulder_left', 7)
        config.save_config()
    """

    def __init__(self):
        self._raw_data: Dict[str, Any] = {}

        try:
            log.debug('Loading configuration...')
            self.load_config()
        except Exception as e:
            log.error('Problem while loading the configuration file: %s', e)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_path = Path.home() / 'spotmicroai.json'
            default_path = Path.home() / 'spotmicroai' / 'configuration' / 'spotmicroai.template'

            # Copy default if config doesn't exist
            if not config_path.exists() and default_path.exists():
                shutil.copyfile(default_path, config_path)

            with open(config_path, encoding='utf-8') as json_file:
                self._raw_data = json.load(json_file)
                log.debug('Configuration loaded from %s', config_path)

        except FileNotFoundError:
            log.error("Configuration file doesn't exist, aborting.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            log.error("Configuration file is not valid JSON: %s", e)
            sys.exit(1)
        except Exception as e:
            log.error("Problem loading configuration: %s", e)
            sys.exit(1)

    def save_config(self):
        """Save current configuration back to JSON file"""
        try:
            config_path = Path.home() / 'spotmicroai.json'
            with open(config_path, 'w', encoding='utf-8') as outfile:
                json.dump(self._raw_data, outfile, indent=2)
            log.info('Configuration saved to %s', config_path)
        except Exception as e:
            log.error("Problem saving the configuration file: %s", e)

    # Abort GPIO Port
    def get_abort_gpio_port(self) -> int:
        """Get the GPIO port for abort controller"""
        return self._raw_data.get('abort_gpio_port', 17)

    def set_abort_gpio_port(self, port: int) -> None:
        """Set the GPIO port for abort controller"""
        self._raw_data['abort_gpio_port'] = port

    # LCD Screen Address
    def get_lcd_screen_address(self) -> str:
        """Get the I2C address for LCD screen"""
        return self._raw_data.get('lcd_screen_address', '0x27')

    def set_lcd_screen_address(self, address: str) -> None:
        """Set the I2C address for LCD screen"""
        self._raw_data['lcd_screen_address'] = address

    # Remote Controller Device
    def get_remote_controller_device(self) -> str:
        """Get the device path for remote controller"""
        return self._raw_data.get('remote_controller_device', 'js0')

    def set_remote_controller_device(self, device: str) -> None:
        """Set the device path for remote controller"""
        self._raw_data['remote_controller_device'] = device

    # Buzzer GPIO Port
    def get_buzzer_gpio_port(self) -> int:
        """Get the GPIO port for buzzer"""
        return self._raw_data.get('buzzer_gpio_port', 21)

    def set_buzzer_gpio_port(self, port: int) -> None:
        """Set the GPIO port for buzzer"""
        self._raw_data['buzzer_gpio_port'] = port

    # PCA9685 Address
    def get_pca9685_address(self) -> int:
        """Get the I2C address for PCA9685 servo controller

        Returns:
            int: The I2C address (e.g., 0x40)
        """
        return int(self._raw_data.get('pca9685_address', 0x40))

    def set_pca9685_address(self, address: int) -> None:
        """Set the I2C address for PCA9685 servo controller

        Args:
            address: The I2C address as an integer (e.g., 0x40 or 64)
        """
        self._raw_data['pca9685_address'] = address

    # PCA9685 Frequency
    def get_pca9685_frequency(self) -> int:
        """Get the PWM frequency for PCA9685"""
        return int(self._raw_data.get('pca9685_frequency', 50))

    def set_pca9685_frequency(self, frequency: int) -> None:
        """Set the PWM frequency for PCA9685"""
        self._raw_data['pca9685_frequency'] = frequency

    # PCA9685 Reference Clock Speed
    def get_pca9685_reference_clock_speed(self) -> int:
        """Get the reference clock speed for PCA9685"""
        return int(self._raw_data.get('pca9685_reference_clock_speed', 25000000))

    def set_pca9685_reference_clock_speed(self, speed: int) -> None:
        """Set the reference clock speed for PCA9685"""
        self._raw_data['pca9685_reference_clock_speed'] = speed

    # Servos
    def _get_servo_key(self, servo_name: ServoName) -> str:
        """Get the flattened key for a servo"""
        key = f'servo_{servo_name.value}'
        if key not in self._raw_data:
            log.error("Servo '%s' not found in configuration", servo_name.value)
            raise KeyError(f"Servo '{servo_name.value}' not found")
        return key

    def get_servo(self, servo_name: ServoName) -> ServoConfig:
        """
        Get servo configuration by enum.

        Args:
            servo_name: ServoName enum value

        Returns:
            ServoConfig dataclass with all servo parameters

        Example:
            servo = config.get_servo(ServoName.FRONT_SHOULDER_LEFT)
            channel = servo.channel
            min_pulse = servo.min_pulse
        """
        key = self._get_servo_key(servo_name)
        data = self._raw_data[key]
        return ServoConfig(
            channel=data['channel'],
            min_pulse=data['min_pulse'],
            max_pulse=data['max_pulse'],
            rest_angle=data['rest_angle'],
            range=data['range'],
        )

    def set_servo(self, servo_name: ServoName, servo: ServoConfig) -> None:
        """
        Set entire servo configuration.

        Args:
            servo_name: ServoName enum value
            servo: ServoConfig dataclass with parameters
        """
        key = self._get_servo_key(servo_name)
        self._raw_data[key] = {
            'channel': servo.channel,
            'min_pulse': servo.min_pulse,
            'max_pulse': servo.max_pulse,
            'rest_angle': servo.rest_angle,
            'range': servo.range,
        }

    def get_servo_channel(self, servo_name: ServoName) -> int:
        """Get the PWM channel for a servo"""
        servo = self.get_servo(servo_name)
        return servo.channel

    def set_servo_channel(self, servo_name: ServoName, channel: int) -> None:
        """Set the PWM channel for a servo"""
        servo = self.get_servo(servo_name)
        servo.channel = channel
        self.set_servo(servo_name, servo)

    def get_servo_min_pulse(self, servo_name: ServoName) -> int:
        """Get the minimum pulse width for a servo"""
        servo = self.get_servo(servo_name)
        return servo.min_pulse

    def set_servo_min_pulse(self, servo_name: ServoName, pulse: int) -> None:
        """Set the minimum pulse width for a servo"""
        servo = self.get_servo(servo_name)
        servo.min_pulse = pulse
        self.set_servo(servo_name, servo)

    def get_servo_max_pulse(self, servo_name: ServoName) -> int:
        """Get the maximum pulse width for a servo"""
        servo = self.get_servo(servo_name)
        return servo.max_pulse

    def set_servo_max_pulse(self, servo_name: ServoName, pulse: int) -> None:
        """Set the maximum pulse width for a servo"""
        servo = self.get_servo(servo_name)
        servo.max_pulse = pulse
        self.set_servo(servo_name, servo)

    def get_servo_rest_angle(self, servo_name: ServoName) -> int:
        """Get the rest angle for a servo"""
        servo = self.get_servo(servo_name)
        return servo.rest_angle

    def set_servo_rest_angle(self, servo_name: ServoName, angle: int) -> None:
        """Set the rest angle for a servo"""
        servo = self.get_servo(servo_name)
        servo.rest_angle = angle
        self.set_servo(servo_name, servo)

    def get_servo_range(self, servo_name: ServoName) -> int:
        """Get the angle range for a servo"""
        servo = self.get_servo(servo_name)
        return servo.range

    def set_servo_range(self, servo_name: ServoName, range_degrees: int) -> None:
        """Set the angle range for a servo"""
        servo = self.get_servo(servo_name)
        servo.range = range_degrees
        self.set_servo(servo_name, servo)

    def get_all_servos(self) -> Dict[ServoName, ServoConfig]:
        """Get all servo configurations as ServoConfig dataclasses"""
        servos = {}
        for servo_enum in ServoName:
            try:
                servo = self.get_servo(servo_enum)
                servos[servo_enum] = servo
            except KeyError:
                log.warning("Servo '%s' not found", servo_enum.value)
        return servos

    # Walking Cycle
    def get_walking_cycle(self) -> List[List[int]]:
        """Get the walking cycle pose sequence"""
        return self._raw_data.get('walking_cycle', [])

    def set_walking_cycle(self, cycle: List[List[int]]) -> None:
        """Set the walking cycle pose sequence"""
        self._raw_data['walking_cycle'] = cycle

    # Poses
    def get_pose(self, pose_name: str) -> List[List[int]]:
        """
        Get pose configuration by name.

        Args:
            pose_name: Name like 'stand', 'sit', 'hi', etc.

        Returns:
            List of joint positions

        Example:
            stand_pose = config.get_pose('stand')
        """
        poses = self._raw_data.get('poses', {})
        if pose_name not in poses:
            log.error("Pose '%s' not found in configuration", pose_name)
            raise KeyError(f"Pose '{pose_name}' not found")
        return poses[pose_name]

    def set_pose(self, pose_name: str, pose: List[List[int]]) -> None:
        """
        Set pose configuration.

        Args:
            pose_name: Name of the pose
            pose: List of joint positions
        """
        if 'poses' not in self._raw_data:
            self._raw_data['poses'] = {}
        self._raw_data['poses'][pose_name] = pose

    def get_all_poses(self) -> Dict[str, List[List[int]]]:
        """Get all pose configurations"""
        return self._raw_data.get('poses', {})
