import json
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional

from spotmicroai.core.utilities.dot_dict import DotDict
from spotmicroai.core.utilities.log import Logger
from spotmicroai.core.utilities.singleton import Singleton

log = Logger().setup_logger('Configuration')


# TODO: add validation
class Config(metaclass=Singleton):
    """
    Clean configuration management using dot notation.

    Usage examples:
        config = Config()

        # Clean dot notation access
        gpio = config.abort_controller.gpio_port
        address = config.lcd_screen_controller.address
        channel = config.motion_controller.servos.front_shoulder_left.channel

        # Dictionary-style access
        gpio = config['abort_controller']['gpio_port']

        # Safe get with default
        device = config.remote_controller.get('device', 'js0')

        # Get servo by name
        servo = config.get_servo('front_shoulder_left')

        # Access all servos
        servos = config.motion_controller.servos
    """

    def __init__(self):
        self._raw_data: Dict[str, Any] = {}
        self._config: Optional[DotDict] = None

        try:
            log.debug('Loading configuration...')
            self.load_config()
            self.list_modules()
        except Exception as e:
            log.error('Problem while loading the configuration file: %s', e)

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            config_path = Path.home() / 'spotmicroai.json'
            default_path = Path.home() / 'spotmicroai' / 'spotmicroai.default'

            # Copy default if config doesn't exist
            if not config_path.exists() and default_path.exists():
                shutil.copyfile(default_path, config_path)

            with open(config_path, encoding='utf-8') as json_file:
                self._raw_data = json.load(json_file)
                self._config = DotDict(self._raw_data)
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

    def list_modules(self):
        """List all configured modules"""
        modules = ', '.join(self._raw_data.keys())
        log.info('Detected configuration for the modules: %s', modules)

    def save_config(self):
        """Save current configuration back to JSON file"""
        try:
            config_path = Path.home() / 'spotmicroai.json'
            with open(config_path, 'w', encoding='utf-8') as outfile:
                json.dump(self._raw_data, outfile, indent=2)
            log.info('Configuration saved to %s', config_path)
        except Exception as e:
            log.error("Problem saving the configuration file: %s", e)

    def __getattr__(self, key: str) -> Any:
        """
        Enable dot notation access on Config object itself.
        Example: config.motion_controller instead of config._config.motion_controller
        """
        if key.startswith('_'):
            # Internal attributes
            return object.__getattribute__(self, key)
        return getattr(self._config, key)

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access"""
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Safe get with default value"""
        if self._config is None:
            return default
        return self._config.get(key, default)

    # Convenience methods for common access patterns

    def get_servo(self, servo_name: str) -> DotDict:
        """
        Get servo configuration by name.

        Args:
            servo_name: Name like 'front_shoulder_left', 'rear_leg_right', etc.

        Returns:
            DotDict with channel, min_pulse, max_pulse, rest_angle, range

        Example:
            servo = config.get_servo('front_shoulder_left')
            channel = servo.channel
            min_pulse = servo.min_pulse
            range_degrees = servo.range
        """
        try:
            return self.motion_controller.servos[servo_name]
        except (AttributeError, KeyError):
            log.error("Servo '%s' not found in configuration", servo_name)
            raise

    def get_all_servos(self) -> Dict[str, DotDict]:
        """
        Get all servo configurations.

        Returns:
            Dictionary of servo name -> servo config

        Example:
            servos = config.get_all_servos()
            for name, servo in servos.items():
                print(f"{name}: channel {servo.channel}")
        """
        return self.motion_controller.servos.to_dict()

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
        try:
            return self.motion_controller.poses[pose_name]
        except (AttributeError, KeyError):
            log.error("Pose '%s' not found in configuration", pose_name)
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to regular dictionary"""
        return self._raw_data
