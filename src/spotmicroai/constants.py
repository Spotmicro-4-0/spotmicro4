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


### Servo Calibration Constants ###
# Calibration specifications for different joint types

# Foot calibration: Maps physical angles to servo pulse widths
FOOT_CALIBRATION = {
    "joint_type": "foot",
    "points": [
        {
            "description": "Minimum position (foot perpendicular to leg)",
            "physical_angle": 17.0,
        },
        {
            "description": "Maximum position (foot inline with leg)",
            "physical_angle": 131.0,
        },
    ],
    "target_min_angle": 17.0,
    "target_max_angle": 131.0,
    "rest_angle": 30.0,
}

# Leg calibration: Maps physical angles to servo pulse widths
# Physical 0° -> -20° (digital), Physical 90° -> 110° (digital)
LEG_CALIBRATION = {
    "joint_type": "leg",
    "points": [
        {
            "description": "Minimum position (leg vertical/perpendicular to floor)",
            "physical_angle": 0.0,
        },
        {
            "description": "Maximum position (leg flat/parallel to floor)",
            "physical_angle": 90.0,
        },
    ],
    "target_min_angle": -20.0,
    "target_max_angle": 110.0,
    "rest_angle": 90.0,
}

# Shoulder calibration: Maps physical angles to servo pulse widths
# Physical 90° -> 60° (digital), Physical 60° -> 120° (digital)
SHOULDER_CALIBRATION = {
    "joint_type": "shoulder",
    "points": [
        {
            "description": "Position 1 (leg flat/parallel to floor)",
            "physical_angle": 90.0,
        },
        {
            "description": "Position 2 (leg lowered 30 degrees)",
            "physical_angle": 60.0,
        },
    ],
    "target_min_angle": 60.0,
    "target_max_angle": 120.0,
    "rest_angle": 90.0,
}

# Mapping of joint types to their calibration specifications
CALIBRATION_SPECS = {
    "foot": FOOT_CALIBRATION,
    "leg": LEG_CALIBRATION,
    "shoulder": SHOULDER_CALIBRATION,
}
