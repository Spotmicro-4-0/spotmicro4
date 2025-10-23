from typing import Any, Dict

### Inverse Kinematics Constants ###
# Constants for inverse kinematics calculations (in mm)
LEG_LENGTH = 110
FOOT_LENGTH = 138
SHOULDER_LENGTH = 57
SAFE_NEUTRAL = (0.0, 0.0, 0.0)

### Motion Controller Constants ###
# Motion controller constants
LEG_SERVO_OFFSET = 120
FOOT_SERVO_OFFSET = 0
ROTATION_OFFSET = 40
INACTIVITY_TIME = 10

# Walking speed
MAX_WALKING_SPEED = 15

# Lean and height multipliers
LEAN_MULTIPLIER = 50
HEIGHT_MULTIPLIER = 40

# Rotation increment
ROTATION_INCREMENT = 0.025

# Buzzer
BEEP_DURATION = 0.5

# Debounce Button
DEFAULT_DEBOUNCE_TIME = 0.5

FRAME_RATE_HZ = 50
FRAME_DURATION = 1.0 / FRAME_RATE_HZ
TELEMETRY_UPDATE_INTERVAL = 2  # Update telemetry display every N frames

DEFAULT_SLEEP = 0.1


# Controller Constants
# ===============================
# General Timing and Publishing
# ===============================
# Rate (in Hz) at which the current joystick state is broadcast to the motion queue.
PUBLISH_RATE_HZ = 20.0
# Delay between read loop iterations (in seconds)
READ_LOOP_SLEEP = 0.005
# ===============================
# Analog Input Filtering
# ===============================
# Deadzone threshold for analog stick drift (0.0–1.0).
DEADZONE = 0.08
# Minimum absolute change in axis value required before updating state.
AXIS_UPDATE_THRESHOLD = 0.01
# ===============================
# Reconnection and Device Search
# ===============================
# Delay between joystick access retries when device is not yet ready or permissions unavailable.
RECONNECT_RETRY_DELAY = 2.0
# Delay between failed device detection cycles.
DEVICE_SEARCH_INTERVAL = 2.5

"""
Reusable Singleton metaclass.
"""


class Singleton(type):
    """
    Metaclass that enforces single-instance creation for subclasses.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


__all__ = [
    'LEG_LENGTH',
    'FOOT_LENGTH',
    'SHOULDER_LENGTH',
    'SAFE_NEUTRAL',
    'LEG_SERVO_OFFSET',
    'FOOT_SERVO_OFFSET',
    'ROTATION_OFFSET',
    'INACTIVITY_TIME',
    'MAX_WALKING_SPEED',
    'LEAN_MULTIPLIER',
    'HEIGHT_MULTIPLIER',
    'ROTATION_INCREMENT',
    'BEEP_DURATION',
    'DEFAULT_DEBOUNCE_TIME',
    'FRAME_RATE_HZ',
    'FRAME_DURATION',
    'TELEMETRY_UPDATE_INTERVAL',
    'DEFAULT_SLEEP',
    'Singleton',
]
