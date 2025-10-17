### Inverse Kinematics Constants ###
# Constants for inverse kinematics calculations (in mm)
UPPER_LEG_LENGTH = 110.2
FOOT_LENGTH = 125.5
SHOULDER_OFFSET = 57.5
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
